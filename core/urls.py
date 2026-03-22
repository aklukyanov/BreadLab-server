
from django.urls import path
from core.views.bot.views import create_user, create_recipe, get_user_recipes, delete_recipe, delete_user, starter_calc, \
    recipe_multiply, update_recipe, get_uniq_recipe, get_recipe_children, get_recipe_parents, recognize_photo, \
    recipe_edit, recipe_hydro_analyze

urlpatterns = [
    path('users/', create_user),
    path('users/<int:user_id>/', delete_user),
    path('users/<int:user_id>/recipes/', get_user_recipes),

    path('recipes/', create_recipe),
    path('recipes/<int:recipe_id>/', get_uniq_recipe),  # GET
    path('recipes/<int:recipe_id>/update/', update_recipe),  # PATCH
    path('recipes/<int:recipe_id>/delete/', delete_recipe),  # DELETE
    path ('recipes/<int:recipe_id>/children/', get_recipe_children), # выводит рецепты, созданные на основе запрашиваемого рецепта
    path ('recipes/<int:recipe_id>/parents/', get_recipe_parents), # выводит рецепты, на основе которых был создан текущий рецепт

    path('starter_calc/', starter_calc),
    path('recipe_multiply/', recipe_multiply),
    path('recognize_photo/', recognize_photo),
    path('recipe_hydro_analyze/', recipe_hydro_analyze),
    path('recipe_edit/', recipe_edit)
]