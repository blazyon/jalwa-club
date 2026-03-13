from django.urls import path
from .views_api import CurrentRoundAPIView, RoundHistoryAPIView, PlaceBetAPIView, MyBetsAPIView

urlpatterns = [
    path('current/', CurrentRoundAPIView.as_view(), name='wingo_current_round'),
    path('history/', RoundHistoryAPIView.as_view(), name='wingo_round_history'),
    path('bet/', PlaceBetAPIView.as_view(), name='wingo_place_bet'),
    path('my-bets/', MyBetsAPIView.as_view(), name='wingo_my_bets'),
]
