import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from utils.calculations import convert_50_to_100, convert_100_to_50, get_multiplication_result, hydro_calc

@csrf_exempt
def starter_calc(request):
    """запрос {
        "direction": "50to100",
        "original_starter": 100,
        "original_water": 50,
        "original_flour": 50,
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
            starter_50=data['original_starter'],
            water_50=data['original_water'],
            flour_50=data['original_flour'],
            starter_part=data['starter_part'],
            water_part=data['water_part'],
            flour_part=data['flour_part'])

        elif data['direction']=='100to50':
            result=convert_100_to_50(
            starter_100=data['original_starter'],
            water_100=data['original_water'],
            flour_100=data['original_flour'],
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
            recipe_dict=data['recipe'])
        

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except KeyError as e:
        return JsonResponse({'error': f'Missing required field:{e}'}, status=400)

    return JsonResponse({'recipe':result}, status=200)


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