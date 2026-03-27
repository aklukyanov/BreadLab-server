
from django.urls import path

from core.views.bot.LLM import recognize_photo, recipe_hydro_analyze, recipe_edit
from core.views.bot.crud_recipes import get_user_recipes, create_recipe, get_uniq_recipe, update_recipe, delete_recipe, \
    get_recipe_children, get_recipe_parents
from core.views.bot.crud_users import create_user, delete_user
from core.views.bot.options import starter_calc, recipe_multiply

urlpatterns = [
    path('users/', create_user),
    path('users/<int:user_id>/', delete_user), #пока не используется
    path('users/<str:external_id>/recipes/', get_user_recipes),

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