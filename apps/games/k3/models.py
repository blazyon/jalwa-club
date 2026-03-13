import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class K3Round(models.Model):
    class Status(models.TextChoices):
        OPEN      = 'OPEN',      'Open'
        LOCKED    = 'LOCKED',    'Locked'
        COMPLETED = 'COMPLETED', 'Completed'

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    round_number = models.BigIntegerField(unique=True)
    status       = models.CharField(max_length=12, choices=Status.choices, default=Status.OPEN)

    # ── Actual result (filled at settlement) ─────────────────────────
    dice1 = models.IntegerField(null=True, blank=True)
    dice2 = models.IntegerField(null=True, blank=True)
    dice3 = models.IntegerField(null=True, blank=True)
    total = models.IntegerField(null=True, blank=True)
    result_tags = models.JSONField(default=list, blank=True)
    seed_hash   = models.CharField(max_length=64, blank=True)

    # ── Admin pre-set override ────────────────────────────────────────
    forced_dice = models.CharField(
        max_length=16, blank=True, null=True,
        help_text=(
            'Admin override: comma-separated dice values e.g. "3,5,2" (each 1–6). '
            'Applied when the round timer ends, NOT immediately.'
        )
    )

    starts_at  = models.DateTimeField()
    ends_at    = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'k3_rounds'
        ordering = ['-round_number']

    def __str__(self):
        return f"K3Round #{self.round_number} [{self.status}]"

    @property
    def is_accepting_bets(self):
        return self.status == self.Status.OPEN and timezone.now() < self.ends_at

    @property
    def seconds_remaining(self):
        if self.status != self.Status.OPEN:
            return 0
        delta = self.ends_at - timezone.now()
        return max(0, int(delta.total_seconds()))


class K3Bet(models.Model):
    class BetType(models.TextChoices):
        TOTAL           = 'TOTAL',           'Total Sum'
        SIZE            = 'SIZE',            'Big/Small'
        PARITY          = 'PARITY',          'Odd/Even'
        SPECIFIC_TRIPLE = 'SPECIFIC_TRIPLE', 'Specific Triple'
        ANY_TRIPLE      = 'ANY_TRIPLE',      'Any Triple'
        SPECIFIC_DOUBLE = 'SPECIFIC_DOUBLE', 'Specific Double'
        TWO_DIFFERENT   = 'TWO_DIFFERENT',   'Two Different Dice'
        THREE_DIFFERENT = 'THREE_DIFFERENT', 'All Different'

    id    = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              related_name='k3_bets')
    round = models.ForeignKey(K3Round, on_delete=models.CASCADE, related_name='bets')
    bet_type  = models.CharField(max_length=20, choices=BetType.choices)
    bet_value = models.CharField(max_length=32)
    amount    = models.DecimalField(max_digits=12, decimal_places=2)
    potential_payout = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    is_winner    = models.BooleanField(null=True, blank=True)
    payout_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    settled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'k3_bets'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'round', 'bet_type', 'bet_value'],
                name='unique_k3_bet_per_round'
            )
        ]
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['round', 'is_winner']),
        ]

    def __str__(self):
        return f"K3Bet({self.user_id}, {self.bet_type}={self.bet_value}, {self.amount})"
