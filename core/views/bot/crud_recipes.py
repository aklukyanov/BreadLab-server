import json
from django.core.paginator import Paginator
from django.db.models import F
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from core.models import User, Recipe
from core.serializers import RecipeSerializer
from logger import crud_recipes_logger




@csrf_exempt
def create_recipe(request):
    """
    Создаёт новый рецепт или возвращает существующий по названию у данного пользователя.

    Валидный JSON запроса (POST):
    {
        "user_id": 42,
        "parent_id": 1,
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
    }

    Поля:
    - user_id (str, обязательно): external_id пользователя.
    - parent_id (int, опционально): ID родительского рецепта (для версионирования).
    - recipe.data (dict, обязательно): Данные рецепта (title, groups, hydration и т.д.).

    Успешный ответ (201 - создан, 200 - уже существует):
    {
        "id": 1,
        "user": {...},
        "parents": [],
        "recipe": {...},
        "created_at": "...",
        "updated_at": "..."
    }

    Ошибки:
    - 400: Invalid JSON или Missing required fields.
    - 404: Parent recipe not found или User not found.
    - 405: Method not allowed.
    """
    if request.method != 'POST':
        crud_recipes_logger.warning(f"Method {request.method} not allowed for create_recipe")
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        external_id = data.get('user_id')
        parent_id = data.get('parent_id')
        hydration = data.get('hydration')
        crud_recipes_logger.debug(f"Creating recipe: user_id={external_id}, parent_id={parent_id}")
    except json.JSONDecodeError:
        crud_recipes_logger.warning("Invalid JSON in create_recipe request body")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    if parent_id:
        try:
            parent = Recipe.objects.get(id=parent_id)
            parents_list = parent.parents + [parent_id]
            crud_recipes_logger.debug(f"Parent recipe found: id={parent_id}, parents_list={parents_list}")
        except Recipe.DoesNotExist:
            crud_recipes_logger.warning(f"Parent recipe not found: id={parent_id}")
            return JsonResponse({'error': 'Parent recipe not found'}, status=404)
    else:
        parents_list = []
        crud_recipes_logger.debug("No parent_id provided, parents_list empty")

    try:
        user = User.objects.get(external_id=external_id)
    except User.DoesNotExist:
        crud_recipes_logger.warning(f"User not found: external_id={external_id}")
        return JsonResponse({'error': 'User not found'}, status=404)

    try:
        recipe_title = data['recipe']['data']['title']
        recipe, created = Recipe.objects.get_or_create(
            title=recipe_title.upper(),
            user=user,
            defaults={
                'recipe': data['recipe'],
                'hydration': hydration,
                'parents': parents_list
            }
        )
        if created:
            crud_recipes_logger.info(f"Recipe created: id={recipe.id}, title='{recipe_title}', user_id={external_id}")
        else:
            crud_recipes_logger.info(f"Recipe already exists: id={recipe.id}, title='{recipe_title}', user_id={external_id}")
    except KeyError as e:
        crud_recipes_logger.error(f"Missing required field in recipe data: {e}")
        return JsonResponse({'error': 'Missing required fields'}, status=400)

    serializer = RecipeSerializer(recipe)
    return JsonResponse(serializer.data, status=201 if created else 200)


