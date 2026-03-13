from django.contrib import admin
from django.contrib import messages
from .models import K3Round, K3Bet


@admin.register(K3Round)
class K3RoundAdmin(admin.ModelAdmin):
    list_display = [
        'round_number', 'status',
        'forced_dice',                        # admin pre-set
        'dice1', 'dice2', 'dice3', 'total',   # actual result
        'ends_at',
    ]
    list_filter   = ['status']
    ordering      = ['-round_number']
    search_fields = ['round_number']

    readonly_fields = [
        'id', 'seed_hash', 'result_tags', 'created_at',
        'dice1', 'dice2', 'dice3', 'total',  # filled at settlement
    ]

    fieldsets = (
        ('Round Info', {
            'fields': ('id', 'round_number', 'status', 'starts_at', 'ends_at')
        }),
        ('⚙️ Admin Pre-Set Result (applied when timer ends)', {
            'fields': ('forced_dice',),
            'description': (
                '✅ Enter comma-separated dice values e.g. <b>3,5,2</b> (each digit must be 1–6). '
                'The round continues running — this value is applied automatically '
                'when the Celery task detects the timer has expired.<br><br>'
                '⚠️ Saving does NOT trigger early settlement. '
                'Use the "Force Settle NOW" action only if you need immediate closure.'
            ),
        }),
        ('📊 Result (auto-filled at settlement)', {
            'fields': ('dice1', 'dice2', 'dice3', 'total', 'result_tags', 'seed_hash'),
        }),
    )

    actions = ['force_settle_now']

    def save_model(self, request, obj, form, change):
        """Save forced_dice override only. Never trigger early settlement."""
        super().save_model(request, obj, form, change)

        if obj.forced_dice:
            messages.success(
                request,
                f"✅ Forced dice saved for K3 Round #{obj.round_number}: "
                f"'{obj.forced_dice}'. Will be applied when timer ends."
            )
        else:
            messages.info(
                request,
                f"K3 Round #{obj.round_number} saved. "
                f"No forced dice set — random dice will be drawn at round end."
            )

    @admin.action(description='⚡ Force Settle NOW (bypasses timer — use with caution)')
    def force_settle_now(self, request, queryset):
        from .services import settle_round
        count = 0
        for round_obj in queryset:
            if round_obj.status != K3Round.Status.COMPLETED:
                try:
                    settle_round(round_obj.id)
                    count += 1
                except Exception as e:
                    self.message_user(
                        request,
                        f"Error settling K3 #{round_obj.round_number}: {e}",
                        level=messages.ERROR
                    )
        self.message_user(request, f"✅ {count} K3 round(s) force-settled.")


@admin.register(K3Bet)
class K3BetAdmin(admin.ModelAdmin):
    list_display  = ['user', 'round', 'bet_type', 'bet_value',
                     'amount', 'is_winner', 'payout_amount']
    list_filter   = ['bet_type', 'is_winner']
    readonly_fields = [f.name for f in K3Bet._meta.fields]