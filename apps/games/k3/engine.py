"""
K3 Game Engine
--------------
Three dice (1-6) rolled each round.
Total ranges from 3-18.
Big = total 11-17, Small = total 4-10.
Triples (all same): total 3(triple-1) or 18(triple-6) do not count as Big/Small.
"""
from decimal import Decimal
from core.utils import secure_random_int, generate_round_seed, hash_seed

# Payout odds
ODDS = {
    'TOTAL_SPECIFIC': {  # odds vary by total
        3:  Decimal('207.36'),
        4:  Decimal('69.12'),
        5:  Decimal('34.56'),
        6:  Decimal('20.74'),
        7:  Decimal('13.82'),
        8:  Decimal('9.88'),
        9:  Decimal('8.64'),
        10: Decimal('8.64'),
        11: Decimal('8.64'),
        12: Decimal('8.64'),
        13: Decimal('9.88'),
        14: Decimal('13.82'),
        15: Decimal('20.74'),
        16: Decimal('34.56'),
        17: Decimal('69.12'),
        18: Decimal('207.36'),
    },
    'SIZE': Decimal('2.0'),
    'PARITY': Decimal('2.0'),
    'SPECIFIC_TRIPLE': Decimal('207.36'),
    'ANY_TRIPLE': Decimal('34.56'),
    'SPECIFIC_DOUBLE': Decimal('8.33'),
    'TWO_DIFFERENT': Decimal('6.0'),
    'THREE_DIFFERENT': Decimal('1.5'),
}


def draw_result(seed: str = None, round_id: int = 0, forced_dice: list = None) -> dict:
    if not seed:
        seed = generate_round_seed()
    if forced_dice and len(forced_dice) == 3 and all(1 <= d <= 6 for d in forced_dice):
        dice = list(forced_dice)
    else:
        dice = [secure_random_int(1, 6) for _ in range(3)]
    total = sum(dice)
    tags = _compute_tags(dice, total)
    return {
        'dice': dice,
        'total': total,
        'tags': tags,
        'seed_hash': hash_seed(seed, round_id),
    }


def _compute_tags(dice: list, total: int) -> list[str]:
    tags = []
    sorted_dice = sorted(dice)
    is_triple = dice[0] == dice[1] == dice[2]
    is_double = (not is_triple) and (
        dice[0] == dice[1] or dice[1] == dice[2] or dice[0] == dice[2]
    )
    all_different = len(set(dice)) == 3

    if is_triple:
        tags.append('TRIPLE')
        tags.append(f'TRIPLE_{dice[0]}')
    elif is_double:
        tags.append('DOUBLE')
        # Find the doubled value
        for v in set(dice):
            if dice.count(v) == 2:
                tags.append(f'DOUBLE_{v}')
    if all_different:
        tags.append('ALL_DIFFERENT')

    # Size (triples at 3 or 18 don't count)
    if not is_triple:
        if 4 <= total <= 10:
            tags.append('SMALL')
        elif 11 <= total <= 17:
            tags.append('BIG')
    else:
        tags.append('INVALID_SIZE')  # Triples don't get Big/Small

    # Parity
    if total % 2 == 0:
        tags.append('EVEN')
    else:
        tags.append('ODD')

    return tags


def calculate_payout(bet_type: str, bet_value: str, amount: Decimal,
                     dice: list, total: int, tags: list) -> tuple[bool, Decimal]:
    amount = Decimal(str(amount))
    bet_type = bet_type.upper()
    bet_value = str(bet_value).upper()

    if bet_type == 'TOTAL':
        target = int(bet_value)
        if total == target:
            odds = ODDS['TOTAL_SPECIFIC'].get(target, Decimal('0'))
            return True, amount * odds
        return False, Decimal('0')

    elif bet_type == 'SIZE':
        if bet_value in tags:
            return True, amount * ODDS['SIZE']
        return False, Decimal('0')

    elif bet_type == 'PARITY':
        if bet_value in tags:
            return True, amount * ODDS['PARITY']
        return False, Decimal('0')

    elif bet_type == 'SPECIFIC_TRIPLE':
        tag = f'TRIPLE_{bet_value}'
        if tag in tags:
            return True, amount * ODDS['SPECIFIC_TRIPLE']
        return False, Decimal('0')

    elif bet_type == 'ANY_TRIPLE':
        if 'TRIPLE' in tags:
            return True, amount * ODDS['ANY_TRIPLE']
        return False, Decimal('0')

    elif bet_type == 'SPECIFIC_DOUBLE':
        tag = f'DOUBLE_{bet_value}'
        if tag in tags:
            return True, amount * ODDS['SPECIFIC_DOUBLE']
        return False, Decimal('0')

    elif bet_type == 'TWO_DIFFERENT':
        # bet_value is "X,Y" e.g. "1,3"
        try:
            parts = sorted([int(x) for x in bet_value.split(',')])
            if len(parts) == 2:
                sorted_dice = sorted(dice)
                # Check if these two values appear with the third being different
                if parts[0] in dice and parts[1] in dice:
                    return True, amount * ODDS['TWO_DIFFERENT']
        except ValueError:
            pass
        return False, Decimal('0')

    elif bet_type == 'THREE_DIFFERENT':
        if 'ALL_DIFFERENT' in tags:
            return True, amount * ODDS['THREE_DIFFERENT']
        return False, Decimal('0')

    return False, Decimal('0')


def get_potential_payout(bet_type: str, bet_value: str, amount: Decimal) -> Decimal:
    amount = Decimal(str(amount))
    bet_type = bet_type.upper()
    bet_value = str(bet_value).upper()

    if bet_type == 'TOTAL':
        try:
            return amount * ODDS['TOTAL_SPECIFIC'].get(int(bet_value), Decimal('0'))
        except ValueError:
            return Decimal('0')
    elif bet_type in ODDS:
        odds = ODDS[bet_type]
        if isinstance(odds, dict):
            return Decimal('0')
        return amount * odds
    return Decimal('0')
