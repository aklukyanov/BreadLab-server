
from django.urls import path
from core.views.bot.views import create_user, create_recipe, get_user_recipes, delete_recipe, delete_user, starter_calc, \
    recipe_multiply, update_recipe, get_uniq_recipe

urlpatterns = [
    path('users/', create_user),
    path('users/<int:user_id>/', delete_user),
    path('users/<int:user_id>/recipes/', get_user_recipes),

    path('recipes/', create_recipe),
    path('recipes/<int:recipe_id>/', get_uniq_recipe),  # GET
    path('recipes/<int:recipe_id>/update/', update_recipe),  # PATCH
    path('recipes/<int:recipe_id>/delete/', delete_recipe),  # DELETE

    path('starter_calc/', starter_calc),
    path('recipe_multiply/', recipe_multiply)
]