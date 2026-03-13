from django.urls import path
from .views import k3_view

urlpatterns = [
    path('', k3_view, name='k3'),
]
