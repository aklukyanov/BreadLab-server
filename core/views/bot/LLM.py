import requests
import json
import tempfile
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from utils.client import cloud_client
from utils.prompts import photo_recognize_prompt, recipe_hydro_analyze_prompt, recipe_edit_prompt





@csrf_exempt
def recognize_photo(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    photo=request.FILES.get('photo')

    if not photo:
        return JsonResponse({'error': 'Photo is required'}, status=400)

    try:
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            tmp.write(photo.read())
            tmp_path = tmp.name


        response = cloud_client.chat(
            model='qwen3.5:397b-cloud',  # облачная мультимодальная модель
            messages=[{
                'role': 'user',
                'content': photo_recognize_prompt,
                'images': [tmp_path]  # ПЕРЕДАЁМ ФОТО ЗДЕСЬ
            }],
            options={
                'temperature': 0.1,
                'num_predict': 1024
            }, think=False
        )


        model_answer_dict = json.loads(response['message']['content'])
        return JsonResponse(model_answer_dict, safe=False)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON from LLM'}, status=500)
    except requests.exceptions.ConnectionError:
        return JsonResponse({'error': 'LLM service unavailable'}, status=503)
    except requests.exceptions.Timeout:
        return JsonResponse({'error': 'LLM timeout'}, status=504)
    except Exception as e:
        return JsonResponse({'error': f'Internal server error: {e}'}, status=500)

    finally:
        if tmp_path and os.path.exists(tmp_path):
             os.unlink(tmp_path)

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