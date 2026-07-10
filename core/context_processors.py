from core.models import Recipe


def user_recipes_count(request):
    user_id = request.session.get('user_id')
    if user_id:
        from core.models import User
        try:
            user = User.objects.get(id=user_id)
            return {'user_recipes_count': Recipe.objects.filter(user=user).count()}
        except User.DoesNotExist:
            pass
    return {}
