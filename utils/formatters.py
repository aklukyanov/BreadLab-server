

def convert_dict_to_pretty_print(dict_to_convert,multiplier=None):
    #Преобразуем ответ модели в вывод для пользователя. 
        recipe=dict_to_convert
        answer_for_user=[]

        if recipe['title']==None:
            title='🍞 БЕЗ НАЗВАНИЯ'
        else:
            title=f"🍞 {recipe['title']}"
        
        if multiplier:  # добавится только если множитель передан
            title += f" ×{multiplier}"
        
        answer_for_user.append(title+'\n')

        for group in recipe['groups']:
            answer_for_user.append(f"{group['name']}:")

            for ingredient in group['ingredients']:
                name=ingredient['name']
                quantity = ingredient['quantity']
                unit = ingredient['unit']

                if quantity==None:
                    answer_for_user.append(f"• {name} - ?")
                else:
                    formatted_quantity=format_quantity_and_unit(quantity,unit)
                    answer_for_user.append(f"• {name} - {formatted_quantity}")
            
            answer_for_user.append("")  # пустая строка после каждой группы
        if 'hydro' in recipe:
            answer_for_user.append(f"💧 Гидратация: {recipe['hydro']}%")
            
        return "\n".join(answer_for_user)

def format_quantity_and_unit(quantity, unit):
    #функция форматирует количество единиц продукта на выходе
    # Если граммы и больше 1000
    if unit == 'г.' and quantity >= 1000:
        kg = quantity / 1000
        if kg.is_integer():
            return f"{int(kg)} кг."
        else:
            return f"{kg} кг."
    # Если килограммы и меньше 1
    elif unit == 'кг.' and quantity < 1:
        g = quantity * 1000
        if g.is_integer():
            return f"{int(g)} г."
        else:
            return f"{g} г."
      
    elif unit == 'пакетик':
        if quantity==1:
            return f"{quantity} пакетик"
        if 1 < quantity < 5:
            return f"{quantity} пакетика"
        if quantity >=5:
            return f"{quantity} пакетиков"
    
    elif unit == 'стакан':
        if quantity==1:
            return f"{quantity} стакан"
        if 1 < quantity < 5:
            return f"{quantity} стакана"
        if quantity >=5:
            return f"{quantity} стаканов"
    
    # Если миллилитры и больше 1000
    elif unit == 'мл.' and quantity >= 1000:
        l = quantity / 1000
        if l.is_integer():
            return f"{int(l)} л."
        else:
            return f"{l} л."
    
    # Если литры и меньше 1
    elif unit == 'л.' and quantity < 1:
        ml = quantity * 1000
        if ml.is_integer():
            return f"{int(ml)} мл."
        else:
            return f"{ml} мл."
    else:
        return f"{quantity} {unit}"