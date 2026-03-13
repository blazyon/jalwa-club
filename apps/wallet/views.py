import logging
from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from .models import Wallet, Transaction, DepositRequest, WithdrawRequest
from core.services import WalletService

logger = logging.getLogger('apps')

# ─── Configurable via settings.py ───────────────────────────────────────────
# Add these to your .env / settings:
#   DEPOSIT_UPI_ID = "yourname@upi"
#   DEPOSIT_UPI_NAME = "Your Name"
#   DEPOSIT_QR_IMAGE = "img/deposit_qr.png"   (relative to /static/)
#   DEPOSIT_MIN = 100
#   DEPOSIT_MAX = 50000
#   WITHDRAW_MIN = 200
#   WITHDRAW_MAX = 50000
# ─────────────────────────────────────────────────────────────────────────────


def _deposit_config():
    return {
        'upi_id': getattr(settings, 'DEPOSIT_UPI_ID', 'demo@upi'),
        'upi_name': getattr(settings, 'DEPOSIT_UPI_NAME', 'LuckyDraw Demo'),
        'qr_image': getattr(settings, 'DEPOSIT_QR_IMAGE', 'img/deposit_qr.png'),
        'min_amount': getattr(settings, 'DEPOSIT_MIN', 100),
        'max_amount': getattr(settings, 'DEPOSIT_MAX', 50000),
    }


def _withdraw_config():
    return {
        'min_amount': getattr(settings, 'WITHDRAW_MIN', 200),
        'max_amount': getattr(settings, 'WITHDRAW_MAX', 50000),
    }


@login_required
def wallet_view(request):
    wallet, created = Wallet.objects.get_or_create(
        user=request.user, defaults={'balance': 0}
    )
    if created:
        messages.info(request, 'Wallet created for your account.')

    transactions = Transaction.objects.filter(wallet=wallet).order_by('-created_at')[:50]

    return render(request, 'wallet/wallet.html', {
        'wallet': wallet,
        'transactions': transactions,
    })


@login_required
def deposit_view(request):
    wallet, _ = Wallet.objects.get_or_create(user=request.user, defaults={'balance': 0})
    cfg = _deposit_config()
    my_requests = DepositRequest.objects.filter(wallet=wallet).order_by('-created_at')[:10]

    if request.method == 'POST':
        # Validate amount
        try:
            amount = Decimal(request.POST.get('amount', '0').strip())
        except InvalidOperation:
            messages.error(request, 'Invalid amount entered.')
            return redirect('deposit')

        utr = request.POST.get('utr_number', '').strip()
        upi_used = request.POST.get('upi_id_used', '').strip() or cfg['upi_id']

        # Validations
        if amount < cfg['min_amount']:
            messages.error(request, f"Minimum deposit is ₹{cfg['min_amount']}.")
            return redirect('deposit')
        if amount > cfg['max_amount']:
            messages.error(request, f"Maximum deposit is ₹{cfg['max_amount']}.")
            return redirect('deposit')
        if not utr or len(utr) < 6:
            messages.error(request, 'Please enter a valid UTR / transaction reference number (min 6 chars).')
            return redirect('deposit')

        # Prevent duplicate UTR submissions
        if DepositRequest.objects.filter(utr_number__iexact=utr).exists():
            messages.error(request, 'This UTR number has already been submitted. Contact support if this is an error.')
            return redirect('deposit')

        DepositRequest.objects.create(
            wallet=wallet,
            amount=amount,
            utr_number=utr,
            upi_id_used=upi_used,
        )
        logger.info(f"Deposit request created: user={request.user.username} amount={amount} utr={utr}")
        messages.success(
            request,
            f'✅ Deposit request of ₹{amount:.0f} submitted! '
            f'Your balance will be credited within 30 minutes after verification.'
        )
        return redirect('deposit')

    return render(request, 'wallet/deposit.html', {
        'wallet': wallet,
        'my_requests': my_requests,
        **cfg,
    })


@login_required
def withdraw_view(request):
    wallet, _ = Wallet.objects.get_or_create(user=request.user, defaults={'balance': 0})
    cfg = _withdraw_config()
    my_requests = WithdrawRequest.objects.filter(wallet=wallet).order_by('-created_at')[:10]

    # Check for any pending withdrawal already
    has_pending = WithdrawRequest.objects.filter(
        wallet=wallet, status=WithdrawRequest.Status.PENDING
    ).exists()

    if request.method == 'POST':
        if has_pending:
            messages.error(request, 'You already have a pending withdrawal request. Please wait for it to be processed.')
            return redirect('withdraw')

        # Validate amount
        try:
            amount = Decimal(request.POST.get('amount', '0').strip())
        except InvalidOperation:
            messages.error(request, 'Invalid amount entered.')
            return redirect('withdraw')

        upi_id = request.POST.get('upi_id', '').strip()

        # Validations
        if amount < cfg['min_amount']:
            messages.error(request, f"Minimum withdrawal is ₹{cfg['min_amount']}.")
            return redirect('withdraw')
        if amount > cfg['max_amount']:
            messages.error(request, f"Maximum withdrawal is ₹{cfg['max_amount']}.")
            return redirect('withdraw')
        if not upi_id or '@' not in upi_id:
            messages.error(request, 'Please enter a valid UPI ID (e.g., name@paytm).')
            return redirect('withdraw')
        if wallet.balance < amount:
            messages.error(request, f'Insufficient balance. Your balance is ₹{wallet.balance:.0f}.')
            return redirect('withdraw')

        # Debit wallet immediately and hold in pending
        try:
            WalletService.debit(
                wallet, amount,
                reference=f'WD_HOLD_{wallet.user.id}_{WithdrawRequest.objects.count()}',
                description=f'Withdrawal hold — pending approval to {upi_id}',
                category='WITHDRAWAL',
            )
        except Exception as e:
            messages.error(request, f'Could not process withdrawal: {e}')
            return redirect('withdraw')

        WithdrawRequest.objects.create(
            wallet=wallet,
            amount=amount,
            upi_id=upi_id,
        )
        logger.info(f"Withdraw request created: user={request.user.username} amount={amount} upi={upi_id}")
        messages.success(
            request,
            f'✅ Withdrawal request of ₹{amount:.0f} submitted! '
            f'Amount will be sent to {upi_id} within 24 hours.'
        )
        return redirect('withdraw')

    return render(request, 'wallet/withdraw.html', {
        'wallet': wallet,
        'my_requests': my_requests,
        'has_pending': has_pending,
        **cfg,
    })
