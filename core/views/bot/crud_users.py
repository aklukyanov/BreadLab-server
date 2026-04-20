import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from core.models import User
from core.serializers import UserSerializer
from logger import crud_users_logger


@csrf_exempt
def create_user(request):
    """
    Создаёт нового пользователя или возвращает существующего по external_id.

    Валидный JSON запроса (POST):
    {
        "external_id": "12345",
        "channel": "vk",
        "username": "alex_baker",
        "first_name": "Алексей",
        "last_name": "Пекарев",
        "gender": "male"
    }

    Поля:
    - external_id (str, обязательно): ID пользователя во внешней системе (VK, TG).
    - channel (str, опционально): Канал регистрации. По умолчанию "vk".
    - username, first_name, last_name, gender (str, опционально): Данные профиля.

    Успешный ответ (201 - создан, 200 - уже существует):
    {
        "id": 1,
        "external_id": "12345",
        "channel": "vk",
        "first_name": "Алексей",
        "last_name": "Пекарев",
        "username": "alex_baker",
        "gender": "male",
        "registered_at": "2026-04-20T21:47:16.154Z",
        "last_active": "2026-04-20T21:47:16.154Z"
    }
    """
    if request.method != 'POST':
        crud_users_logger.warning(f"Method {request.method} not allowed for create_user")
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        crud_users_logger.warning("Invalid JSON in create_user request body")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    external_id = data.get('external_id')
    if not external_id:
        return JsonResponse({'error': 'external_id is required'}, status=400)

    crud_users_logger.info(f"Creating/updating user with external_id={external_id}")

    user, created = User.objects.get_or_create(
        external_id=external_id,
        channel=data.get('channel', 'vk'),
        defaults={
            'first_name': data.get('first_name'),
            'last_name': data.get('last_name'),
            'username': data.get('username'),
            'gender': data.get('gender'),
        }
    )

    if created:
        crud_users_logger.info(f"User created: {external_id}")
    else:
        crud_users_logger.info(f"User already exists: {external_id}")

    serializer = UserSerializer(user)
    return JsonResponse(serializer.data, status=201 if created else 200)


@csrf_exempt
def delete_user(request, user_id):
    """
    Удаляет пользователя по его внутреннему ID в БД.

    URL: DELETE /api/users/<user_id>/

    Пример запроса: DELETE /api/users/42/

    Успешный ответ (200):
    {
        "message": "User deleted"
    }

    Ошибки:
    - 404: Пользователь не найден.
    - 405: Метод не DELETE.
    """
    if request.method != 'DELETE':
        crud_users_logger.warning(f"Method {request.method} not allowed for delete_user")
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    crud_users_logger.info(f"Attempting to delete user with id={user_id}")

    try:
        user = User.objects.get(id=user_id)
        external_id = user.external_id
        user.delete()
        crud_users_logger.info(f"User deleted: id={user_id}, external_id={external_id}")
        return JsonResponse({'message': 'User deleted'}, status=200)
    except User.DoesNotExist:
        crud_users_logger.warning(f"User not found for deletion: id={user_id}")
        return JsonResponse({'error': 'User not found'}, status=404)