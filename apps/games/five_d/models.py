import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class FiveDRound(models.Model):
    class Status(models.TextChoices):
        OPEN      = 'OPEN',      'Open'
        LOCKED    = 'LOCKED',    'Locked'
        COMPLETED = 'COMPLETED', 'Completed'

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    round_number = models.BigIntegerField(unique=True)
    status       = models.CharField(max_length=12, choices=Status.choices, default=Status.OPEN)

    # ── Actual result (filled at settlement) ─────────────────────────
    digit_a = models.IntegerField(null=True, blank=True)
    digit_b = models.IntegerField(null=True, blank=True)
    digit_c = models.IntegerField(null=True, blank=True)
    digit_d = models.IntegerField(null=True, blank=True)
    digit_e = models.IntegerField(null=True, blank=True)
    total     = models.IntegerField(null=True, blank=True)
    seed_hash = models.CharField(max_length=64, blank=True)

    # ── Admin pre-set override ────────────────────────────────────────
    forced_digits = models.CharField(
        max_length=20, blank=True, null=True,
        help_text=(
            'Admin override: 5 comma-separated digits e.g. "1,2,3,4,5" (each 0–9). '
            'Applied when the round timer ends, NOT immediately.'
        )
    )

    starts_at  = models.DateTimeField()
    ends_at    = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'fived_rounds'
        ordering = ['-round_number']

    def __str__(self):
        return f"5DRound #{self.round_number} [{self.status}]"

    @property
    def digits(self):
        return [self.digit_a, self.digit_b, self.digit_c, self.digit_d, self.digit_e]

    @property
    def is_accepting_bets(self):
        return self.status == self.Status.OPEN and timezone.now() < self.ends_at

    @property
    def seconds_remaining(self):
        if self.status != self.Status.OPEN:
            return 0
        delta = self.ends_at - timezone.now()
        return max(0, int(delta.total_seconds()))


class FiveDbet(models.Model):
    class BetType(models.TextChoices):
        POSITION     = 'POSITION',     'Position Digit'
        TOTAL_SIZE   = 'TOTAL_SIZE',   'Total Size'
        TOTAL_PARITY = 'TOTAL_PARITY', 'Total Parity'
        EXACT_TOTAL  = 'EXACT_TOTAL',  'Exact Total Sum'

    id    = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              related_name='fived_bets')
    round = models.ForeignKey(FiveDRound, on_delete=models.CASCADE, related_name='bets')
    bet_type  = models.CharField(max_length=20, choices=BetType.choices)
    bet_value = models.CharField(max_length=32)
    amount    = models.DecimalField(max_digits=12, decimal_places=2)
    potential_payout = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    is_winner    = models.BooleanField(null=True, blank=True)
    payout_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    settled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'fived_bets'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'round', 'bet_type', 'bet_value'],
                name='unique_fived_bet_per_round'
            )
        ]
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['round', 'is_winner']),
        ]

    def __str__(self):
        return f"5DBet({self.user_id}, {self.bet_type}={self.bet_value}, {self.amount})"