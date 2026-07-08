from django.shortcuts import render
import datetime

from django.shortcuts import render

from core.models import User
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password

def home(request):
    return render(request, 'home.html')

def login_view(request):
    if request.method == 'POST':
        vk_id = request.POST.get('vk_id')
        password = request.POST.get('password')

        # 2. Проверка, существует ли пользователь с таким external_id
        if not User.objects.filter(external_id=vk_id).exists():
            return render(request, 'home.html', {
                'error': 'Сначала напишите что-нибудь боту Вконтакте',
                'modal_open': 'login'
            })

        user = User.objects.get(external_id=vk_id)
        if not check_password(password, user.password):
            return render(request, 'home.html', {
                'error': 'Пароль не подходит',
                'modal_open': 'login'
            })



    return render(request, 'auth/login.html')


def register_view(request):
    if request.method == 'POST':
        vk_id = request.POST.get('vk_id')
        password = request.POST.get('password')

        # 2. Проверка, существует ли пользователь с таким external_id
        if not User.objects.filter(external_id=vk_id).exists():
            return render(request, 'home.html', {
                'error': 'Сначала напишите что-нибудь боту Вконтакте',
                'modal_open': 'register'
            })

        user = User.objects.get(external_id=vk_id)
        user.password = make_password(password)
        user.save()

    return render(request, 'auth/register.html')

def dashboard_view(request):
    return render(request, 'dashboard.html')