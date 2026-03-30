import json

from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from core.models import User, Recipe
from core.serializers import RecipeSerializer


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
        external_id = data.get('user_id')
        parent_id = data.get('parent_id')
        print(parent_id)
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

    print(f'parents_list {parents_list}')

    try:
        user=User.objects.get(external_id=external_id)  # проверяем существует ли пользователь в базе
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

    try:
        recipe_title=data['recipe']['data']['title']
        recipe, created = Recipe.objects.get_or_create(
        title=recipe_title.upper(),
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



def get_user_recipes(request, external_id):
    #возвращает массив словарей с данными пользователя и рецептами
    #hydration для гидратации!
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
         user = User.objects.get(external_id=external_id)  # проверяем существует ли пользователь в базе
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

    recipes = Recipe.objects.filter(user=user).order_by('-created_at')
    paginator = Paginator(recipes, 4)
    page = request.GET.get('page', 1)
    recipes_page = paginator.get_page(page)

    serializer = RecipeSerializer(recipes_page, many=True)
    return JsonResponse({
        'recipes': serializer.data,
        'page': int(page),
        'has_next': recipes_page.has_next(),
        'has_prev': recipes_page.has_previous(),
        'total_pages': paginator.num_pages
    })

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