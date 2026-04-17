import requests
import json
import tempfile
import os
import base64
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from utils.client import cloud_client
from utils.prompts import photo_recognize_prompt, recipe_hydro_analyze_prompt, recipe_edit_prompt, \
    recognize_text_recipe_prompt


@csrf_exempt
def recognize_text_recipe(request):
    """Обработчик текстового рецепта"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        recipe_text = data.get('recipe')

        if not recipe_text or not recipe_text.strip():
            return JsonResponse({'error': 'Recipe text is required'}, status=400)

        # ФОРМИРУЕМ ПРАВИЛЬНЫЙ ЗАПРОС - промпт + текст рецепта
        full_prompt = f"{recognize_text_recipe_prompt}\n\nТЕКСТ РЕЦЕПТА:\n{recipe_text}"

        response = cloud_client.chat(
            model='qwen3.5:397b-cloud',
            messages=[{
                'role': 'user',
                'content': full_prompt,  # переменная с промптом, определенная снаружи
            }],
            options={
                'temperature': 0.1,
                'num_predict': 1024
            },
            think=False,
            format='json'
        )

        # Извлекаем и парсим JSON
        model_answer = response['message']['content']
        model_answer_dict = extract_json(model_answer)
        print(model_answer)

        if not model_answer_dict:
            return JsonResponse({'error': 'Failed to parse LLM response as JSON'}, status=500)

        print(f"Processed text recipe: {model_answer_dict.get('name', 'Unknown')}")

        return JsonResponse(model_answer_dict, safe=False)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON in request body'}, status=400)
    except requests.exceptions.ConnectionError:
        return JsonResponse({'error': 'LLM service unavailable'}, status=503)
    except requests.exceptions.Timeout:
        return JsonResponse({'error': 'LLM timeout'}, status=504)
    except Exception as e:
        return JsonResponse({'error': f'Internal server error: {e}'}, status=500)


@csrf_exempt
def recognize_photo(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    data = json.loads(request.body)
    photo_base64 = data.get('photo')
    image_bytes = base64.b64decode(photo_base64)

    if not image_bytes:
        return JsonResponse({'error': 'Photo is required'}, status=400)

    try:
        response = cloud_client.chat(
            model='qwen3.5:397b-cloud',  # облачная мультимодальная модель
            messages=[{
                'role': 'user',
                'content': photo_recognize_prompt,
                'images': [image_bytes]  # ПЕРЕДАЁМ ФОТО ЗДЕСЬ

            }],
            options={
                'temperature': 0.1,
                'num_predict': 1024
            }, think=False,
            format='json'
        )
        model_answer_dict = json.loads(response['message']['content'])
        print(model_answer_dict)

        return JsonResponse(model_answer_dict, safe=False)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON from LLM'}, status=500)
    except requests.exceptions.ConnectionError:
        return JsonResponse({'error': 'LLM service unavailable'}, status=503)
    except requests.exceptions.Timeout:
        return JsonResponse({'error': 'LLM timeout'}, status=504)
    except Exception as e:
        return JsonResponse({'error': f'Internal server error: {e}'}, status=500)

def extract_json(text):
    """Извлекает JSON из текста, даже если есть пояснения"""
    # Ищем первый { и последний }
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1:
        json_str = text[start:end+1]
        try:
            return json.loads(json_str)
        except:
            pass
    return None

@csrf_exempt
def recipe_edit(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    print(f"cloud_client: {cloud_client}")
    try:
        data = json.loads(request.body)
        print(data)
        recipe = data.get('recipe')
        instruction = data.get('instruction')

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    if not recipe or not instruction:
        return JsonResponse({'error': 'recipe and instruction are required'}, status=400)
    try:
        response=cloud_client.chat(
        model='qwen3.5:397b-cloud',  # облачная мультимодальная модель
        messages=[{
            'role': 'user',
            'content': f"{recipe_edit_prompt}\nрецепт - {recipe}\nинструкция - {instruction}"
        }],
        options={
            'temperature': 0.1,
            'num_predict': 1024
        }, 
        think=False,
        format='json'

    )
        print(response)
        
        model_answer_dict=extract_json(response['message']['content'])
        print(f"🔵 4. JSON распарсен: {model_answer_dict}")
        return JsonResponse({'recipe':model_answer_dict}, safe=False)

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