from django.contrib import admin
from .models import User
from .models import Recipe
from .models import BakingSession
from .models import BakingNote


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
        'password',
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
    list_display = ('id', 'user', 'title', 'parents', 'hydration', 'created_at', 'updated_at')
    list_filter = ('created_at', 'hydration')
    search_fields = ('user__external_id', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at', 'parents')

    fieldsets = (
        ('Recipe Data', {
            'fields': ('user', 'recipe', 'hydration')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(BakingSession)
class BakingSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__external_id', 'user__first_name', 'recipe__title')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Session Data', {
            'fields': ('user', 'recipe', 'status')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(BakingNote)
class BakingNoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'baking_session', 'type', 'created_at')
    list_filter = ('type', 'created_at')
    search_fields = ('baking_session__recipe__title', 'note')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Note Data', {
            'fields': ('baking_session', 'type', 'note')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )