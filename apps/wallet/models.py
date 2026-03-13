import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings


class Wallet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name='wallet')
    balance = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'wallets'

    def __str__(self):
        return f"Wallet({self.user.username}) = {self.balance}"


class Transaction(models.Model):
    class Type(models.TextChoices):
        CREDIT = 'CREDIT', 'Credit'
        DEBIT = 'DEBIT', 'Debit'

    class Category(models.TextChoices):
        SIGNUP_BONUS = 'SIGNUP_BONUS', 'Signup Bonus'
        ADMIN_CREDIT = 'ADMIN_CREDIT', 'Admin Credit'
        ADMIN_DEBIT = 'ADMIN_DEBIT', 'Admin Debit'
        BET_PLACED = 'BET_PLACED', 'Bet Placed'
        BET_WON = 'BET_WON', 'Bet Won'
        BET_REFUND = 'BET_REFUND', 'Bet Refund'
        DEPOSIT = 'DEPOSIT', 'Deposit'
        WITHDRAWAL = 'WITHDRAWAL', 'Withdrawal'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    tx_type = models.CharField(max_length=10, choices=Type.choices)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    balance_after = models.DecimalField(max_digits=14, decimal_places=2)
    reference = models.CharField(max_length=128, unique=True)
    description = models.CharField(max_length=255, blank=True)
    category = models.CharField(max_length=32, choices=Category.choices,
                                default=Category.ADMIN_CREDIT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['wallet', '-created_at']),
            models.Index(fields=['reference']),
        ]

    def __str__(self):
        return f"{self.tx_type} {self.amount} | {self.reference}"


class DepositRequest(models.Model):
    """User submits a deposit request with UTR after paying via UPI."""

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Review'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='deposit_requests')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    utr_number = models.CharField(
        max_length=64,
        help_text='UTR / Transaction reference number provided by user'
    )
    upi_id_used = models.CharField(
        max_length=128, blank=True,
        help_text='UPI ID the user sent money to'
    )
    status = models.CharField(
        max_length=16, choices=Status.choices,
        default=Status.PENDING, db_index=True
    )
    admin_note = models.CharField(max_length=255, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='reviewed_deposits'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'deposit_requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['wallet', '-created_at']),
        ]

    def __str__(self):
        return f"Deposit #{self.id} | {self.wallet.user.username} | ₹{self.amount} | {self.status}"


class WithdrawRequest(models.Model):
    """User requests withdrawal to their UPI ID. Admin sends money and approves."""

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Review'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='withdraw_requests')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    upi_id = models.CharField(max_length=128, help_text='UPI ID to send money to')
    status = models.CharField(
        max_length=16, choices=Status.choices,
        default=Status.PENDING, db_index=True
    )
    admin_note = models.CharField(max_length=255, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='reviewed_withdrawals'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'withdraw_requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['wallet', '-created_at']),
        ]

    def __str__(self):
        return f"Withdraw #{self.id} | {self.wallet.user.username} | ₹{self.amount} | {self.status}"
