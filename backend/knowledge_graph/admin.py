from django.contrib import admin
from .models import Character, Relationship, Event, Work, Article

@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    list_display = ('name', 'work', 'faction', 'description')
    list_filter = ('work', 'faction')
    search_fields = ('name', 'description')

@admin.register(Relationship)
class RelationshipAdmin(admin.ModelAdmin):
    list_display = ('source', 'target', 'type', 'work')
    list_filter = ('work', 'type')
    search_fields = ('source__name', 'target__name', 'description')

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'work', 'time', 'description')
    list_filter = ('work',)
    search_fields = ('name', 'description')

@admin.register(Work)
class WorkAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'updated_at')
    search_fields = ('name',)

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'work', 'created_at')
    list_filter = ('work',)
    search_fields = ('title', 'text')
