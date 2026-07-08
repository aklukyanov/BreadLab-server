from django.shortcuts import render
import datetime

from django.shortcuts import render

def home(request):
    return render(request, 'home.html')

def login_view(request):
    return render(request, 'auth/login.html')

def register_view(request):
    return render(request, 'auth/register.html')

def dashboard_view(request):
    return render(request, 'dashboard.html')