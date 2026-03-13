from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics
from .models import Wallet, Transaction
from .serializers import WalletSerializer, TransactionSerializer


class WalletBalanceAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # BUG FIX: use get_or_create so users without wallets don't get 500 errors
        wallet, _ = Wallet.objects.get_or_create(
            user=request.user,
            defaults={'balance': 0}
        )
        return Response(WalletSerializer(wallet).data)


class TransactionHistoryAPIView(generics.ListAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Transaction.objects.filter(
            wallet__user=self.request.user
        ).order_by('-created_at')
