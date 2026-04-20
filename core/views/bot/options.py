import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from utils.calculations import convert_50_to_100, convert_100_to_50, get_multiplication_result, hydro_calc

from logger import options_logger




@csrf_exempt
def starter_calc(request):
    """
    Рассчитывает закваску для перехода между влажностями 50% и 100%.

    Валидный JSON запроса (POST):
    {
        "direction": "50to100",
        "original_starter": 100,
        "original_water": 50,
        "original_flour": 50,
        "starter_part": 1,
        "water_part": 1,
        "flour_part": 1
    }

    Поля:
    - direction (str, обязательно): "50to100" или "100to50".
    - original_starter, original_water, original_flour (float): Исходные количества.
    - starter_part, water_part, flour_part (float): Пропорции для расчёта.

    Успешный ответ (200):
    {
        "starter": 150,
        "water": 75,
        "flour": 75,
        "water_to_remove": 25  // только для 50→100
        // или "water_to_add": 25  // только для 100→50
    }

    Ошибки:
    - 400: Invalid direction, Missing required field, Invalid JSON.
    - 405: Method not allowed.
    """
    if request.method != 'POST':
        options_logger.warning(f"Method {request.method} not allowed for starter_calc")
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        direction = data.get('direction')
        options_logger.info(f"Starter calculation: direction={direction}")

        if direction == '50to100':
            result = convert_50_to_100(
                starter_50=data['original_starter'],
                water_50=data['original_water'],
                flour_50=data['original_flour'],
                starter_part=data['starter_part'],
                water_part=data['water_part'],
                flour_part=data['flour_part']
            )
            options_logger.debug(f"50to100 result: {result}")

        elif direction == '100to50':
            result = convert_100_to_50(
                starter_100=data['original_starter'],
                water_100=data['original_water'],
                flour_100=data['original_flour'],
                starter_part=data['starter_part'],
                water_part=data['water_part'],
                flour_part=data['flour_part']
            )
            options_logger.debug(f"100to50 result: {result}")

        else:
            options_logger.warning(f"Invalid direction: {direction}")
            return JsonResponse({'error': 'Invalid direction'}, status=400)

        return JsonResponse(result, status=200)

    except KeyError as e:
        options_logger.error(f"Missing required field in starter_calc: {e}")
        return JsonResponse({'error': f'Missing required field: {e}'}, status=400)
    except json.JSONDecodeError:
        options_logger.warning("Invalid JSON in starter_calc request body")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        options_logger.exception(f"Unexpected error in starter_calc: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@csrf_exempt
def recipe_multiply(request):
    """
    Умножает все ингредиенты рецепта на заданный множитель.

    Валидный JSON запроса (POST):
    {
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
    }

    Поля:
    - multiplier (float, обязательно): Множитель (> 0).
    - recipe (dict, обязательно): Рецепт в стандартном формате.

    Успешный ответ (200):
    {
        "recipe": {
            "status": "ok",
            "data": {
                "title": "Хлеб простой x2",
                "groups": [...]
            }
        }
    }

    Ошибки:
    - 400: Invalid JSON, Missing required field.
    - 405: Method not allowed.
    """
    if request.method != 'POST':
        options_logger.warning(f"Method {request.method} not allowed for recipe_multiply")
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        multiplier = data.get('multiplier')
        options_logger.info(f"Recipe multiply: multiplier={multiplier}")

        result = get_multiplication_result(
            quantity_recipes=multiplier,
            recipe_dict=data['recipe']
        )
        options_logger.debug(f"Multiplication result title: {result.get('data', {}).get('title', 'Unknown')}")

    except json.JSONDecodeError:
        options_logger.warning("Invalid JSON in recipe_multiply request body")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except KeyError as e:
        options_logger.error(f"Missing required field in recipe_multiply: {e}")
        return JsonResponse({'error': f'Missing required field: {e}'}, status=400)
    except Exception as e:
        options_logger.exception(f"Unexpected error in recipe_multiply: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)

    return JsonResponse({'recipe': result}, status=200)


@csrf_exempt
def calculate_hydration(request):
    """
    Рассчитывает гидрацию рецепта (влажность теста).

    Валидный JSON запроса (POST):
    {
        "recipe": {
            "data": {
                "title": "Хлеб",
                "groups": [
                    {
                        "name": "Тесто",
                        "ingredients": [
                            {"name": "мука", "quantity": 500, "unit": "г"},
                            {"name": "вода", "quantity": 350, "unit": "г"}
                        ]
                    }
                ]
            }
        }
    }

    Поля:
    - recipe (dict, обязательно): Рецепт в стандартном формате.

    Успешный ответ (200):
    {
        "recipe": {
            "data": {
                "title": "Хлеб",
                "groups": [...],
                "dry_sum": 500,
                "wet_sum": 350,
                "hydration": 70.0
            }
        }
    }

    Ошибки:
    - 400: recipe is required.
    - 405: Method not allowed.
    - 500: Internal server error.
    """
    if request.method != 'POST':
        options_logger.warning(f"Method {request.method} not allowed for calculate_hydration")
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        recipe = data.get('recipe')
        if not recipe:
            options_logger.warning("calculate_hydration: recipe is required")
            return JsonResponse({'error': 'recipe is required'}, status=400)

        options_logger.info(f"Calculating hydration for recipe: {recipe.get('data', {}).get('title', 'Unknown')}")

        hydro, dry_sum, wet_sum = hydro_calc(recipe)
        recipe['data']['dry_sum'] = dry_sum
        recipe['data']['wet_sum'] = wet_sum
        recipe['data']['hydration'] = hydro

        options_logger.debug(f"Hydration result: dry_sum={dry_sum}, wet_sum={wet_sum}, hydration={hydro}")

        return JsonResponse({'recipe': recipe}, status=200)

    except json.JSONDecodeError:
        options_logger.warning("Invalid JSON in calculate_hydration request body")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        options_logger.exception(f"Unexpected error in calculate_hydration: {e}")
        return JsonResponse({'error': str(e)}, status=500)