from django.contrib import admin

from .models import Skill


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "skill_type", "level", "mode", "user", "created_at")
    list_filter = ("skill_type", "level", "mode", "category")
    search_fields = ("title", "category", "description", "user__username")
