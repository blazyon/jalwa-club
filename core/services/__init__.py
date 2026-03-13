from decimal import Decimal
from django.db import transaction


class InsufficientBalanceError(Exception):
    pass


class WalletService:
    """Centralized atomic wallet operations with correct transaction categories."""

    @staticmethod
    @transaction.atomic
    def debit(wallet, amount: Decimal, reference: str, description: str = '',
              category: str = 'BET_PLACED'):
        from apps.wallet.models import Transaction
        amount = Decimal(str(amount))
        if amount <= 0:
            raise ValueError("Amount must be positive")
        # Lock the wallet row to prevent race conditions
        wallet = wallet.__class__.objects.select_for_update().get(pk=wallet.pk)
        if wallet.balance < amount:
            raise InsufficientBalanceError(
                f"Insufficient balance. Required: {amount}, Available: {wallet.balance}"
            )
        wallet.balance -= amount
        wallet.save(update_fields=['balance', 'updated_at'])
        tx = Transaction.objects.create(
            wallet=wallet,
            tx_type=Transaction.Type.DEBIT,
            amount=amount,
            balance_after=wallet.balance,
            reference=reference,
            description=description,
            category=category,
        )
        return tx

    @staticmethod
    @transaction.atomic
    def credit(wallet, amount: Decimal, reference: str, description: str = '',
               category: str = None):
        from apps.wallet.models import Transaction
        amount = Decimal(str(amount))
        if amount <= 0:
            raise ValueError("Amount must be positive")
        wallet = wallet.__class__.objects.select_for_update().get(pk=wallet.pk)
        wallet.balance += amount
        wallet.save(update_fields=['balance', 'updated_at'])

        # Auto-detect category from reference prefix if not supplied
        if category is None:
            ref_upper = reference.upper()
            if ref_upper.startswith('SIGNUP_BONUS'):
                category = Transaction.Category.SIGNUP_BONUS
            elif ref_upper.startswith('WIN_'):
                category = Transaction.Category.BET_WON
            elif ref_upper.startswith('ADMIN_'):
                category = Transaction.Category.ADMIN_CREDIT
            elif ref_upper.startswith('REFUND_') or ref_upper.startswith('WD_REFUND'):
                category = Transaction.Category.BET_REFUND
            elif ref_upper.startswith('DEPOSIT_'):
                category = Transaction.Category.DEPOSIT
            else:
                category = Transaction.Category.ADMIN_CREDIT

        tx = Transaction.objects.create(
            wallet=wallet,
            tx_type=Transaction.Type.CREDIT,
            amount=amount,
            balance_after=wallet.balance,
            reference=reference,
            description=description,
            category=category,
        )
        return tx
