from django.urls import path

from . import views


app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("explore/", views.explore_skills, name="explore"),
    path("explore/<slug:slug>/", views.explore_skill_detail, name="explore_detail"),
    path("search/", views.global_search, name="global_search"),
    path("dashboard/", views.dashboard, name="dashboard"),
]
