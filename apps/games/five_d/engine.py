"""
5D Game Engine
--------------
Five independent digits A-E each 0-9.
Total range: 0-45.
Big = 23-45, Small = 0-22.
Position bet: guess exact digit at position A/B/C/D/E.
"""
from decimal import Decimal
from core.utils import secure_random_digits, generate_round_seed, hash_seed

POSITIONS = ['A', 'B', 'C', 'D', 'E']

ODDS = {
    'POSITION': Decimal('9.0'),   # Exact digit at position
    'TOTAL_SIZE': Decimal('2.0'),
    'TOTAL_PARITY': Decimal('2.0'),
    'EXACT_TOTAL': Decimal('50.0'),  # Harder to hit exact sum
}


def draw_result(seed: str = None, round_id: int = 0, forced_digits: list = None) -> dict:
    if not seed:
        seed = generate_round_seed()
    if forced_digits and len(forced_digits) == 5 and all(0 <= d <= 9 for d in forced_digits):
        digits = list(forced_digits)
    else:
        digits = secure_random_digits(5)
    total = sum(digits)
    size = 'BIG' if total >= 23 else 'SMALL'
    parity = 'ODD' if total % 2 != 0 else 'EVEN'
    return {
        'digits': digits,
        'total': total,
        'size': size,
        'parity': parity,
        'seed_hash': hash_seed(seed, round_id),
    }


def calculate_payout(bet_type: str, bet_value: str, amount: Decimal,
                     digits: list, total: int, size: str, parity: str) -> tuple[bool, Decimal]:
    amount = Decimal(str(amount))
    bet_type = bet_type.upper()
    bet_value = str(bet_value).upper()
    pos_map = {pos: val for pos, val in zip(POSITIONS, digits)}

    if bet_type == 'POSITION':
        # Format: "A:3"
        try:
            pos, digit_str = bet_value.split(':')
            pos = pos.strip()
            target = int(digit_str.strip())
            if pos in pos_map and pos_map[pos] == target:
                return True, amount * ODDS['POSITION']
        except (ValueError, KeyError):
            pass
        return False, Decimal('0')

    elif bet_type == 'TOTAL_SIZE':
        if bet_value == size:
            return True, amount * ODDS['TOTAL_SIZE']
        return False, Decimal('0')

    elif bet_type == 'TOTAL_PARITY':
        if bet_value == parity:
            return True, amount * ODDS['TOTAL_PARITY']
        return False, Decimal('0')

    elif bet_type == 'EXACT_TOTAL':
        try:
            if int(bet_value) == total:
                return True, amount * ODDS['EXACT_TOTAL']
        except ValueError:
            pass
        return False, Decimal('0')

    return False, Decimal('0')


def get_potential_payout(bet_type: str, bet_value: str, amount: Decimal) -> Decimal:
    amount = Decimal(str(amount))
    bet_type = bet_type.upper()
    return amount * ODDS.get(bet_type, Decimal('0'))
