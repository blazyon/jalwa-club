import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone


class WingoRound(models.Model):
    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open for Bets'
        LOCKED = 'LOCKED', 'Locked (Processing)'
        COMPLETED = 'COMPLETED', 'Completed'

    class Mode(models.TextChoices):
        MIN1 = '1MIN', '1 Minute'
        MIN3 = '3MIN', '3 Minutes'
        MIN5 = '5MIN', '5 Minutes'

    # ── NEW: Admin can pre-set a color override ──────────────────────
    class ForcedColor(models.TextChoices):
        GREEN  = 'GREEN',  'Green'
        RED    = 'RED',    'Red'
        VIOLET = 'VIOLET', 'Violet'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mode = models.CharField(max_length=8, choices=Mode.choices, default=Mode.MIN1)
    round_number = models.BigIntegerField()
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.OPEN)

    # ── Actual result (filled at settlement time) ────────────────────
    result_number = models.IntegerField(null=True, blank=True)
    result_color  = models.CharField(max_length=16, blank=True)
    result_size   = models.CharField(max_length=8,  blank=True)

    # ── Admin pre-set overrides (stored, applied only when timer ends) ─
    forced_result = models.IntegerField(
        null=True, blank=True,
        help_text='Admin override: force result NUMBER (0-9). Applied when timer ends, NOT immediately.'
    )
    forced_color = models.CharField(
        max_length=16, blank=True, null=True,
        choices=ForcedColor.choices,
        help_text=(
            'Admin override: force result COLOR (Green / Red / Violet). '
            'If set together with forced_result, both are applied at round end. '
            'Leave blank to let color be derived automatically from the number.'
        )
    )

    seed_hash  = models.CharField(max_length=64, blank=True)
    starts_at  = models.DateTimeField()
    ends_at    = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'wingo_rounds'
        ordering = ['-round_number', 'mode']
        unique_together = [('mode', 'round_number')]
        indexes = [
            models.Index(fields=['mode', '-round_number']),
            models.Index(fields=['mode', 'status']),
        ]

    def __str__(self):
        return f"Wingo[{self.mode}] #{self.round_number} [{self.status}]"

    @property
    def is_accepting_bets(self):
        now = timezone.now()
        return self.status == self.Status.OPEN and now < self.ends_at

    @property
    def seconds_remaining(self):
        if self.status != self.Status.OPEN:
            return 0
        delta = self.ends_at - timezone.now()
        return max(0, int(delta.total_seconds()))

    @property
    def duration_seconds(self):
        return {'1MIN': 60, '3MIN': 180, '5MIN': 300}.get(self.mode, 60)


class WingoBet(models.Model):
    class BetType(models.TextChoices):
        NUMBER = 'NUMBER', 'Number (0-9)'
        COLOR  = 'COLOR',  'Color'
        SIZE   = 'SIZE',   'Big/Small'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              related_name='wingo_bets')
    round = models.ForeignKey(WingoRound, on_delete=models.CASCADE, related_name='bets')
    bet_type  = models.CharField(max_length=10, choices=BetType.choices)
    bet_value = models.CharField(max_length=16)
    amount    = models.DecimalField(max_digits=12, decimal_places=2)
    potential_payout = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    is_winner    = models.BooleanField(null=True, blank=True)
    payout_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    settled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'wingo_bets'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'round', 'bet_type', 'bet_value'],
                name='unique_wingo_bet_per_round'
            )
        ]
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['round', 'is_winner']),
        ]

    def __str__(self):
        return f"WingoBet({self.user.username}, {self.bet_type}={self.bet_value}, ₹{self.amount})"
