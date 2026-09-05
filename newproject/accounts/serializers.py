# accounts/serializers.py
from rest_framework import serializers
from .models import Account, AccountHistory, Branch


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'account_number', 'account_type', 'status', 'balance', 'branch', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'status', 'balance']


class AccountHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountHistory
        fields = ['id', 'transaction_date', 'transaction_type', 'amount', 'description']


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ['id', 'name', 'code', 'address', 'phone']


class AccountDetailSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    account_number = serializers.CharField()
    account_type = serializers.CharField()
    status = serializers.CharField()
    balance = serializers.DecimalField(max_digits=15, decimal_places=2)
    branch = serializers.CharField(allow_null=True)
    user_name = serializers.CharField(source='user.username')
    user_email = serializers.CharField(source='user.email')

    class Meta:
        fields = ['id', 'account_number', 'account_type', 'status', 'balance', 'branch', 'user_name', 'user_email']


class AccountTurnoverSerializer(serializers.Serializer):
    account_number = serializers.CharField()
    total_income = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_outcome = serializers.DecimalField(max_digits=15, decimal_places=2)
    balance = serializers.DecimalField(max_digits=15, decimal_places=2)