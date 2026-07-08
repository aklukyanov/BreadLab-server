
from django.urls import path

from core.views.bot.LLM import recognize_photo, recipe_hydro_analyze, recipe_edit, recognize_text_recipe
from core.views.bot.crud_recipes import get_user_recipes, create_recipe, get_uniq_recipe, update_recipe, delete_recipe, \
    get_recipe_children, get_recipe_parents, check_recipe_exists
from core.views.bot.crud_users import create_user, delete_user
from core.views.bot.options import starter_calc, recipe_multiply
from core.views.web.greeting import home, login_view, register_view, dashboard_view, logout_view, delete_recipe_web

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
    path('recognize_text/', recognize_text_recipe),
    path('recipe_hydro_analyze/', recipe_hydro_analyze),
    path('recipe_edit/', recipe_edit),
    path('recipe_check_exists/', check_recipe_exists),

    # WEB
    path('', home, name='home'),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/recipes/<int:recipe_id>/delete/', delete_recipe_web, name='delete_recipe_web'),

]