def get_user_recipes(request, external_id):
    """
    Возвращает список рецептов пользователя с пагинацией.

    URL: GET /api/users/<external_id>/recipes/?page=1

    Параметры query string:
    - page (int, опционально): Номер страницы. По умолчанию 1.

    Успешный ответ (200):
    {
        "recipes": [...],
        "page": 1,
        "has_next": true,
        "has_prev": false,
        "total_pages": 5
    }

    Ошибки:
    - 404: User not found.
    - 405: Method not allowed.
    """
    if request.method != 'GET':
        crud_recipes_logger.warning(f"Method {request.method} not allowed for get_user_recipes")
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        user = User.objects.get(external_id=external_id)
    except User.DoesNotExist:
        crud_recipes_logger.warning(f"User not found: external_id={external_id}")
        return JsonResponse({'error': 'User not found'}, status=404)

    recipes = Recipe.objects.filter(user=user).order_by('-created_at')
    paginator = Paginator(recipes, 4)
    page = request.GET.get('page', 1)
    recipes_page = paginator.get_page(page)

    crud_recipes_logger.debug(f"Fetching recipes for user_id={external_id}, page={page}, total={paginator.count}")

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
    """
    Удаляет рецепт по ID. Также удаляет его ID из списков parents всех связанных рецептов.

    URL: DELETE /api/recipes/<recipe_id>/delete/

    Успешный ответ (200):
    {
        "message": "Recipe deleted"
    }

    Ошибки:
    - 404: Recipe not found.
    - 405: Method not allowed.
    """
    if request.method != 'DELETE':
        crud_recipes_logger.warning(f"Method {request.method} not allowed for delete_recipe")
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    crud_recipes_logger.info(f"Attempting to delete recipe: id={recipe_id}")

    try:
        # Удаляем id удаляемого рецепта из списков версий, где он есть
        for recipe in Recipe.objects.all():
            if recipe_id in recipe.parents:
                recipe.parents.remove(recipe_id)
                recipe.save()
                crud_recipes_logger.debug(f"Removed deleted recipe id={recipe_id} from parents of recipe id={recipe.id}")

        recipe_to_delete = Recipe.objects.get(id=recipe_id)
        title = recipe_to_delete.recipe.get('data', {}).get('title', 'Unknown')
        recipe_to_delete.delete()
        crud_recipes_logger.info(f"Recipe deleted: id={recipe_id}, title='{title}'")
        return JsonResponse({'message': 'Recipe deleted'}, status=200)

    except Recipe.DoesNotExist:
        crud_recipes_logger.warning(f"Recipe not found for deletion: id={recipe_id}")
        return JsonResponse({'error': 'Recipe not found'}, status=404)


@csrf_exempt
def update_recipe(request, recipe_id):
    """
    Обновляет существующий рецепт (PATCH).

    Валидный JSON запроса (PATCH):
    {
        "recipe": {
            "status": "ok",
            "data": {
                "title": "Хлеб с отрубями",
                "groups": [...],
                "dry_sum": 610,
                "wet_sum": 440,
                "hydration": 72.1
            }
        }
    }

    URL: PATCH /api/recipes/<recipe_id>/update/

    Успешный ответ (200):
    {
        "id": 1,
        "user": {...},
        "parents": [...],
        "recipe": {...},
        "created_at": "...",
        "updated_at": "..."
    }

    Ошибки:
    - 400: Invalid JSON или Recipe with this title already exists.
    - 404: Recipe not found.
    - 405: Method not allowed.
    """
    if request.method != 'PATCH':
        crud_recipes_logger.warning(f"Method {request.method} not allowed for update_recipe")
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        crud_recipes_logger.warning("Invalid JSON in update_recipe request body")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    try:
        recipe = Recipe.objects.get(id=recipe_id)
        recipe.recipe = data.get('recipe', recipe.recipe)
        new_title = data['recipe']['data']['title']

        if Recipe.objects.filter(user=recipe.user, title=new_title).exclude(id=recipe.id).exists():
            crud_recipes_logger.warning(f"Update failed: title '{new_title}' already exists for user")
            return JsonResponse({'error': 'Recipe with this title already exists'}, status=400)

        recipe.title = new_title.upper()
        recipe.save()
        crud_recipes_logger.info(f"Recipe updated: id={recipe_id}, new_title='{new_title}'")
        serializer = RecipeSerializer(recipe)
        return JsonResponse(serializer.data, status=200)

    except Recipe.DoesNotExist:
        crud_recipes_logger.warning(f"Recipe not found for update: id={recipe_id}")
        return JsonResponse({'error': 'Recipe not found'}, status=404)
    except KeyError as e:
        crud_recipes_logger.error(f"Missing required field in update data: {e}")
        return JsonResponse({'error': 'Missing required fields'}, status=400)


@csrf_exempt
def get_uniq_recipe(request, recipe_id):
    """
    Возвращает один рецепт по ID.

    URL: GET /api/recipes/<recipe_id>/

    Успешный ответ (200):
    {
        "id": 1,
        "user": {...},
        "parents": [...],
        "recipe": {...},
        "created_at": "...",
        "updated_at": "..."
    }

    Ошибки:
    - 404: Recipe not found.
    - 405: Method not allowed.
    """
    if request.method != 'GET':
        crud_recipes_logger.warning(f"Method {request.method} not allowed for get_uniq_recipe")
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        recipe = Recipe.objects.get(id=recipe_id)
        crud_recipes_logger.debug(f"Fetching recipe: id={recipe_id}")
        serializer = RecipeSerializer(recipe)
        data = serializer.data
        if data['parents']:
            parent_id = data['parents'][-1]
            try:
                parent = Recipe.objects.get(id=parent_id)
                data['parent_title'] = parent.title
            except Recipe.DoesNotExist:
                pass
        return JsonResponse(data, status=200)
    except Recipe.DoesNotExist:
        crud_recipes_logger.warning(f"Recipe not found: id={recipe_id}")
        return JsonResponse({'error': 'Recipe not found'}, status=404)


