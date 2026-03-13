from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views_api import RegisterAPIView, LoginAPIView, ProfileAPIView, ReferralsAPIView

urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='api_register'),
    path('login/', LoginAPIView.as_view(), name='api_login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='api_token_refresh'),
    path('profile/', ProfileAPIView.as_view(), name='api_profile'),
    path('referrals/', ReferralsAPIView.as_view(), name='api_referrals'),
]
