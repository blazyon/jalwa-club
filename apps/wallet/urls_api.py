from django.urls import path
from .views_api import WalletBalanceAPIView, TransactionHistoryAPIView

urlpatterns = [
    path('balance/', WalletBalanceAPIView.as_view(), name='api_wallet_balance'),
    path('transactions/', TransactionHistoryAPIView.as_view(), name='api_transactions'),
]
