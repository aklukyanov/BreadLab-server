import json
import base64
import requests
from logger import llm_client_logger
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from utils.client import cloud_client
from utils.prompts import (
    photo_recognize_prompt,
    recipe_hydro_analyze_prompt,
    recipe_edit_prompt,
    recognize_text_recipe_prompt
)



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

        full_prompt = f"{recognize_text_recipe_prompt}\n\nТЕКСТ РЕЦЕПТА:\n{recipe_text}"

        response = cloud_client.chat(
            model='gemma3:27b-cloud',
            messages=[{'role': 'user', 'content': full_prompt}],
            options={'temperature': 0.1, 'num_predict': 1024},
            think=False,
            format='json'
        )

        model_answer = response['message']['content']
        llm_client_logger.debug(f"LLM raw response: {model_answer[:200]}...")

        model_answer_dict = extract_json(model_answer)

        if not model_answer_dict:
            llm_client_logger.error("Failed to parse LLM response as JSON")
            return JsonResponse({'error': 'Failed to parse LLM response as JSON'}, status=500)

        llm_client_logger.info(f"Processed text recipe: {model_answer_dict.get('title', 'Unknown')}")
        return JsonResponse(model_answer_dict, safe=False)

    except json.JSONDecodeError:
        llm_client_logger.warning("Invalid JSON in request body")
        return JsonResponse({'error': 'Invalid JSON in request body'}, status=400)
    except requests.exceptions.ConnectionError:
        llm_client_logger.error("LLM service unavailable (connection error)")
        return JsonResponse({'error': 'LLM service unavailable'}, status=503)
    except requests.exceptions.Timeout:
        llm_client_logger.error("LLM timeout")
        return JsonResponse({'error': 'LLM timeout'}, status=504)
    except Exception as e:
        llm_client_logger.exception(f"Internal server error: {e}")
        return JsonResponse({'error': f'Internal server error: {e}'}, status=500)


@csrf_exempt
def recognize_photo(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        photo_base64 = data.get('photo')
        image_bytes = base64.b64decode(photo_base64)

        if not image_bytes:
            return JsonResponse({'error': 'Photo is required'}, status=400)

        response = cloud_client.chat(
            model='qwen3.5:397b-cloud',
            messages=[{
                'role': 'user',
                'content': photo_recognize_prompt,
                'images': [image_bytes]
            }],
            options={'temperature': 0.1, 'num_predict': 1024},
            think=False,
            format='json'
        )

        model_answer_dict = json.loads(response['message']['content'])
        llm_client_logger.info(f"Processed photo recipe: {model_answer_dict.get('title', 'Unknown')}")
        return JsonResponse(model_answer_dict, safe=False)

    except json.JSONDecodeError:
        llm_client_logger.error("Invalid JSON from LLM")
        return JsonResponse({'error': 'Invalid JSON from LLM'}, status=500)
    except requests.exceptions.ConnectionError:
        llm_client_logger.error("LLM service unavailable (connection error)")
        return JsonResponse({'error': 'LLM service unavailable'}, status=503)
    except requests.exceptions.Timeout:
        llm_client_logger.error("LLM timeout")
        return JsonResponse({'error': 'LLM timeout'}, status=504)
    except Exception as e:
        llm_client_logger.exception(f"Internal server error: {e}")
        return JsonResponse({'error': f'Internal server error: {e}'}, status=500)


def extract_json(text):
    """Извлекает JSON из текста, даже если есть пояснения"""
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1:
        json_str = text[start:end+1]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
    return None


@csrf_exempt
def recipe_edit(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        recipe = data.get('recipe')
        instruction = data.get('instruction')
    except json.JSONDecodeError:
        llm_client_logger.warning("Invalid JSON in request body")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    if not recipe or not instruction:
        return JsonResponse({'error': 'recipe and instruction are required'}, status=400)

    try:
        response = cloud_client.chat(
            model='gemma3:27b-cloud',
            messages=[{
                'role': 'user',
                'content': f"{recipe_edit_prompt}\nрецепт - {recipe}\nинструкция - {instruction}"
            }],
            options={'temperature': 0.1, 'num_predict': 1024},
            think=False,
            format='json'
        )

        llm_client_logger.debug(f"LLM edit response: {response}")

        model_answer_dict = extract_json(response['message']['content'])
        llm_client_logger.info(f"Parsed edit result: {model_answer_dict}")

        if model_answer_dict:
            return JsonResponse(model_answer_dict, safe=False)
        else:
            llm_client_logger.error("Failed to parse LLM edit response as JSON")
            return JsonResponse({'error': 'Invalid JSON from LLM'}, status=500)

    except json.JSONDecodeError:
        llm_client_logger.error("Invalid JSON from LLM")
        return JsonResponse({'error': 'Invalid JSON from LLM'}, status=500)
    except requests.exceptions.ConnectionError:
        llm_client_logger.error("LLM service unavailable (connection error)")
        return JsonResponse({'error': 'LLM service unavailable'}, status=503)
    except requests.exceptions.Timeout:
        llm_client_logger.error("LLM timeout")
        return JsonResponse({'error': 'LLM timeout'}, status=504)
    except Exception as e:
        llm_client_logger.exception(f"Internal server error: {e}")
        return JsonResponse({'error': f'Internal server error: {e}'}, status=500)


@csrf_exempt
def recipe_hydro_analyze(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        recipe = data.get('recipe')
    except json.JSONDecodeError:
        llm_client_logger.warning("Invalid JSON in request body")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    if not recipe:
        return JsonResponse({'error': 'recipe is required'}, status=400)

    try:
        response = cloud_client.chat(
            model='qwen3.5:397b-cloud',
            messages=[{
                'role': 'user',
                'content': f'{recipe_hydro_analyze_prompt}.\n Исходный рецепт:\n{recipe}'
            }],
            options={'temperature': 0.1, 'num_predict': 1024},
            think=False
        )

        model_answer_dict = json.loads(response['message']['content'])
        return JsonResponse(model_answer_dict, safe=False)

    except json.JSONDecodeError:
        llm_client_logger.error("Invalid JSON from LLM")
        return JsonResponse({'error': 'Invalid JSON from LLM'}, status=500)
    except requests.exceptions.ConnectionError:
        llm_client_logger.error("LLM service unavailable (connection error)")
        return JsonResponse({'error': 'LLM service unavailable'}, status=503)
    except requests.exceptions.Timeout:
        llm_client_logger.error("LLM timeout")
        return JsonResponse({'error': 'LLM timeout'}, status=504)
    except Exception as e:
        llm_client_logger.exception(f"Internal server error: {e}")
        return JsonResponse({'error': f'Internal server error:{e}'}, status=500)