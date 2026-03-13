from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import FiveDRound, FiveDbet
from .services import get_or_create_current_round


@login_required
def fived_view(request):
    try:
        current_round = get_or_create_current_round()
    except Exception as e:
        messages.error(request, f'Could not load game round: {e}')
        return redirect('home')

    history = FiveDRound.objects.filter(
        status='COMPLETED'
    ).order_by('-round_number')[:20]

    my_bets = FiveDbet.objects.filter(
        user=request.user,
        round=current_round
    ).order_by('-created_at')

    return render(request, 'games/five_d.html', {
        'current_round': current_round,
        'history': history,
        'my_bets': my_bets,
    })
