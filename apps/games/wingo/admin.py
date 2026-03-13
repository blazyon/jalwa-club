from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from .models import WingoRound, WingoBet


@admin.register(WingoRound)
class WingoRoundAdmin(admin.ModelAdmin):
    list_display = [
        'round_number', 'mode', 'status',
        'forced_result', 'forced_color',          # admin pre-set
        'result_number', 'result_color',           # actual result after settlement
        'result_size', 'ends_at',
    ]
    list_filter  = ['mode', 'status']
    ordering     = ['-round_number']
    search_fields = ['round_number']

    readonly_fields = [
        'id', 'seed_hash', 'created_at',
        'result_number', 'result_color', 'result_size',  # filled at settlement
    ]

    fieldsets = (
        ('Round Info', {
            'fields': ('id', 'mode', 'round_number', 'status', 'starts_at', 'ends_at')
        }),
        ('⚙️ Admin Pre-Set Result (applied when timer ends)', {
            'fields': ('forced_result', 'forced_color'),
            'description': (
                '✅ Set these fields to pre-program the round result. '
                'The round will NOT close immediately — it runs until the timer expires. '
                'When the timer hits zero, Celery applies these values and settles all bets. '
                '<br><br>'
                '<b>forced_result</b>: Number 0–9 to force as the winning number. Leave blank for random.<br>'
                '<b>forced_color</b>: Color to display (Green / Red / Violet). '
                'Leave blank to auto-derive from the number.<br><br>'
                '⚠️ Saving this form does NOT trigger early settlement. '
                'Use the "Force Settle NOW" action only if you need to end a round immediately.'
            ),
        }),
        ('📊 Result (auto-filled at settlement)', {
            'fields': ('result_number', 'result_color', 'result_size', 'seed_hash'),
        }),
    )

    actions = ['force_settle_now']

    def save_model(self, request, obj, form, change):
        """
        Save admin overrides ONLY. Do NOT trigger settlement here.
        The Celery task will apply forced_result / forced_color when the timer expires.
        """
        super().save_model(request, obj, form, change)

        # Give admin clear feedback about what will happen
        if obj.forced_result is not None or obj.forced_color:
            parts = []
            if obj.forced_result is not None:
                parts.append(f"Number={obj.forced_result}")
            if obj.forced_color:
                parts.append(f"Color={obj.forced_color}")
            messages.success(
                request,
                f"✅ Pre-set result saved for Wingo[{obj.mode}] #{obj.round_number}: "
                f"{', '.join(parts)}. "
                f"Will be applied automatically when the round timer ends."
            )
        else:
            messages.info(
                request,
                f"Round #{obj.round_number} [{obj.mode}] saved. "
                f"No forced result set — random result will be drawn at round end."
            )

    @admin.action(description='⚡ Force Settle NOW (bypasses timer — use with caution)')
    def force_settle_now(self, request, queryset):
        """
        Emergency action: immediately settle selected rounds regardless of timer.
        Use only when needed — normal flow lets rounds complete naturally.
        """
        from .services import settle_round
        count = 0
        for round_obj in queryset:
            if round_obj.status != WingoRound.Status.COMPLETED:
                try:
                    settle_round(round_obj.id)
                    count += 1
                except Exception as e:
                    self.message_user(
                        request,
                        f"Error settling #{round_obj.round_number} [{round_obj.mode}]: {e}",
                        level=messages.ERROR
                    )
        self.message_user(request, f"✅ {count} round(s) force-settled immediately.")


@admin.register(WingoBet)
class WingoBetAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'round_mode', 'round_num', 'bet_type', 'bet_value',
        'amount', 'is_winner', 'payout_amount', 'created_at'
    ]
    list_filter   = ['bet_type', 'is_winner', 'round__mode']
    search_fields = ['user__username']
    readonly_fields = [f.name for f in WingoBet._meta.fields]
    ordering = ['-created_at']

    def round_mode(self, obj):
        return obj.round.mode
    round_mode.short_description = 'Mode'

    def round_num(self, obj):
        return f"#{obj.round.round_number}"
    round_num.short_description = 'Round'