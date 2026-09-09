import json
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from core.models import User, Recipe, BakingSession
from core.serializers import BakingSessionSerializer
from logger import crud_baking_sessions_logger


@csrf_exempt
def create_baking_session(request):
    """
    Создаёт новую сессию выпечки.

    POST /api/baking_sessions/
    {
        "user_id": 1,
        "recipe_id": 5
    }

    Поля:
    - user_id (int, обязательно): ID пользователя.
    - recipe_id (int, обязательно): ID рецепта.

    Сессия всегда создаётся со статусом "unfinished".

    Успешный ответ (201):
    {
        "id": 1,
        "recipe_title": "Сита",
        "status": "unfinished",
        "created_at": "2026-09-09T12:00:00Z",
        "updated_at": "2026-09-09T12:00:00Z"
    }

    Ошибки:
    - 400: Invalid JSON / Missing required fields
    - 404: User not found / Recipe not found
    - 405: Method not allowed
    """
    if request.method != 'POST':
        crud_baking_sessions_logger.warning(f"Method {request.method} not allowed for create_baking_session")
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        crud_baking_sessions_logger.warning("Invalid JSON in create_baking_session")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    user_id = data.get('user_id')
    recipe_id = data.get('recipe_id')

    if not user_id or not recipe_id:
        return JsonResponse({'error': 'user_id and recipe_id are required'}, status=400)

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        crud_baking_sessions_logger.warning(f"User not found: id={user_id}")
        return JsonResponse({'error': 'User not found'}, status=404)

    try:
        recipe = Recipe.objects.get(id=recipe_id)
    except Recipe.DoesNotExist:
        crud_baking_sessions_logger.warning(f"Recipe not found: id={recipe_id}")
        return JsonResponse({'error': 'Recipe not found'}, status=404)

    session = BakingSession.objects.create(
        user=user,
        recipe=recipe,
        status='unfinished',
    )

    crud_baking_sessions_logger.info(f"Baking session created: id={session.id}, user_id={user_id}, recipe_id={recipe_id}")

    serializer = BakingSessionSerializer(session)
    return JsonResponse(serializer.data, status=201)


@csrf_exempt
def delete_baking_session(request, session_id):
    """
    Удаляет сессию выпечки и все связанные заметки (CASCADE).

    DELETE /api/baking_sessions/<session_id>/

    Успешный ответ (200):
    {
        "message": "Baking session deleted"
    }

    Ошибки:
    - 404: Baking session not found
    - 405: Method not allowed
    """
    if request.method != 'DELETE':
        crud_baking_sessions_logger.warning(f"Method {request.method} not allowed for delete_baking_session")
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        session = BakingSession.objects.get(id=session_id)
        session.delete()
        crud_baking_sessions_logger.info(f"Baking session deleted: id={session_id}")
        return JsonResponse({'message': 'Baking session deleted'}, status=200)
    except BakingSession.DoesNotExist:
        crud_baking_sessions_logger.warning(f"Baking session not found: id={session_id}")
        return JsonResponse({'error': 'Baking session not found'}, status=404)


@csrf_exempt
def update_baking_session_status(request, session_id):
    """
    Обновляет статус сессии выпечки.

    PATCH /api/baking_sessions/<session_id>/update/
    {
        "status": "finished"
    }

    Поля:
    - status (str, обязательно): Новый статус: 'unfinished' или 'finished'.

    Успешный ответ (200):
    {
        "id": 1,
        "recipe_title": "Сита",
        "status": "finished",
        "created_at": "...",
        "updated_at": "..."
    }

    Ошибки:
    - 400: Invalid JSON / Missing required fields
    - 404: Baking session not found
    - 405: Method not allowed
    """
    if request.method != 'PATCH':
        crud_baking_sessions_logger.warning(f"Method {request.method} not allowed for update_baking_session_status")
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        crud_baking_sessions_logger.warning("Invalid JSON in update_baking_session_status")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    status = data.get('status')
    if not status:
        return JsonResponse({'error': 'status is required'}, status=400)

    try:
        session = BakingSession.objects.get(id=session_id)
    except BakingSession.DoesNotExist:
        crud_baking_sessions_logger.warning(f"Baking session not found: id={session_id}")
        return JsonResponse({'error': 'Baking session not found'}, status=404)

    session.status = status
    session.save()

    crud_baking_sessions_logger.info(f"Baking session status updated: id={session_id}, status={status}")

    serializer = BakingSessionSerializer(session)
    return JsonResponse(serializer.data, status=200)


@csrf_exempt
def get_user_baking_sessions(request, user_id):
    """
    Возвращает список сессий выпечки пользователя.

    Поддерживает пагинацию (для бота) и полный вывод (для веб-клиента).

    GET /api/users/<user_id>/baking_sessions/
    GET /api/users/<user_id>/baking_sessions/?page=1
    GET /api/users/<user_id>/baking_sessions/?recipe_id=5&status=unfinished
    GET /api/users/<user_id>/baking_sessions/?paginate=false

    Параметры query string:
    - page (int, опционально): Номер страницы. По умолчанию 1.
    - recipe_id (int, опционально): Фильтр по ID рецепта.
    - status (str, опционально): Фильтр по статусу ('unfinished', 'finished').
    - paginate (str, опционально): 'true' (по умолчанию) или 'false'.
        Если 'false' — возвращает все сессии без пагинации.

    Ответ с пагинацией (200) — по умолчанию:
    {
        "baking_sessions": [...],
        "page": 1,
        "has_next": true,
        "has_prev": false,
        "total_pages": 3
    }

    Ответ без пагинации (200) — paginate=false:
    {
        "baking_sessions": [...]
    }

    Ошибки:
    - 404: User not found
    - 405: Method not allowed
    """
    if request.method != 'GET':
        crud_baking_sessions_logger.warning(f"Method {request.method} not allowed for get_user_baking_sessions")
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        crud_baking_sessions_logger.warning(f"User not found: id={user_id}")
        return JsonResponse({'error': 'User not found'}, status=404)

    sessions = BakingSession.objects.filter(user=user).order_by('-created_at')

    recipe_id = request.GET.get('recipe_id')
    if recipe_id:
        sessions = sessions.filter(recipe_id=recipe_id)

    status = request.GET.get('status')
    if status:
        sessions = sessions.filter(status=status)

    paginate = request.GET.get('paginate', 'true')

    if paginate == 'false':
        crud_baking_sessions_logger.debug(f"Fetching all sessions for user_id={user_id}, total={sessions.count()}")
        serializer = BakingSessionSerializer(sessions, many=True)
        return JsonResponse({'baking_sessions': serializer.data})

    paginator = Paginator(sessions, 4)
    page = request.GET.get('page', 1)
    sessions_page = paginator.get_page(page)

    crud_baking_sessions_logger.debug(f"Fetching sessions for user_id={user_id}, page={page}, total={paginator.count}")

    serializer = BakingSessionSerializer(sessions_page, many=True)
    return JsonResponse({
        'baking_sessions': serializer.data,
        'page': int(page),
        'has_next': sessions_page.has_next(),
        'has_prev': sessions_page.has_previous(),
        'total_pages': paginator.num_pages
    })
