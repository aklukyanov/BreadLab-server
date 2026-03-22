from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from core.models import User, Recipe
from core.serializers import UserSerializer, RecipeSerializer
from utils.calculations import convert_50_to_100, convert_100_to_50, get_multiplication_result


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
"parent_id":1,
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
        parent_id = data.get('parent_id')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    if parent_id:
        try:
            parent = Recipe.objects.get(id=parent_id)
            parents_list=parent.parents+[parent_id]
        except Recipe.DoesNotExist:
            return JsonResponse({'error': 'Parent recipe not found'}, status=404)
    else:
        parents_list=[]

    try:
        user=User.objects.get(id=user_id)  # проверяем существует ли пользователь в базе
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

    try:
        recipe_title=data['recipe']['data']['title']
        recipe, created = Recipe.objects.get_or_create(
        title=recipe_title,
        user=user,
        defaults={
        'recipe':data['recipe'],
        'hydration':data['recipe']['data']['hydration'],
        'parents':parents_list
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

    # удаляем id удаляемого рецепта из списков версий, где он есть
    #
    try:
    #      ВЕРСИЯ ДЛЯ POSTGRESQL
    #     linked_recipes=Recipe.objects.filter(parents__contains=[recipe_id])
    #     for linked_recipe in linked_recipes:
    #         linked_recipe.parents.remove(recipe_id)
    #         linked_recipe.save()
        #УНИВЕРСАЛЬНАЯ НО НЕ ТАКАЯ ПРОИЗВОДИТЕЛЬНАЯ ВЕРСИЯ
        for recipe in Recipe.objects.all():
            if recipe_id in recipe.parents:
                recipe.parents.remove(recipe_id)
                recipe.save()
    # находим и удаляем сам рецепт
        recipe_to_delete=Recipe.objects.get(id=recipe_id)
        recipe_to_delete.delete()
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

@csrf_exempt
def recipe_multiply(request):
    # валидный запрос
    '''{
        "multiplier": 2,
        "recipe": {
            "status": "ok",
            "data": {
                "title": "Хлеб простой",
                "groups": [
                    {
                        "name": "Тесто",
                        "ingredients": [
                            {"name": "мука пшеничная", "quantity": 500, "unit": "г"},
                            {"name": "вода", "quantity": 350, "unit": "мл"},
                            {"name": "соль", "quantity": 10, "unit": "г"},
                            {"name": "дрожжи", "quantity": 5, "unit": "г"}
                        ]
                    }
                ]
            }
        }
    }'''
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        result=get_multiplication_result(
            quantity_recipes=data['multiplier'],
            recipe_dict=data['recipe']['data'])

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except KeyError as e:
        return JsonResponse({'error': f'Missing required field:{e}'}, status=400)

    return JsonResponse({'recipe':result}, status=200)
@csrf_exempt
def update_recipe(request, recipe_id):
    if request.method != 'PATCH':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    try:
        recipe=Recipe.objects.get(id=recipe_id)
        recipe.recipe = data.get('recipe', recipe.recipe)
        recipe.save()
        serializer = RecipeSerializer(recipe)
        return JsonResponse(serializer.data, status=200)

    except Recipe.DoesNotExist:
        return JsonResponse({'error': 'Recipe not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
@csrf_exempt
def get_uniq_recipe(request, recipe_id):
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        recipe=Recipe.objects.get(id=recipe_id)
        serializer = RecipeSerializer(recipe)
        return JsonResponse(serializer.data, status=200)

    except Recipe.DoesNotExist:
        return JsonResponse({'error': 'Recipe not found'}, status=404)












