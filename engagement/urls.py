from django.urls import path

from . import views


app_name = "engagement"

urlpatterns = [
    path("achievements/", views.achievements_page, name="achievements"),
    path("certificates/", views.certificates_page, name="certificates"),
    path("certificates/<int:certificate_id>/", views.certificate_detail, name="certificate_detail"),
    path("leaderboard/", views.leaderboard_page, name="leaderboard"),
    path("community/", views.community_page, name="community"),
]