@csrf_exempt
def get_recipe_children(request, recipe_id):
    """
    Возвращает все версии (дочерние рецепты) для заданного рецепта.

    URL: GET /api/recipes/<recipe_id>/children/

    Успешный ответ (200):
    [
        {...},  // Рецепт-версия 1
        {...}   // Рецепт-версия 2
    ]

    Ошибки:
    - 404: Recipe not found.
    - 405: Method not allowed.
    """
    if request.method != 'GET':
        crud_recipes_logger.warning(f"Method {request.method} not allowed for get_recipe_children")
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        Recipe.objects.get(id=recipe_id)
        versions = [recipe for recipe in Recipe.objects.all() if recipe_id in recipe.parents]
        crud_recipes_logger.debug(f"Fetching children for recipe id={recipe_id}, found {len(versions)} versions")
        serializer = RecipeSerializer(versions, many=True)
        return JsonResponse(serializer.data, safe=False, status=200)
    except Recipe.DoesNotExist:
        crud_recipes_logger.warning(f"Recipe not found for children: id={recipe_id}")
        return JsonResponse({'error': 'Recipe not found'}, status=404)


@csrf_exempt
def get_recipe_parents(request, recipe_id):
    """
    Возвращает все родительские рецепты для заданного рецепта.

    URL: GET /api/recipes/<recipe_id>/parents/

    Успешный ответ (200):
    [
        {...},  // Родительский рецепт 1
        {...}   // Родительский рецепт 2
    ]

    Ошибки:
    - 404: Recipe not found.
    - 405: Method not allowed.
    """
    if request.method != 'GET':
        crud_recipes_logger.warning(f"Method {request.method} not allowed for get_recipe_parents")
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        recipe = Recipe.objects.get(id=recipe_id)
        parent_objects = []
        for pid in recipe.parents:
            try:
                parent_objects.append(Recipe.objects.get(id=pid))
            except Recipe.DoesNotExist:
                continue
        crud_recipes_logger.debug(f"Fetching parents for recipe id={recipe_id}, found {len(parent_objects)} parents")
        serializer = RecipeSerializer(parent_objects, many=True)
        return JsonResponse(serializer.data, safe=False, status=200)
    except Recipe.DoesNotExist:
        crud_recipes_logger.warning(f"Recipe not found for parents: id={recipe_id}")
        return JsonResponse({'error': 'Recipe not found'}, status=404)


@csrf_exempt
def check_recipe_exists(request):
    """
    Проверяет, существует ли у пользователя рецепт с заданным названием.

    URL: GET /api/recipe_check_exists/?user_id=<external_id>&title=<название>

    Параметры query string:
    - user_id (str, обязательно): external_id пользователя.
    - title (str, обязательно): Название рецепта (регистронезависимо).

    Успешный ответ (200):
    {
        "exists": true
    }

    Ошибки:
    - 405: Method not allowed.
    """
    if request.method != 'GET':
        crud_recipes_logger.warning(f"Method {request.method} not allowed for check_recipe_exists")
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    user_id = request.GET.get('user_id')
    title = request.GET.get('title', '').upper()
    exists = Recipe.objects.filter(user__external_id=user_id, title=title).exists()
    crud_recipes_logger.debug(f"Check recipe exists: user_id={user_id}, title='{title}', exists={exists}")
    return JsonResponse({'exists': exists})


@csrf_exempt
def get_recipe_tree(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    query_recipe_id = request.GET.get('recipe_id')
    if not query_recipe_id:
        return JsonResponse({'error': 'recipe_id required'}, status=400)

    try:
        recipe = Recipe.objects.get(id=query_recipe_id)
    except Recipe.DoesNotExist:
        return JsonResponse({'error': 'Recipe not found'}, status=404)

    # Определяем корень дерева
    root_id = recipe.parents[0] if recipe.parents else recipe.id

    # Собираем все рецепты дерева
    all_recipes = Recipe.objects.all()
    tree_recipes = []
    for r in all_recipes:
        if r.id == root_id:
            tree_recipes.append(r)
        elif r.parents and len(r.parents) > 0 and r.parents[0] == root_id:
            tree_recipes.append(r)

    serializer = RecipeSerializer(tree_recipes, many=True)
    return JsonResponse({
        'root_id': root_id,
        'current_id': int(query_recipe_id),
        'tree': serializer.data,
    }, status=200)








