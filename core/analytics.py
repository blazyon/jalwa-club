"""
Analytics admin view - accessible at /admin/analytics/
Shows revenue, user stats, game stats.
"""
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta


@staff_member_required
def analytics_view(request):
    from apps.wallet.models import Transaction, Wallet
    from apps.users.models import User
    from apps.games.wingo.models import WingoRound, WingoBet
    from apps.games.k3.models import K3Round, K3Bet
    from apps.games.five_d.models import FiveDRound, FiveDbet

    now = timezone.now()
    last_24h = now - timedelta(hours=24)
    last_7d  = now - timedelta(days=7)

    # User stats
    total_users    = User.objects.count()
    new_users_24h  = User.objects.filter(date_joined__gte=last_24h).count()
    active_7d      = User.objects.filter(wingo_bets__created_at__gte=last_7d).distinct().count()
    blocked_users  = User.objects.filter(is_blocked=True).count()

    # Wallet stats
    total_balance = Wallet.objects.aggregate(s=Sum('balance'))['s'] or 0
    credits_24h   = Transaction.objects.filter(
        tx_type='CREDIT', created_at__gte=last_24h
    ).aggregate(s=Sum('amount'))['s'] or 0
    debits_24h    = Transaction.objects.filter(
        tx_type='DEBIT', created_at__gte=last_24h
    ).aggregate(s=Sum('amount'))['s'] or 0

    # Game stats - Wingo
    wingo_rounds_today = WingoRound.objects.filter(
        status='COMPLETED', created_at__date=now.date()
    ).count()
    wingo_bets_24h = WingoBet.objects.filter(created_at__gte=last_24h)
    wingo_total_wagered = wingo_bets_24h.aggregate(s=Sum('amount'))['s'] or 0
    wingo_total_paid    = wingo_bets_24h.filter(
        is_winner=True
    ).aggregate(s=Sum('payout_amount'))['s'] or 0

    # K3
    k3_bets_24h = K3Bet.objects.filter(created_at__gte=last_24h)
    k3_total_wagered = k3_bets_24h.aggregate(s=Sum('amount'))['s'] or 0
    k3_total_paid    = k3_bets_24h.filter(
        is_winner=True
    ).aggregate(s=Sum('payout_amount'))['s'] or 0

    # 5D
    fived_bets_24h = FiveDbet.objects.filter(created_at__gte=last_24h)
    fived_total_wagered = fived_bets_24h.aggregate(s=Sum('amount'))['s'] or 0
    fived_total_paid    = fived_bets_24h.filter(
        is_winner=True
    ).aggregate(s=Sum('payout_amount'))['s'] or 0

    context = {
        'title': 'Revenue Analytics',
        'total_users': total_users,
        'new_users_24h': new_users_24h,
        'active_7d': active_7d,
        'blocked_users': blocked_users,
        'total_balance': total_balance,
        'credits_24h': credits_24h,
        'debits_24h': debits_24h,
        'wingo_rounds_today': wingo_rounds_today,
        'wingo_total_wagered': wingo_total_wagered,
        'wingo_total_paid': wingo_total_paid,
        'wingo_house_edge': wingo_total_wagered - wingo_total_paid,
        'k3_total_wagered': k3_total_wagered,
        'k3_total_paid': k3_total_paid,
        'k3_house_edge': k3_total_wagered - k3_total_paid,
        'fived_total_wagered': fived_total_wagered,
        'fived_total_paid': fived_total_paid,
        'fived_house_edge': fived_total_wagered - fived_total_paid,
        'total_wagered': wingo_total_wagered + k3_total_wagered + fived_total_wagered,
        'total_house_edge': (wingo_total_wagered - wingo_total_paid) + (k3_total_wagered - k3_total_paid) + (fived_total_wagered - fived_total_paid),
    }
    return render(request, 'admin/analytics.html', context)
