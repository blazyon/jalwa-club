"""
Wingo Game Engine
-----------------
- Numbers 0-9 drawn each round
- Color mapping: 0=violet+red, 5=violet+green, 1,3,7,9=green, 2,4,6,8=red
- Size: 0-4=Small, 5-9=Big
- Odds: Number=9x, Color=2x (Violet=4.5x), Size=2x

Admin overrides:
  forced_number  → bypass random number draw
  forced_color   → override the color derived from number (optional)
"""
from decimal import Decimal
from core.utils import secure_random_int, generate_round_seed, hash_seed


ODDS = {
    'NUMBER':       Decimal('9.0'),
    'COLOR_SINGLE': Decimal('2.0'),
    'COLOR_VIOLET': Decimal('4.5'),
    'SIZE':         Decimal('2.0'),
}

# Natural color mapping per number
COLOR_MAP = {
    0: ['RED', 'VIOLET'],
    1: ['GREEN'],
    2: ['RED'],
    3: ['GREEN'],
    4: ['RED'],
    5: ['GREEN', 'VIOLET'],
    6: ['RED'],
    7: ['GREEN'],
    8: ['RED'],
    9: ['GREEN'],
}

VALID_COLORS = {'GREEN', 'RED', 'VIOLET'}


def get_colors(number: int) -> list:
    return COLOR_MAP.get(number, [])


def get_size(number: int) -> str:
    return 'BIG' if number >= 5 else 'SMALL'


def draw_result(
    seed: str = None,
    round_id: int = 0,
    forced_number: int = None,
    forced_color: str = None,
) -> dict:
    """
    Generate round result.

    Parameters
    ----------
    forced_number : int or None
        If 0-9, use this instead of a random draw.
    forced_color  : str or None
        If provided (GREEN / RED / VIOLET), override the derived color list.
        This does NOT change the number — only the displayed color.
        Useful when admin wants e.g. number=5 but show as RED instead of GREEN+VIOLET.
    """
    if not seed:
        seed = generate_round_seed()

    # ── Determine number ─────────────────────────────────────────────
    if forced_number is not None and 0 <= int(forced_number) <= 9:
        number = int(forced_number)
    else:
        number = secure_random_int(0, 9)

    # ── Determine colors ─────────────────────────────────────────────
    if forced_color and forced_color.upper() in VALID_COLORS:
        # Admin explicitly set a color — use it as the primary color.
        # We keep the number honest but override the color label.
        colors = [forced_color.upper()]
    else:
        colors = get_colors(number)

    size = get_size(number)

    return {
        'number':    number,
        'colors':    colors,
        'size':      size,
        'seed_hash': hash_seed(seed, round_id),
    }


def calculate_payout(bet_type: str, bet_value: str, amount: Decimal,
                     result_number: int, result_colors: list = None) -> tuple:
    """
    Returns (is_winner, payout_amount). payout_amount=0 if lost.

    result_colors: if provided (from stored result_color), use these instead of
                   re-deriving from number. This respects the admin color override.
    """
    amount = Decimal(str(amount))

    # Use stored colors if available (respects forced_color), else derive
    if result_colors is None:
        result_colors = get_colors(result_number)

    result_size = get_size(result_number)

    if bet_type == 'NUMBER':
        if str(result_number) == str(bet_value):
            return True, amount * ODDS['NUMBER']
        return False, Decimal('0')

    elif bet_type == 'COLOR':
        bet_color = bet_value.upper()
        if bet_color == 'VIOLET' and 'VIOLET' in result_colors:
            return True, amount * ODDS['COLOR_VIOLET']
        elif bet_color in result_colors and bet_color != 'VIOLET':
            return True, amount * ODDS['COLOR_SINGLE']
        return False, Decimal('0')

    elif bet_type == 'SIZE':
        if bet_value.upper() == result_size:
            return True, amount * ODDS['SIZE']
        return False, Decimal('0')

    return False, Decimal('0')


def get_potential_payout(bet_type: str, bet_value: str, amount: Decimal) -> Decimal:
    amount = Decimal(str(amount))
    if bet_type == 'NUMBER':
        return amount * ODDS['NUMBER']
    elif bet_type == 'COLOR':
        if bet_value.upper() == 'VIOLET':
            return amount * ODDS['COLOR_VIOLET']
        return amount * ODDS['COLOR_SINGLE']
    elif bet_type == 'SIZE':
        return amount * ODDS['SIZE']
    return Decimal('0')
