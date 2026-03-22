import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from core.models import User
from core.serializers import UserSerializer


@csrf_exempt
def create_user(request):
    """
    {
  "external_id": "12345",
  "channel": "vk",
  "username": "alex_baker",
  "first_name": "Алексей",
  "last_name": "Пекарев"
}"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    data = json.loads(request.body)

    user, created = User.objects.get_or_create(
        external_id=data['external_id'],
        channel=data.get('channel', 'vk'),
        defaults={
            'first_name': data.get('first_name'),
            'last_name': data.get('last_name'),
            'username': data.get('username'),
            'gender': data.get('gender'),
        }
    )

    serializer = UserSerializer(user)
    return JsonResponse(serializer.data, status=201 if created else 200)


@csrf_exempt
def delete_user(request, user_id):
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        user=User.objects.get(id=user_id)
        user.delete()
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

    return JsonResponse({'message': 'User deleted'}, status=200)