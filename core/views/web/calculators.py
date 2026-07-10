from django.shortcuts import render, redirect
from core.models import Recipe
from utils.calculations import convert_50_to_100, convert_100_to_50, get_multiplication_result
from core.views.web.greeting import _get_web_user


def starter_view(request):
    user_data = _get_web_user(request)
    if not user_data:
        return redirect('home')

    result = None
    if request.method == 'POST':
        direction = request.POST.get('direction')
        starter = float(request.POST.get('starter', 0))
        water = float(request.POST.get('water', 0))
        flour = float(request.POST.get('flour', 0))
        starter_part = int(request.POST.get('starter_part', 1))
        water_part = int(request.POST.get('water_part', 1))
        flour_part = int(request.POST.get('flour_part', 1))

        if direction == '50to100':
            result = convert_50_to_100(starter, water, flour, starter_part, water_part, flour_part)
            result['direction_label'] = '50% → 100%'
        else:
            result = convert_100_to_50(starter, water, flour, starter_part, water_part, flour_part)
            result['direction_label'] = '100% → 50%'

    return render(request, 'calculators/starter.html', {
        'user_data': user_data,
        'result': result,
        'active_tab': 'starter',
    })


def multiply_view(request):
    user_data = _get_web_user(request)
    if not user_data:
        return redirect('home')

    recipes = Recipe.objects.filter(user=user_data).order_by('-created_at')
    result = None

    if request.method == 'POST':
        recipe_id = request.POST.get('recipe_id')
        multiplier = float(request.POST.get('multiplier', 1))

        recipe = Recipe.objects.get(id=recipe_id, user=user_data)
        recipe_data = recipe.recipe.get('data', recipe.recipe)
        multiplied = get_multiplication_result(multiplier, recipe_data)

        result = {
            'recipe': recipe,
            'multiplied_data': multiplied,
            'multiplier': multiplier,
        }

    return render(request, 'calculators/multiply.html', {
        'user_data': user_data,
        'recipes': recipes,
        'result': result,
        'active_tab': 'multiply',
    })
