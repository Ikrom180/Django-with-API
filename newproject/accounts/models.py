# accounts/models.py
from django.db import models
from django.contrib.auth.models import User


class Account(models.Model):
    ACCOUNT_TYPES = [
        ('PHYSICAL', 'Physical Person'),
        ('LEGAL', 'Legal Entity'),
    ]

    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('PENDING', 'Pending Approval'),
        ('CLOSED', 'Closed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='accounts')
    account_number = models.CharField(max_length=20, unique=True)
    account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    branch = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.account_number} - {self.user.username}"


class AccountHistory(models.Model):
    TRANSACTION_TYPES = [
        ('INCOME', 'Income'),
        ('OUTCOME', 'Outcome'),
        ('TRANSFER', 'Transfer'),
    ]

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='history')
    transaction_date = models.DateTimeField(auto_now_add=True)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.TextField()

    def __str__(self):
        return f"{self.account.account_number} - {self.transaction_type} - {self.amount}"


class Branch(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    address = models.TextField()
    phone = models.CharField(max_length=20)

    def __str__(self):
        return self.name