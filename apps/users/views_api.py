from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.conf import settings
from .models import User
from .serializers import RegisterSerializer, UserProfileSerializer
from apps.wallet.models import Wallet
from core.services import WalletService


class RegisterAPIView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = 'anon'

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Always create the wallet atomically with the user
            wallet, _ = Wallet.objects.get_or_create(user=user, defaults={'balance': 0})
            bonus = getattr(settings, 'DEMO_SIGNUP_BONUS', 1000)
            if bonus > 0:
                WalletService.credit(
                    wallet, bonus,
                    reference=f'SIGNUP_BONUS_{user.id}',
                    description='Demo signup bonus — welcome gift',
                    category='SIGNUP_BONUS',
                )
            refresh = RefreshToken.for_user(user)
            return Response({
                'message': 'Account created. This is a DEMO platform — no real money.',
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserProfileSerializer(user).data,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = 'anon'

    def post(self, request):
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '')
        if not username or not password:
            return Response({'error': 'Username and password required.'}, status=400)
        user = authenticate(request, username=username, password=password)
        if not user:
            return Response({'error': 'Invalid credentials.'}, status=401)
        if user.is_blocked:
            return Response({'error': 'Account is blocked. Contact support.'}, status=403)
        # Ensure wallet exists on login
        Wallet.objects.get_or_create(user=user, defaults={'balance': 0})
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserProfileSerializer(user).data,
        })


class ProfileAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # Ensure wallet exists when profile is fetched
        Wallet.objects.get_or_create(user=self.request.user, defaults={'balance': 0})
        return self.request.user


class ReferralsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        referrals = User.objects.filter(referred_by=request.user).values(
            'username', 'date_joined'
        )
        return Response({
            'referral_code': request.user.referral_code,
            'total_referrals': referrals.count(),
            'referrals': list(referrals),
        })
