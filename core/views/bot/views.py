import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import tempfile
import os

from core.models import User, Recipe
from core.serializers import UserSerializer, RecipeSerializer
from utils.calculations import convert_50_to_100, convert_100_to_50, get_multiplication_result, hydro_calc
from utils.client import cloud_client
from utils.prompts import photo_recognize_prompt, recipe_hydro_analyze_prompt, recipe_edit_prompt


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
    # валидный входящий json
#     {
# "user_id": 42,
# "parent_id":1,
# "recipe": {
#     "status": "ok",
#     "data": {
#       "title": "РЖАНОЙ МУЛЬТИЗЕРНОВОЙ ХЛЕБ",
#       "groups": [...],
#       "dry_sum": 210,
#       "wet_sum": 130,
#       "hydration": 61.9
#     }
#   }
# }
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
    # {
    #     "multiplier": 2,
    #     "recipe": {
    #         "status": "ok",
    #         "data": {
    #             "title": "Хлеб простой",
    #             "groups": [
    #                 {
    #                     "name": "Тесто",
    #                     "ingredients": [
    #                         {"name": "мука пшеничная", "quantity": 500, "unit": "г"},
    #                         {"name": "вода", "quantity": 350, "unit": "мл"},
    #                         {"name": "соль", "quantity": 10, "unit": "г"},
    #                         {"name": "дрожжи", "quantity": 5, "unit": "г"}
    #                     ]
    #                 }
    #             ]
    #         }
    #     }
    # }
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
    #    {
    #     "recipe": {
    #         "status": "ok",
    #         "data": {
    #             "title": "Хлеб с отрубями",
    #             "groups": [
    #                 {
    #                     "name": "Тесто",
    #                     "ingredients": [
    #                         {"name": "мука пшеничная", "quantity": 550, "unit": "г"},
    #                         {"name": "отруби", "quantity": 60, "unit": "г"},
    #                         {"name": "вода", "quantity": 440, "unit": "мл"},
    #                         {"name": "соль", "quantity": 10, "unit": "г"},
    #                         {"name": "дрожжи", "quantity": 5, "unit": "г"}
    #                     ]
    #                 }
    #             ],
    #             "dry_sum": 610,
    #             "wet_sum": 440,
    #             "hydration": 72.1
    #         }
    #     }
    # }
    if request.method != 'PATCH':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    try:
        recipe=Recipe.objects.get(id=recipe_id)
        recipe.recipe = data.get('recipe', recipe.recipe)
        new_title= data['recipe']['data']['title']

        if Recipe.objects.filter(user=recipe.user, title=new_title).exclude(id=recipe.id).exists():
            return JsonResponse({'error': 'Recipe with this title already exists'}, status=400)
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

@csrf_exempt
def get_recipe_children(request, recipe_id):
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:
        Recipe.objects.get(id=recipe_id)

        # ВЕРСИЯ ДЛЯ POSTGRESQL
        # versions=Recipe.objects.filter(parents__contains=recipe_id)
        versions=[recipe for recipe in Recipe.objects.all() if recipe_id in recipe.parents]
    except Recipe.DoesNotExist:
        return JsonResponse({'error': 'Recipe not found'}, status=404)

    serializer = RecipeSerializer(versions, many=True)
    return JsonResponse(serializer.data, safe=False, status=200)


@csrf_exempt
def get_recipe_parents(request, recipe_id):
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:
        recipe = Recipe.objects.get(id=recipe_id)
    except Recipe.DoesNotExist:
        return JsonResponse({'error': 'Recipe not found'}, status=404)

    parents = Recipe.objects.filter(id__in=recipe.parents)
    serializer = RecipeSerializer(parents, many=True)
    return JsonResponse(serializer.data, safe=False, status=200)


@csrf_exempt
def recognize_photo(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    photo=request.FILES.get('photo')

    if not photo:
        return JsonResponse({'error': 'Photo is required'}, status=400)

    try:
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            tmp.write(photo.read())
            tmp_path = tmp.name


        response = cloud_client.chat(
            model='qwen3.5:397b-cloud',  # облачная мультимодальная модель
            messages=[{
                'role': 'user',
                'content': photo_recognize_prompt,
                'images': [tmp_path]  # ПЕРЕДАЁМ ФОТО ЗДЕСЬ
            }],
            options={
                'temperature': 0.1,
                'num_predict': 1024
            }, think=False
        )


        model_answer_dict = json.loads(response['message']['content'])
        return JsonResponse(model_answer_dict, safe=False)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON from LLM'}, status=500)
    except requests.exceptions.ConnectionError:
        return JsonResponse({'error': 'LLM service unavailable'}, status=503)
    except requests.exceptions.Timeout:
        return JsonResponse({'error': 'LLM timeout'}, status=504)
    except Exception as e:
        return JsonResponse({'error': f'Internal server error: {e}'}, status=500)

    finally:
        if tmp_path and os.path.exists(tmp_path):
             os.unlink(tmp_path)

@csrf_exempt
def recipe_edit(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        recipe = data.get('recipe')
        instruction = data.get('instruction')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    if not recipe or not instruction:
        return JsonResponse({'error': 'recipe and instruction are required'}, status=400)
    try:
        response = cloud_client.chat(
        model='qwen3.5:397b-cloud',  # облачная мультимодальная модель
        messages=[{
            'role': 'user',
            'content': f"{recipe_edit_prompt}\nрецепт - {recipe}\nинструкция - {instruction}"
        }],
        options={
            'temperature': 0.1,
            'num_predict': 1024
        }, think=False
    )

        model_answer_dict=json.loads(response['message']['content'])
        return JsonResponse(model_answer_dict, safe=False)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON from LLM'}, status=500)
    except requests.exceptions.ConnectionError:
        return JsonResponse({'error': 'LLM service unavailable'}, status=503)
    except requests.exceptions.Timeout:
        return JsonResponse({'error': 'LLM timeout'}, status=504)
    except Exception as e:
        return JsonResponse({'error': f'Internal server error: {e}'}, status=500)

@csrf_exempt
def recipe_hydro_analyze(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:
        data = json.loads(request.body)
        recipe = data.get('recipe')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    if not recipe:
        return JsonResponse({'error': 'recipe is required'}, status=400)
    try:
        response = cloud_client.chat(
        model='qwen3.5:397b-cloud',  # облачная мультимодальная модель
        messages=[{
            'role': 'user',
            'content': f'{recipe_hydro_analyze_prompt}.\n Исходный рецепт:\n{recipe}'
        }],
        options={
            'temperature': 0.1,
            'num_predict': 1024
        }, think=False
    )

        model_answer_dict=json.loads(response['message']['content'])
        return JsonResponse(model_answer_dict, safe=False)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON from LLM'}, status=500)
    except requests.exceptions.ConnectionError:
        return JsonResponse({'error': 'LLM service unavailable'}, status=503)
    except requests.exceptions.Timeout:
        return JsonResponse({'error': 'LLM timeout'}, status=504)
    except Exception as e:
        return JsonResponse({'error': f'Internal server error:{e}'}, status=500)

@csrf_exempt
def calculate_hydration(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:
        data = json.loads(request.body)
        recipe = data.get('recipe')
        if not recipe:
            return JsonResponse({'error': 'recipe is required'}, status=400)

        hydro, dry_sum, wet_sum = hydro_calc(recipe)
        recipe['data']['dry_sum'] = dry_sum
        recipe['data']['wet_sum'] = wet_sum
        recipe['data']['hydration'] = hydro

        return JsonResponse({'recipe': recipe}, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



