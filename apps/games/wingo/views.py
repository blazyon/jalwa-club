from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import WingoRound, WingoBet
from .services import get_or_create_current_round

VALID_MODES = {'1MIN', '3MIN', '5MIN'}
MODE_LABELS = {'1MIN': '1 Min', '3MIN': '3 Min', '5MIN': '5 Min'}


@login_required
def wingo_view(request):
    mode = request.GET.get('mode', '1MIN').upper()
    if mode not in VALID_MODES:
        mode = '1MIN'

    try:
        current_round = get_or_create_current_round(mode=mode)
    except Exception as e:
        messages.error(request, f'Could not load game round: {e}')
        return redirect('home')

    history = WingoRound.objects.filter(
        mode=mode, status='COMPLETED'
    ).order_by('-round_number')[:20]

    my_bets = WingoBet.objects.filter(
        user=request.user,
        round=current_round
    ).order_by('-created_at')

    # All bets history for this user (last 30, this mode)
    bet_history = WingoBet.objects.filter(
        user=request.user,
        round__mode=mode,
        round__status='COMPLETED',
    ).select_related('round').order_by('-created_at')[:30]

    return render(request, 'games/wingo.html', {
        'current_round': current_round,
        'history': history,
        'my_bets': my_bets,
        'bet_history': bet_history,
        'current_mode': mode,
        'mode_label': MODE_LABELS.get(mode, '1 Min'),
        'valid_modes': [
            {'key': '1MIN', 'label': '1 Min'},
            {'key': '3MIN', 'label': '3 Min'},
            {'key': '5MIN', 'label': '5 Min'},
        ],
    })
