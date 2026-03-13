import logging
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from .models import K3Round, K3Bet
from .engine import draw_result, calculate_payout, get_potential_payout
from core.services import WalletService, InsufficientBalanceError

logger = logging.getLogger('apps')

ROUND_DURATION_SECONDS = 180   # 3-minute rounds
BET_LOCK_SECONDS = 5

VALID_BET_TYPES = {
    'TOTAL', 'SIZE', 'PARITY', 'SPECIFIC_TRIPLE',
    'ANY_TRIPLE', 'SPECIFIC_DOUBLE', 'TWO_DIFFERENT', 'THREE_DIFFERENT'
}


def get_or_create_current_round() -> K3Round:
    now = timezone.now()
    round_obj = K3Round.objects.filter(status=K3Round.Status.OPEN).first()
    if round_obj:
        return round_obj
    last = K3Round.objects.order_by('-round_number').first()
    next_num = (last.round_number + 1) if last else 1
    starts_at = now
    ends_at   = starts_at + timezone.timedelta(seconds=ROUND_DURATION_SECONDS)
    return K3Round.objects.create(
        round_number=next_num,
        status=K3Round.Status.OPEN,
        starts_at=starts_at,
        ends_at=ends_at,
    )


@transaction.atomic
def place_bet(user, round_id, bet_type: str, bet_value: str, amount: Decimal) -> K3Bet:
    from apps.wallet.models import Wallet
    amount    = Decimal(str(amount))
    if amount < Decimal('10'):
        raise ValueError("Minimum bet is 10 demo coins.")
    if amount > Decimal('10000'):
        raise ValueError("Maximum bet is 10,000 demo coins per bet.")

    bet_type  = bet_type.upper()
    bet_value = str(bet_value).upper()

    if bet_type not in VALID_BET_TYPES:
        raise ValueError(f"Invalid bet type. Choose from {VALID_BET_TYPES}")

    try:
        round_obj = K3Round.objects.select_for_update().get(pk=round_id)
    except K3Round.DoesNotExist:
        raise ValueError("Round not found.")

    if not round_obj.is_accepting_bets:
        raise ValueError("This round is no longer accepting bets.")

    if round_obj.seconds_remaining <= BET_LOCK_SECONDS:
        raise ValueError("Bet window closed.")

    wallet    = Wallet.objects.get(user=user)
    potential = get_potential_payout(bet_type, bet_value, amount)

    WalletService.debit(
        wallet, amount,
        reference=f'BET_K3_{round_obj.round_number}_{user.id}_{bet_type}_{bet_value}',
        description=f'K3 bet #{round_obj.round_number} {bet_type}={bet_value}',
    )

    bet = K3Bet.objects.create(
        user=user, round=round_obj,
        bet_type=bet_type, bet_value=bet_value,
        amount=amount, potential_payout=potential,
    )
    return bet


def _parse_forced_dice(forced_dice_str: str):
    """
    Parse admin forced_dice string e.g. "3,5,2" → [3, 5, 2].
    Returns None if invalid.
    """
    try:
        parts = [int(x.strip()) for x in forced_dice_str.split(',')]
        if len(parts) == 3 and all(1 <= d <= 6 for d in parts):
            return parts
    except (ValueError, AttributeError):
        pass
    return None


@transaction.atomic
def settle_round(round_id) -> K3Round:
    """
    Settle a K3 round when its timer expires (called by Celery task only).

    If admin pre-set forced_dice, those values are used.
    Settlement never happens from admin.save_model() — only from here.
    """
    from apps.wallet.models import Wallet
    round_obj = K3Round.objects.select_for_update().get(pk=round_id)

    if round_obj.status == K3Round.Status.COMPLETED:
        return round_obj

    round_obj.status = K3Round.Status.LOCKED
    round_obj.save(update_fields=['status'])

    # ── Resolve forced dice ──────────────────────────────────────────
    forced_dice = None
    if round_obj.forced_dice:
        forced_dice = _parse_forced_dice(round_obj.forced_dice)
        if forced_dice:
            logger.info(f"K3 #{round_obj.round_number}: using FORCED dice={forced_dice}")
        else:
            logger.warning(f"K3 #{round_obj.round_number}: invalid forced_dice "
                           f"'{round_obj.forced_dice}', using random.")

    result = draw_result(round_id=round_obj.round_number, forced_dice=forced_dice)
    dice  = result['dice']
    total = result['total']
    tags  = result['tags']

    round_obj.dice1, round_obj.dice2, round_obj.dice3 = dice
    round_obj.total       = total
    round_obj.result_tags = tags
    round_obj.seed_hash   = result['seed_hash']
    round_obj.status      = K3Round.Status.COMPLETED
    round_obj.save()

    # ── Settle all bets ──────────────────────────────────────────────
    bets = K3Bet.objects.select_related('user').filter(round=round_obj)
    for bet in bets:
        is_winner, payout = calculate_payout(
            bet.bet_type, bet.bet_value, bet.amount, dice, total, tags
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
                    reference=f'WIN_K3_{round_obj.round_number}_{bet.id}',
                    description=f'K3 win #{round_obj.round_number}',
                )
            except Exception as e:
                logger.error(f"K3 credit error: {e}")

    logger.info(f"K3 #{round_obj.round_number} settled. Dice: {dice} Total: {total}")

    # ── Open next round ──────────────────────────────────────────────
    get_or_create_current_round()
    return round_obj