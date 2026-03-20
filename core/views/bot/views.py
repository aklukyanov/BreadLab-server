from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from core.models import User, Recipe
from core.serializers import UserSerializer, RecipeSerializer


# Create your views here.
@csrf_exempt
def create_user(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    data = json.loads(request.body)
    serializer = UserSerializer(data=data)

    if serializer.is_valid():
        user = serializer.save()
        return JsonResponse(serializer.data, status=201)

    return JsonResponse(serializer.errors, status=400)

@csrf_exempt
def create_recipe(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    data = json.loads(request.body)
    serializer = RecipeSerializer(data=data)
    if serializer.is_valid():
        recipe = serializer.save()
        return JsonResponse(serializer.data, status=201)

    return JsonResponse(serializer.errors, status=400)

def get_user_recipes(request, user_id):
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    #идем в БД за рецептами
    recipes = Recipe.objects.filter(user_id=user_id).order_by('-created_at')
    serializer = RecipeSerializer(recipes, many=True)
    return JsonResponse(serializer.data, safe=False, status=200)


