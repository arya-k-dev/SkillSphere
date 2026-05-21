from django.contrib import admin

from .models import MatchRequest, SkillExchange


@admin.register(MatchRequest)
class MatchRequestAdmin(admin.ModelAdmin):
    list_display = ("sender", "receiver", "status", "score", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("sender__username", "receiver__username", "message")


@admin.register(SkillExchange)
class SkillExchangeAdmin(admin.ModelAdmin):
    list_display = ("requester", "responder", "offered_skill", "requested_skill", "created_at")
    search_fields = ("requester__username", "responder__username")
