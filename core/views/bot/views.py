from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from core.models import User, Recipe
from core.serializers import UserSerializer, RecipeSerializer
from utils.calculations import convert_50_to_100, convert_100_to_50


@csrf_exempt
def create_user(request):
    """
    {
  "external_id": "12345",
  "channel": "vk",
  "username": "alex_baker",
  "first_name": "Алексей",
  "last_name": "Пекарев"
}"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    data = json.loads(request.body)

    user, created = User.objects.get_or_create(
        external_id=data['external_id'],
        channel=data.get('channel', 'vk'),
        defaults={
            'first_name': data.get('first_name'),
            'last_name': data.get('last_name'),
            'username': data.get('username'),
            'gender': data.get('gender'),
        }
    )

    serializer = UserSerializer(user)
    return JsonResponse(serializer.data, status=201 if created else 200)


@csrf_exempt
def create_recipe(request):
    "валидный входящий json"
    '''{
"user_id": 42,
"recipe": {
    "status": "ok",
    "data": {
      "title": "РЖАНОЙ МУЛЬТИЗЕРНОВОЙ ХЛЕБ",
      "groups": [...],
      "dry_sum": 210,
      "wet_sum": 130,
      "hydration": 61.9
    }
  }
}'''
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

#извлекаем из входящего json данные
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    try:
        user=User.objects.get(id=user_id)  # проверяем существует ли пользователь в базе
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    try:
        recipe_title=data['recipe']['data']['title']

        recipe, created = Recipe.objects.get_or_create(
        name=recipe_title,
        user=user,
        defaults={
        'recipe':data['recipe'],
        'hydration':data['recipe']['data']['hydration']
        }
    )
    except KeyError:
        return JsonResponse({'error': 'Missing required fields'}, status=400)

    serializer = RecipeSerializer(recipe)

    return JsonResponse(serializer.data, status=201 if created else 200)



def get_user_recipes(request, user_id):
    #возвращает массив словарей с данными пользователя и рецептами
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        user=User.objects.get(id=user_id)  # проверяем существует ли пользователь в базе
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

    recipes = Recipe.objects.filter(user_id=user_id).order_by('-created_at')
    serializer = RecipeSerializer(recipes, many=True)
    return JsonResponse(serializer.data, safe=False)

@csrf_exempt
def delete_recipe(request, recipe_id):

    if request.method != 'DELETE':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        recipe=Recipe.objects.get(id=recipe_id)
        recipe.delete()
    except Recipe.DoesNotExist:
        return JsonResponse({'error': 'Recipe not found'}, status=404)

    return JsonResponse({'message': 'Recipe deleted'}, status=200)

@csrf_exempt
def delete_user(request, user_id):
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        user=User.objects.get(id=user_id)
        user.delete()
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

    return JsonResponse({'message': 'User deleted'}, status=200)


@csrf_exempt
def starter_calc(request):
    """запрос {
        "direction": "50to100",
        "starter_50": 100,
        "water_50": 50,
        "flour_50": 50,
        "starter_part": 1,
        "water_part": 1,
        "flour_part": 1
    }"""

    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data=json.loads(request.body)
        if data['direction']=='50to100':
            result=convert_50_to_100(
            starter_50=data['starter_50'],
            water_50=data['water_50'],
            flour_50=data['flour_50'],
            starter_part=data['starter_part'],
            water_part=data['water_part'],
            flour_part=data['flour_part'])

        elif data['direction']=='100to50':
            result=convert_100_to_50(
            starter_100=data['starter_100'],
            water_100=data['water_100'],
            flour_100=data['flour_100'],
            starter_part=data['starter_part'],
            water_part=data['water_part'],
            flour_part=data['flour_part'])
        else:
            return JsonResponse({'error': 'Invalid direction'}, status=400)

        return JsonResponse(result, status=200)
    except KeyError as e:
        return JsonResponse({'error': f'Missing required field:{e}'}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)














