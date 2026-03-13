from django.urls import path
from .views_api import CurrentK3RoundAPIView, K3RoundHistoryAPIView, PlaceK3BetAPIView, MyK3BetsAPIView

urlpatterns = [
    path('current/', CurrentK3RoundAPIView.as_view()),
    path('history/', K3RoundHistoryAPIView.as_view()),
    path('bet/', PlaceK3BetAPIView.as_view()),
    path('my-bets/', MyK3BetsAPIView.as_view()),
]
