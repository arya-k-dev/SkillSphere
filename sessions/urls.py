from django.urls import path

from . import views


app_name = "sessions"

urlpatterns = [
    path("", views.sessions_list, name="list"),
    path("schedule/<int:exchange_id>/", views.schedule_session, name="schedule"),
    path("<int:session_id>/", views.session_detail, name="detail"),
    path("<int:session_id>/edit/", views.edit_session, name="edit"),
    path("<int:session_id>/cancel/", views.cancel_session, name="cancel"),
    path("<int:session_id>/complete/", views.mark_session_complete, name="complete"),
    path("<int:session_id>/feedback/", views.submit_session_feedback, name="feedback"),
]
