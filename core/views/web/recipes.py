import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from core.models import Recipe
from core.serializers import RecipeSerializer
from core.views.web.greeting import _get_web_user


@csrf_exempt
def create_recipe_web(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    user_data = _get_web_user(request)
    if not user_data:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    recipe_data = data.get('recipe')
    parent_id = data.get('parent_id')
    if not recipe_data or not recipe_data.get('data', {}).get('title', '').strip():
        return JsonResponse({'error': 'Missing required fields'}, status=400)

    title = recipe_data['data']['title'].upper()

    parents_list = []
    if parent_id:
        try:
            parent = Recipe.objects.get(id=parent_id)
            parents_list = parent.parents + [parent_id]
        except Recipe.DoesNotExist:
            pass

    recipe = Recipe.objects.create(
        user=user_data,
        title=title,
        recipe=recipe_data,
        parents=parents_list,
    )

    serializer = RecipeSerializer(recipe)
    return JsonResponse(serializer.data, status=201)
