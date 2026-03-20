
from django.urls import path
from core.views.bot import create_user, create_recipe, get_user_recipes
urlpatterns = [
    path('users/', create_user),
    path('recipes/', create_recipe),
    path('users/<int:user_id>/recipes/', get_user_recipes)
]