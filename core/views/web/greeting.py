from django.shortcuts import render, redirect

from core.models import User, Recipe
from django.contrib.auth.hashers import make_password, check_password


def _get_web_user(request):
    user_id = request.session.get('user_id')
    if user_id:
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            request.session.flush()
    return None


def home(request):
    return render(request, 'home.html', {'user_data': _get_web_user(request)})


def login_view(request):

    if request.method == 'POST':
        vk_id = request.POST.get('vk_id')
        password = request.POST.get('password')

        if not User.objects.filter(external_id=vk_id).exists():
            return render(request, 'home.html', {
                'error': 'Сначала напишите что-нибудь боту Вконтакте',
                'modal_open': 'login',
                'user_data': None,
            })

        user = User.objects.get(external_id=vk_id)
        if not user.password:
            return render(request, 'home.html', {
                'error': 'Сначала зарегистрируйтесь',
                'modal_open': 'register',
                'user_data': None,
            })
        if not check_password(password, user.password):
            return render(request, 'home.html', {
                'error': 'Пароль не подходит',
                'modal_open': 'login',
                'user_data': None,
            })

        request.session['user_id'] = user.id
        return redirect('dashboard')

    return render(request, 'auth/login.html')


def register_view(request):
    if _get_web_user(request):
        return redirect('dashboard')

    if request.method == 'POST':
        vk_id = request.POST.get('vk_id')
        password = request.POST.get('password')

        if not User.objects.filter(external_id=vk_id).exists():
            return render(request, 'home.html', {
                'error': 'Сначала напишите что-нибудь боту Вконтакте',
                'modal_open': 'register',
                'user_data': None,
            })

        user = User.objects.get(external_id=vk_id)
        user.password = make_password(password)
        user.save()

        request.session['user_id'] = user.id
        return redirect('dashboard')

    return render(request, 'auth/register.html')


def dashboard_view(request):
    user_data = _get_web_user(request)
    if not user_data:
        return redirect('home')

    recipes = Recipe.objects.filter(user=user_data).order_by('-created_at')
    return render(request, 'dashboard.html', {
        'user_data': user_data,
        'recipes': recipes,
        'active_tab': 'recipes',
    })


def logout_view(request):
    request.session.flush()
    return redirect('home')


def delete_recipe_web(request, recipe_id):
    if request.method != 'POST':
        return redirect('dashboard')

    user_data = _get_web_user(request)
    if not user_data:
        return redirect('home')

    for recipe in Recipe.objects.all():
        if recipe_id in recipe.parents:
            recipe.parents.remove(recipe_id)
            recipe.save()

    Recipe.objects.filter(id=recipe_id, user=user_data).delete()
    return redirect('dashboard')