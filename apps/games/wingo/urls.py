from django.urls import path
from .views import wingo_view

urlpatterns = [
    path('wingo/', wingo_view, name='wingo'),
]
