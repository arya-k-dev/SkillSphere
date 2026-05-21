from django.urls import path

from . import views


app_name = "messaging"

urlpatterns = [
    path("", views.messages_inbox, name="inbox"),
    path("exchange/<int:exchange_id>/", views.exchange_chat, name="exchange_chat"),
]
