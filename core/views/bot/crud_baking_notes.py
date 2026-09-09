import json
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from core.models import BakingSession, BakingNote
from core.serializers import BakingNoteSerializer
from logger import crud_baking_notes_logger


@csrf_exempt
def create_baking_note(request):
    """
    Добавляет заметку к сессии выпечки.

    POST /api/baking_notes/
    {
        "baking_session_id": 1,
        "type": "text",
        "note": "Тесто поднялось за 3 часа"
    }

    Поля:
    - baking_session_id (int, обязательно): ID сессии выпечки.
    - type (str, обязательно): 'text' или 'photo'.
    - note (str, обязательно): Текст заметки или ссылка на фото в VK.

    Успешный ответ (201):
    {
        "id": 1,
        "baking_session_id": 1,
        "note": "Тесто поднялось за 3 часа",
        "type": "text",
        "created_at": "2026-09-09T12:05:00Z",
        "updated_at": "2026-09-09T12:05:00Z"
    }

    Ошибки:
    - 400: Invalid JSON / Missing required fields
    - 404: Baking session not found
    - 405: Method not allowed
    """
    if request.method != 'POST':
        crud_baking_notes_logger.warning(f"Method {request.method} not allowed for create_baking_note")
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        crud_baking_notes_logger.warning("Invalid JSON in create_baking_note")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    baking_session_id = data.get('baking_session_id')
    note_type = data.get('type')
    note_text = data.get('note')

    if not baking_session_id or not note_type or not note_text:
        return JsonResponse({'error': 'baking_session_id, type and note are required'}, status=400)

    try:
        session = BakingSession.objects.get(id=baking_session_id)
    except BakingSession.DoesNotExist:
        crud_baking_notes_logger.warning(f"Baking session not found: id={baking_session_id}")
        return JsonResponse({'error': 'Baking session not found'}, status=404)

    baking_note = BakingNote.objects.create(
        baking_session=session,
        type=note_type,
        note=note_text,
    )

    crud_baking_notes_logger.info(f"Baking note created: id={baking_note.id}, session_id={baking_session_id}, type={note_type}")

    serializer = BakingNoteSerializer(baking_note)
    return JsonResponse(serializer.data, status=201)


@csrf_exempt
def get_baking_session_notes(request, session_id):
    """
    Возвращает заметки сессии выпечки.

    Поддерживает пагинацию (для бота) и полный вывод (для веб-клиента).

    GET /api/baking_sessions/<session_id>/notes/
    GET /api/baking_sessions/<session_id>/notes/?page=1
    GET /api/baking_sessions/<session_id>/notes/?paginate=false

    Параметры query string:
    - page (int, опционально): Номер страницы. По умолчанию 1.
    - paginate (str, опционально): 'true' (по умолчанию) или 'false'.
        Если 'false' — возвращает все заметки без пагинации.

    Ответ с пагинацией (200):
    {
        "notes": [...],
        "page": 1,
        "has_next": true,
        "has_prev": false,
        "total_pages": 2
    }

    Ответ без пагинации (200):
    {
        "notes": [...]
    }

    Ошибки:
    - 404: Baking session not found
    - 405: Method not allowed
    """
    if request.method != 'GET':
        crud_baking_notes_logger.warning(f"Method {request.method} not allowed for get_baking_session_notes")
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        session = BakingSession.objects.get(id=session_id)
    except BakingSession.DoesNotExist:
        crud_baking_notes_logger.warning(f"Baking session not found: id={session_id}")
        return JsonResponse({'error': 'Baking session not found'}, status=404)

    notes = BakingNote.objects.filter(baking_session=session).order_by('created_at')

    paginate = request.GET.get('paginate', 'true')

    if paginate == 'false':
        crud_baking_notes_logger.debug(f"Fetching all notes for session_id={session_id}, total={notes.count()}")
        serializer = BakingNoteSerializer(notes, many=True)
        return JsonResponse({'notes': serializer.data})

    paginator = Paginator(notes, 4)
    page = request.GET.get('page', 1)
    notes_page = paginator.get_page(page)

    crud_baking_notes_logger.debug(f"Fetching notes for session_id={session_id}, page={page}, total={paginator.count}")

    serializer = BakingNoteSerializer(notes_page, many=True)
    return JsonResponse({
        'notes': serializer.data,
        'page': int(page),
        'has_next': notes_page.has_next(),
        'has_prev': notes_page.has_previous(),
        'total_pages': paginator.num_pages
    })


@csrf_exempt
def delete_baking_note(request, note_id):
    """
    Удаляет заметку сессии выпечки.

    DELETE /api/baking_notes/<note_id>/

    Успешный ответ (200):
    {
        "message": "Baking note deleted"
    }

    Ошибки:
    - 404: Baking note not found
    - 405: Method not allowed
    """
    if request.method != 'DELETE':
        crud_baking_notes_logger.warning(f"Method {request.method} not allowed for delete_baking_note")
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        note = BakingNote.objects.get(id=note_id)
        note.delete()
        crud_baking_notes_logger.info(f"Baking note deleted: id={note_id}")
        return JsonResponse({'message': 'Baking note deleted'}, status=200)
    except BakingNote.DoesNotExist:
        crud_baking_notes_logger.warning(f"Baking note not found: id={note_id}")
        return JsonResponse({'error': 'Baking note not found'}, status=404)


@csrf_exempt
def update_baking_note(request, note_id):
    """
    Обновляет заметку сессии выпечки.

    PATCH /api/baking_notes/<note_id>/update/
    {
        "note": "Тесто поднялось за 2.5 часа"
    }

    Поля (опционально — обновляются только переданные):
    - note (str): Новый текст заметки или ссылка на фото в VK.
    - type (str): Новый тип: 'text' или 'photo'.

    Успешный ответ (200):
    {
        "id": 1,
        "baking_session_id": 1,
        "note": "Тесто поднялось за 2.5 часа",
        "type": "text",
        "created_at": "...",
        "updated_at": "..."
    }

    Ошибки:
    - 400: Invalid JSON
    - 404: Baking note not found
    - 405: Method not allowed
    """
    if request.method != 'PATCH':
        crud_baking_notes_logger.warning(f"Method {request.method} not allowed for update_baking_note")
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        crud_baking_notes_logger.warning("Invalid JSON in update_baking_note")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    try:
        baking_note = BakingNote.objects.get(id=note_id)
    except BakingNote.DoesNotExist:
        crud_baking_notes_logger.warning(f"Baking note not found: id={note_id}")
        return JsonResponse({'error': 'Baking note not found'}, status=404)

    if 'note' in data:
        baking_note.note = data['note']
    if 'type' in data:
        baking_note.type = data['type']

    baking_note.save()

    crud_baking_notes_logger.info(f"Baking note updated: id={note_id}")

    serializer = BakingNoteSerializer(baking_note)
    return JsonResponse(serializer.data, status=200)
