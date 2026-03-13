import logging
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from .models import WingoRound, WingoBet
from .engine import draw_result, calculate_payout, get_potential_payout
from core.services import WalletService, InsufficientBalanceError

logger = logging.getLogger('apps')

BET_LOCK_SECONDS = 5

MODE_DURATIONS = {
    '1MIN': 60,
    '3MIN': 180,
    '5MIN': 300,
}


def get_or_create_current_round(mode: str = '1MIN') -> WingoRound:
    """Get the current open round for a mode, or create a new one."""
    mode = mode.upper()
    now = timezone.now()

    round_obj = WingoRound.objects.filter(
        mode=mode, status=WingoRound.Status.OPEN
    ).first()
    if round_obj:
        return round_obj

    last = WingoRound.objects.filter(mode=mode).order_by('-round_number').first()
    next_num = (last.round_number + 1) if last else 1
    duration = MODE_DURATIONS.get(mode, 60)
    starts_at = now
    ends_at = starts_at + timezone.timedelta(seconds=duration)

    return WingoRound.objects.create(
        mode=mode,
        round_number=next_num,
        status=WingoRound.Status.OPEN,
        starts_at=starts_at,
        ends_at=ends_at,
    )


@transaction.atomic
def place_bet(user, round_id, bet_type: str, bet_value: str, amount: Decimal) -> WingoBet:
    """Place a bet — atomic debit + validation."""
    from apps.wallet.models import Wallet
    amount = Decimal(str(amount))
    if amount < Decimal('10'):
        raise ValueError("Minimum bet is 10 demo coins.")
    if amount > Decimal('10000'):
        raise ValueError("Maximum bet is 10,000 demo coins per bet.")

    bet_type  = bet_type.upper()
    bet_value = str(bet_value).upper()

    valid_colors = {'RED', 'GREEN', 'VIOLET'}
    valid_sizes  = {'BIG', 'SMALL'}
    if bet_type == 'NUMBER':
        if not bet_value.isdigit() or not (0 <= int(bet_value) <= 9):
            raise ValueError("Invalid number bet. Choose 0-9.")
    elif bet_type == 'COLOR':
        if bet_value not in valid_colors:
            raise ValueError(f"Invalid color. Choose from {valid_colors}")
    elif bet_type == 'SIZE':
        if bet_value not in valid_sizes:
            raise ValueError(f"Invalid size. Choose BIG or SMALL.")
    else:
        raise ValueError("Invalid bet type.")

    try:
        round_obj = WingoRound.objects.select_for_update().get(pk=round_id)
    except WingoRound.DoesNotExist:
        raise ValueError("Round not found.")

    if not round_obj.is_accepting_bets:
        raise ValueError("This round is no longer accepting bets.")

    if round_obj.seconds_remaining <= BET_LOCK_SECONDS:
        raise ValueError("Bet window closed. Wait for next round.")

    wallet = Wallet.objects.get(user=user)
    potential = get_potential_payout(bet_type, bet_value, amount)

    WalletService.debit(
        wallet, amount,
        reference=f'BET_WINGO_{round_obj.mode}_{round_obj.round_number}_{user.id}_{bet_type}_{bet_value}',
        description=f'Wingo[{round_obj.mode}] bet #{round_obj.round_number} {bet_type}={bet_value}',
    )

    bet = WingoBet.objects.create(
        user=user,
        round=round_obj,
        bet_type=bet_type,
        bet_value=bet_value,
        amount=amount,
        potential_payout=potential,
    )
    logger.info(f"Wingo bet: user={user.username} mode={round_obj.mode} "
                f"round=#{round_obj.round_number} {bet_type}={bet_value} amount={amount}")
    return bet


@transaction.atomic
def settle_round(round_id) -> WingoRound:
    """
    Settle a round when its timer expires (called by Celery task only).

    Flow:
      1. Lock the round row (select_for_update)
      2. If admin pre-set forced_result / forced_color → use them
         Otherwise → draw random
      3. Settle all bets, credit winners
      4. Open next round for this mode

    ⚠️  This function must NEVER be called from admin.save_model().
        Admin only stores the override fields; Celery applies them at round end.
    """
    from apps.wallet.models import Wallet
    round_obj = WingoRound.objects.select_for_update().get(pk=round_id)

    if round_obj.status == WingoRound.Status.COMPLETED:
        return round_obj

    round_obj.status = WingoRound.Status.LOCKED
    round_obj.save(update_fields=['status'])

    # ── Resolve forced overrides ─────────────────────────────────────
    forced_num   = None
    forced_color = None

    if round_obj.forced_result is not None:
        fn = int(round_obj.forced_result)
        if 0 <= fn <= 9:
            forced_num = fn
            logger.info(f"Wingo[{round_obj.mode}] #{round_obj.round_number}: "
                        f"using FORCED number={forced_num}")

    if round_obj.forced_color:
        forced_color = round_obj.forced_color.strip().upper()
        logger.info(f"Wingo[{round_obj.mode}] #{round_obj.round_number}: "
                    f"using FORCED color={forced_color}")

    result = draw_result(
        round_id=round_obj.round_number,
        forced_number=forced_num,
        forced_color=forced_color,
    )

    number = result['number']
    colors = result['colors']
    size   = result['size']

    round_obj.result_number = number
    round_obj.result_color  = ','.join(colors)
    round_obj.result_size   = size
    round_obj.seed_hash     = result['seed_hash']
    round_obj.status        = WingoRound.Status.COMPLETED
    round_obj.save()

    # ── Settle all bets ──────────────────────────────────────────────
    bets = WingoBet.objects.select_related('user').filter(round=round_obj)
    for bet in bets:
        # Pass stored colors so forced_color is respected in payout logic
        is_winner, payout = calculate_payout(
            bet.bet_type, bet.bet_value, bet.amount,
            number, result_colors=colors
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
                    reference=f'WIN_WINGO_{round_obj.mode}_{round_obj.round_number}_{bet.id}',
                    description=f'Wingo[{round_obj.mode}] win #{round_obj.round_number} '
                                f'{bet.bet_type}={bet.bet_value}',
                )
                logger.info(f"Credited {payout} to {bet.user.username} for Wingo win")
            except Exception as e:
                logger.error(f"Failed to credit win for bet {bet.id}: {e}")

    logger.info(f"Wingo[{round_obj.mode}] #{round_obj.round_number} settled. "
                f"Result={number} Colors={colors} Size={size}")

    # ── Open next round for this mode ────────────────────────────────
    get_or_create_current_round(mode=round_obj.mode)
    return round_obj
