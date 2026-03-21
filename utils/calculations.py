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
        'total_weight_100': round(sourdough100, 1),
        'starter_100': round(starter, 1),
        'water_100': round(water, 1),
        'flour_100': round(flour, 1),
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
        'total_weight_50': round(sourdough50, 1),
        'starter_50': round(starter, 1),
        'water_50': round(water, 1),
        'flour_50': round(flour, 1),
        'water_to_add': round(water_to_add, 1)  # кол-во воды, которое нужно добавить при замесе
    }


def get_multiplication_result(quantity_recipes, recipe_dict):
    for group in recipe_dict['groups']:
        for ingredient in group['ingredients']:
            quantity = ingredient['quantity']
            if quantity is not None:
                result_quantity = round(float(quantity) * int(quantity_recipes), 1)
                if result_quantity.is_integer():
                    ingredient['quantity'] = int(result_quantity)
                else:
                    ingredient['quantity'] = result_quantity
    return recipe_dict