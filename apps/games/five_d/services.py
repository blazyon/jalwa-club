import logging
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from .models import FiveDRound, FiveDbet
from .engine import draw_result, calculate_payout, get_potential_payout
from core.services import WalletService, InsufficientBalanceError

logger = logging.getLogger('apps')

ROUND_DURATION_SECONDS = 300   # 5-minute rounds
BET_LOCK_SECONDS = 5

VALID_BET_TYPES = {'POSITION', 'TOTAL_SIZE', 'TOTAL_PARITY', 'EXACT_TOTAL'}


def get_or_create_current_round() -> FiveDRound:
    now = timezone.now()
    round_obj = FiveDRound.objects.filter(status=FiveDRound.Status.OPEN).first()
    if round_obj:
        return round_obj
    last     = FiveDRound.objects.order_by('-round_number').first()
    next_num = (last.round_number + 1) if last else 1
    starts_at = now
    ends_at   = starts_at + timezone.timedelta(seconds=ROUND_DURATION_SECONDS)
    return FiveDRound.objects.create(
        round_number=next_num,
        status=FiveDRound.Status.OPEN,
        starts_at=starts_at,
        ends_at=ends_at,
    )


@transaction.atomic
def place_bet(user, round_id, bet_type: str, bet_value: str, amount: Decimal) -> FiveDbet:
    from apps.wallet.models import Wallet
    amount    = Decimal(str(amount))
    if amount < Decimal('10'):
        raise ValueError("Minimum bet is 10 demo coins.")
    if amount > Decimal('10000'):
        raise ValueError("Maximum bet is 10,000 demo coins.")

    bet_type  = bet_type.upper()
    bet_value = str(bet_value).upper()

    if bet_type not in VALID_BET_TYPES:
        raise ValueError(f"Invalid bet type.")

    try:
        round_obj = FiveDRound.objects.select_for_update().get(pk=round_id)
    except FiveDRound.DoesNotExist:
        raise ValueError("Round not found.")

    if not round_obj.is_accepting_bets:
        raise ValueError("Round not accepting bets.")

    if round_obj.seconds_remaining <= BET_LOCK_SECONDS:
        raise ValueError("Bet window closed.")

    wallet    = Wallet.objects.get(user=user)
    potential = get_potential_payout(bet_type, bet_value, amount)

    WalletService.debit(
        wallet, amount,
        reference=f'BET_5D_{round_obj.round_number}_{user.id}_{bet_type}_{bet_value}',
        description=f'5D bet #{round_obj.round_number} {bet_type}={bet_value}',
    )

    return FiveDbet.objects.create(
        user=user, round=round_obj,
        bet_type=bet_type, bet_value=bet_value,
        amount=amount, potential_payout=potential,
    )


def _parse_forced_digits(forced_digits_str: str):
    """
    Parse admin forced_digits string e.g. "1,2,3,4,5" → [1, 2, 3, 4, 5].
    Returns None if invalid.
    """
    try:
        parts = [int(x.strip()) for x in forced_digits_str.split(',')]
        if len(parts) == 5 and all(0 <= d <= 9 for d in parts):
            return parts
    except (ValueError, AttributeError):
        pass
    return None


@transaction.atomic
def settle_round(round_id) -> FiveDRound:
    """
    Settle a 5D round when its timer expires (called by Celery task only).

    If admin pre-set forced_digits, those values are used.
    Settlement never happens from admin.save_model() — only from here.
    """
    from apps.wallet.models import Wallet
    round_obj = FiveDRound.objects.select_for_update().get(pk=round_id)

    if round_obj.status == FiveDRound.Status.COMPLETED:
        return round_obj

    round_obj.status = FiveDRound.Status.LOCKED
    round_obj.save(update_fields=['status'])

    # ── Resolve forced digits ────────────────────────────────────────
    forced_digits = None
    if round_obj.forced_digits:
        forced_digits = _parse_forced_digits(round_obj.forced_digits)
        if forced_digits:
            logger.info(f"5D #{round_obj.round_number}: using FORCED digits={forced_digits}")
        else:
            logger.warning(f"5D #{round_obj.round_number}: invalid forced_digits "
                           f"'{round_obj.forced_digits}', using random.")

    result = draw_result(round_id=round_obj.round_number, forced_digits=forced_digits)
    digits = result['digits']
    total  = result['total']
    size   = result['size']
    parity = result['parity']

    round_obj.digit_a, round_obj.digit_b, round_obj.digit_c, \
        round_obj.digit_d, round_obj.digit_e = digits
    round_obj.total     = total
    round_obj.seed_hash = result['seed_hash']
    round_obj.status    = FiveDRound.Status.COMPLETED
    round_obj.save()

    # ── Settle all bets ──────────────────────────────────────────────
    bets = FiveDbet.objects.select_related('user').filter(round=round_obj)
    for bet in bets:
        is_winner, payout = calculate_payout(
            bet.bet_type, bet.bet_value, bet.amount, digits, total, size, parity
        )
        bet.is_winner     = is_winner
        bet.payout_amount = payout
        bet.settled_at    = timezone.now()
        bet.save(update_fields=['is_winner', 'payout_amount', 'settled_at'])
        if is_winner and payout > 0:
            try:
                wallet = Wallet.objects.get(user=bet.user)
                WalletService.credit(
                    wallet, payout,
                    reference=f'WIN_5D_{round_obj.round_number}_{bet.id}',
                    description=f'5D win #{round_obj.round_number}',
                )
            except Exception as e:
                logger.error(f"5D credit error: {e}")

    logger.info(f"5D #{round_obj.round_number} settled. Digits: {digits}")

    # ── Open next round ──────────────────────────────────────────────
    get_or_create_current_round()
    return round_obj