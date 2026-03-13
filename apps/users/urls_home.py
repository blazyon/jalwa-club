from django.urls import path
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def home_view(request):
    return render(request, 'home.html')


urlpatterns = [
    path('', home_view, name='home'),
]
