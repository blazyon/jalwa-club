from django.urls import path
from .views_api import CurrentFiveDRoundAPIView, FiveDHistoryAPIView, PlaceFiveDAPIView, MyFiveDBetsAPIView

urlpatterns = [
    path('current/', CurrentFiveDRoundAPIView.as_view()),
    path('history/', FiveDHistoryAPIView.as_view()),
    path('bet/', PlaceFiveDAPIView.as_view()),
    path('my-bets/', MyFiveDBetsAPIView.as_view()),
]
