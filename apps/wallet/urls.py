from django.urls import path
from .views import wallet_view, deposit_view, withdraw_view

urlpatterns = [
    path('', wallet_view, name='wallet'),
    path('deposit/', deposit_view, name='deposit'),
    path('withdraw/', withdraw_view, name='withdraw'),
]
