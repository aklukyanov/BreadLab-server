from django.contrib import admin
from .models import User
from .models import Recipe


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """User model admin interface"""

    list_display = (
        'id',
        'external_id',
        'channel',
        'first_name',
        'last_name',
        'username',
        'registered_at',
        'last_active'
    )

    list_filter = ('channel', 'registered_at', 'last_active')

    search_fields = ('external_id', 'first_name', 'last_name', 'username')

    readonly_fields = ('registered_at', 'last_active')

    fieldsets = (
        ('Identification', {
            'fields': ('external_id', 'channel')
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'username', 'gender')
        }),
        ('Platforms', {
            'fields': ('platforms',)
        }),
        ('Metadata', {
            'fields': ('registered_at', 'last_active'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title', 'parent', 'hydration', 'created_at', 'updated_at')
    list_filter = ('created_at', 'hydration')
    search_fields = ('user__external_id', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at', 'parent')

    fieldsets = (
        ('Recipe Data', {
            'fields': ('user', 'recipe', 'dry_sum', 'wet_sum', 'hydration')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )