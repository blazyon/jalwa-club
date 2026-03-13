import secrets
import string
import hashlib
from decimal import Decimal


def generate_referral_code(length=8):
    """Generate a cryptographically secure referral code."""
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_round_seed():
    """Generate a secure seed for round result generation."""
    return secrets.token_hex(32)


def secure_random_int(min_val: int, max_val: int) -> int:
    """Generate a cryptographically secure random integer in [min_val, max_val]."""
    return secrets.randbelow(max_val - min_val + 1) + min_val


def secure_random_digits(count: int) -> list[int]:
    """Generate `count` secure random digits 0-9."""
    return [secrets.randbelow(10) for _ in range(count)]


def hash_seed(seed: str, round_id: int) -> str:
    """Create a verifiable hash from seed + round_id."""
    data = f"{seed}:{round_id}".encode()
    return hashlib.sha256(data).hexdigest()


def to_decimal(value) -> Decimal:
    return Decimal(str(value))
