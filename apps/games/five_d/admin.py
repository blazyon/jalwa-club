from django.contrib import admin
from django.contrib import messages
from .models import FiveDRound, FiveDbet


@admin.register(FiveDRound)
class FiveDRoundAdmin(admin.ModelAdmin):
    list_display = [
        'round_number', 'status',
        'forced_digits',                                          # admin pre-set
        'digit_a', 'digit_b', 'digit_c', 'digit_d', 'digit_e',  # actual result
        'total', 'ends_at',
    ]
    list_filter   = ['status']
    ordering      = ['-round_number']
    search_fields = ['round_number']

    readonly_fields = [
        'id', 'seed_hash', 'created_at',
        'digit_a', 'digit_b', 'digit_c', 'digit_d', 'digit_e', 'total',
    ]

    fieldsets = (
        ('Round Info', {
            'fields': ('id', 'round_number', 'status', 'starts_at', 'ends_at')
        }),
        ('⚙️ Admin Pre-Set Result (applied when timer ends)', {
            'fields': ('forced_digits',),
            'description': (
                '✅ Enter 5 comma-separated digits e.g. <b>1,2,3,4,5</b> (each 0–9). '
                'The round will NOT end immediately. '
                'Celery applies this result when the timer expires.<br><br>'
                '⚠️ Saving does NOT trigger early settlement. '
                'Use the "Force Settle NOW" action only for emergency closure.'
            ),
        }),
        ('📊 Result (auto-filled at settlement)', {
            'fields': ('digit_a', 'digit_b', 'digit_c', 'digit_d', 'digit_e', 'total', 'seed_hash'),
        }),
    )

    actions = ['force_settle_now']

    def save_model(self, request, obj, form, change):
        """Save forced_digits override only. Never trigger early settlement."""
        super().save_model(request, obj, form, change)

        if obj.forced_digits:
            messages.success(
                request,
                f"✅ Forced digits saved for 5D Round #{obj.round_number}: "
                f"'{obj.forced_digits}'. Will be applied when timer ends."
            )
        else:
            messages.info(
                request,
                f"5D Round #{obj.round_number} saved. "
                f"No forced digits set — random digits will be drawn at round end."
            )

    @admin.action(description='⚡ Force Settle NOW (bypasses timer — use with caution)')
    def force_settle_now(self, request, queryset):
        from .services import settle_round
        count = 0
        for round_obj in queryset:
            if round_obj.status != FiveDRound.Status.COMPLETED:
                try:
                    settle_round(round_obj.id)
                    count += 1
                except Exception as e:
                    self.message_user(
                        request,
                        f"Error settling 5D #{round_obj.round_number}: {e}",
                        level=messages.ERROR
                    )
        self.message_user(request, f"✅ {count} 5D round(s) force-settled.")


@admin.register(FiveDbet)
class FiveDBetAdmin(admin.ModelAdmin):
    list_display  = ['user', 'round', 'bet_type', 'bet_value',
                     'amount', 'is_winner', 'payout_amount']
    list_filter   = ['bet_type', 'is_winner']
    readonly_fields = [f.name for f in FiveDbet._meta.fields]