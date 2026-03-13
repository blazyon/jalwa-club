from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User
from .serializers import RegisterSerializer
from apps.wallet.models import Wallet, Transaction
from core.services import WalletService
from django.conf import settings


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user:
            if user.is_blocked:
                messages.error(request, 'Account is blocked. Contact support.')
                return render(request, 'users/login.html')
            # Ensure wallet exists on login
            Wallet.objects.get_or_create(user=user, defaults={'balance': 0})
            login(request, user)
            return redirect(request.GET.get('next', 'home'))
        messages.error(request, 'Invalid username or password.')
    return render(request, 'users/login.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        data = {
            'username': request.POST.get('username', '').strip(),
            'email': request.POST.get('email', '').strip(),
            'phone': request.POST.get('phone', '').strip(),
            'password': request.POST.get('password', ''),
            'password2': request.POST.get('password2', ''),
            'referral_code': request.POST.get('referral_code', '').strip(),
        }
        serializer = RegisterSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            # Create wallet and credit signup bonus atomically
            wallet, _ = Wallet.objects.get_or_create(user=user, defaults={'balance': 0})
            bonus = getattr(settings, 'DEMO_SIGNUP_BONUS', 1000)
            if bonus > 0:
                WalletService.credit(
                    wallet, bonus,
                    reference=f'SIGNUP_BONUS_{user.id}',
                    description='Demo signup bonus — welcome gift',
                    category='SIGNUP_BONUS',
                )
            login(request, user)
            messages.success(request, f'Welcome {user.username}! You received {bonus} demo coins.')
            return redirect('home')
        for field, errs in serializer.errors.items():
            for err in errs:
                messages.error(request, f"{field}: {err}")
    return render(request, 'users/register.html', {
        'referral_code': request.GET.get('ref', '')
    })


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def profile_view(request):
    referrals = User.objects.filter(referred_by=request.user)
    transactions = Transaction.objects.filter(
        wallet__user=request.user
    ).order_by('-created_at')[:20]
    return render(request, 'users/profile.html', {
        'referrals': referrals,
        'transactions': transactions,
    })
