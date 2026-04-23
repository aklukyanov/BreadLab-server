def convert_50_to_100(starter_50: float, water_50: float, flour_50: float, starter_part: int, water_part: int,
                      flour_part: int) -> dict:
    total_weight50 = starter_50 + water_50 + flour_50
    sourdough100 = (total_weight50 / 3) * 4  # кол-во опары 100%, которое нужно взять для этой рецептуры
    water_to_remove = total_weight50 / 3  # кол-во воды, которое нужно убрать из рецептуры для сохранения гидратации

    # расчет частей опары 100%
    sum_of_parts = starter_part + water_part + flour_part  # определяем количество частей
    part = sourdough100 / sum_of_parts  # считаем одну часть
    starter = part * starter_part
    water = part * water_part
    flour = part * flour_part

    return {
        'total_weight': round(sourdough100, 1),
        'starter': round(starter, 1),
        'water': round(water, 1),
        'flour': round(flour, 1),
        'water_to_remove': round(water_to_remove, 1)  # кол-во воды, которое нужно убрать при замесе
    }

# в рецепте закваска 100%, а у нас закваска 50%
def convert_100_to_50(starter_100: float, water_100: float, flour_100: float, starter_part: int, water_part: int,
                      flour_part: int) -> dict:
    total_weight100 = starter_100 + water_100 + flour_100
    sourdough50 = (total_weight100 / 4) * 3  # кол-во опары 50%, которое нужно взять для этой рецептуры
    water_to_add = total_weight100 / 4  # кол-во воды, которое нужно добавить в рецептуру для сохранения гидратации

    # расчет частей опары 100%
    sum_of_parts = starter_part + water_part + flour_part  # определяем количество частей
    part = sourdough50 / sum_of_parts  # считаем одну часть
    starter = part * starter_part
    water = part * water_part
    flour = part * flour_part

    return {
        'total_weight': round(sourdough50, 1),
        'starter': round(starter, 1),
        'water': round(water, 1),
        'flour': round(flour, 1),
        'water_to_add': round(water_to_add, 1)  # кол-во воды, которое нужно добавить при замесе
    }


def get_multiplication_result(quantity_recipes, recipe_dict):
    for group in recipe_dict['groups']:
        for ingredient in group['ingredients']:
            amount = ingredient.get('amount', ingredient.get('quantity'))
            if amount is not None:
                result = round(float(amount) * float(quantity_recipes), 1)
                ingredient['amount'] = int(result) if result.is_integer() else result
    return recipe_dict


def hydro_calc(recipe):

    dry_sum = 0
    wet_sum = 0
    for group in recipe['data']['groups']:
        group_name = group['name'].lower()

        if group_name == 'сухие':
            for ingredient in group['ingredients']:
                quantity = int(ingredient['quantity'])
                dry_sum += quantity
        elif group_name == 'жидкие':
            for ingredient in group['ingredients']:
                quantity = int(ingredient['quantity'])
                wet_sum += quantity

    hydro = round((wet_sum / dry_sum) * 100, 1)
    return hydro, dry_sum, wet_sum

