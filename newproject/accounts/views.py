# accounts/views.py
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Q
from .models import Account, AccountHistory, Branch
from .serializers import (
    AccountSerializer,
    AccountHistorySerializer,
    AccountDetailSerializer,
    AccountTurnoverSerializer,
    BranchSerializer
)


class AccountViewSet(viewsets.ViewSet):
    """
    Account management endpoints
    """
    permission_classes = [IsAuthenticated]

    # POST /1.0.0/account - Create account (Physical + Legal)
    def create(self, request):
        serializer = AccountSerializer(data=request.data)
        if serializer.is_valid():
            # Generate account number if not provided
            account_number = request.data.get('account_number')
            if not account_number:
                # Generate unique account number
                import random
                account_number = f"{random.randint(1000000000, 9999999999)}"

            account = Account.objects.create(
                user=request.user,
                account_number=account_number,
                account_type=request.data.get('account_type', 'PHYSICAL'),
                branch=request.data.get('branch', ''),
                status='PENDING'  # New accounts start as pending
            )

            # Add initial transaction
            AccountHistory.objects.create(
                account=account,
                transaction_type='INCOME',
                amount=0,
                description='Account created'
            )

            return Response(
                AccountSerializer(account).data,
                status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    # DELETE /1.0.0/account/{id} - Close account
    def destroy(self, request, pk=None):
        account = get_object_or_404(Account, pk=pk, user=request.user)

        # Check if account can be closed
        if account.balance > 0:
            return Response(
                {"error": "Cannot close account with positive balance"},
                status=status.HTTP_400_BAD_REQUEST
            )

        account.status = 'CLOSED'
        account.save()

        # Log account closure
        AccountHistory.objects.create(
            account=account,
            transaction_type='OUTCOME',
            amount=0,
            description='Account closed'
        )

        return Response(
            {"message": f"Account {account.account_number} closed successfully"},
            status=status.HTTP_204_NO_CONTENT
        )

    # PATCH /1.0.0/account/{id} - Approve account
    def partial_update(self, request, pk=None):
        account = get_object_or_404(Account, pk=pk)

        # Only admins or the account owner can approve
        if account.user != request.user and not request.user.is_staff:
            return Response(
                {"error": "You don't have permission to approve this account"},
                status=status.HTTP_403_FORBIDDEN
            )

        account.status = 'ACTIVE'
        account.save()

        AccountHistory.objects.create(
            account=account,
            transaction_type='INCOME',
            amount=0,
            description='Account approved'
        )

        return Response(
            {"message": f"Account {account.account_number} approved successfully"},
            status=status.HTTP_200_OK
        )

    # GET /1.0.0/get-account-details - Account details
    @action(detail=False, methods=['get'], url_path='get-account-details')
    def get_account_details(self, request):
        account_number = request.query_params.get('account_number')

        if not account_number:
            return Response(
                {"error": "account_number parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        account = get_object_or_404(
            Account,
            account_number=account_number,
            user=request.user
        )

        # Using the detail serializer to include user info
        data = {
            'id': account.id,
            'account_number': account.account_number,
            'account_type': account.account_type,
            'status': account.status,
            'balance': account.balance,
            'branch': account.branch,
            'user_name': account.user.username,
            'user_email': account.user.email
        }

        return Response(data)

    # GET /1.0.0/get-account-history/{id} - Account history
    @action(detail=False, methods=['get'], url_path='get-account-history/(?P<id>[^/.]+)')
    def get_account_history(self, request, id=None):
        account = get_object_or_404(Account, pk=id, user=request.user)
        history = account.history.all().order_by('-transaction_date')
        serializer = AccountHistorySerializer(history, many=True)
        return Response(serializer.data)

    # GET /1.0.0/get-account-turnover - Account turnover
    @action(detail=False, methods=['get'], url_path='get-account-turnover')
    def get_account_turnover(self, request):
        account_number = request.query_params.get('account_number')

        if not account_number:
            return Response(
                {"error": "account_number parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        account = get_object_or_404(
            Account,
            account_number=account_number,
            user=request.user
        )

        income = account.history.filter(
            transaction_type='INCOME'
        ).aggregate(total=Sum('amount'))['total'] or 0

        outcome = account.history.filter(
            transaction_type='OUTCOME'
        ).aggregate(total=Sum('amount'))['total'] or 0

        data = {
            'account_number': account.account_number,
            'total_income': income,
            'total_outcome': outcome,
            'balance': account.balance
        }

        return Response(data)

    # GET /1.0.0/get-accounts-and-branches - Get branches and accounts
    @action(detail=False, methods=['get'], url_path='get-accounts-and-branches')
    def get_accounts_and_branches(self, request):
        # Get all branches
        branches = Branch.objects.all()

        response_data = {
            'branches': []
        }

        for branch in branches:
            accounts = Account.objects.filter(
                branch=branch.name,
                user=request.user
            ).values('id', 'account_number', 'status', 'account_type', 'balance')

            response_data['branches'].append({
                'id': branch.id,
                'name': branch.name,
                'code': branch.code,
                'address': branch.address,
                'accounts': list(accounts)
            })

        # If no branches in DB, return some mock data
        if not response_data['branches']:
            response_data['branches'] = [
                {
                    'id': 1,
                    'name': 'Main Branch',
                    'code': '001',
                    'address': 'Tashkent, Uzbekistan',
                    'accounts': Account.objects.filter(
                        user=request.user
                    ).values('id', 'account_number', 'status', 'account_type', 'balance')
                }
            ]

        return Response(response_data)

    # GET /1.0.0/get-active-accounts/{clientId} - Active accounts
    @action(detail=False, methods=['get'], url_path='get-active-accounts/(?P<clientId>[^/.]+)')
    def get_active_accounts(self, request, clientId=None):
        # Check authorization
        try:
            client_id = int(clientId)
        except ValueError:
            return Response(
                {"error": "Invalid client ID"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if client_id != request.user.id and not request.user.is_staff:
            return Response(
                {"error": "Unauthorized access"},
                status=status.HTTP_403_FORBIDDEN
            )

        accounts = Account.objects.filter(
            user_id=client_id,
            status='ACTIVE'
        )

        serializer = AccountSerializer(accounts, many=True)
        return Response(serializer.data)

    # Additional endpoint: Get all accounts for a user
    @action(detail=False, methods=['get'], url_path='my-accounts')
    def my_accounts(self, request):
        accounts = Account.objects.filter(user=request.user)
        serializer = AccountSerializer(accounts, many=True)
        return Response(serializer.data)