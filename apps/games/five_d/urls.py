from django.urls import path
from .views import fived_view

urlpatterns = [
    path('', fived_view, name='five_d'),
]
