from django.urls import path

from . import views


app_name = "skills"

urlpatterns = [
    path("", views.skill_list, name="list"),
    path("browse/", views.public_skill_browse, name="browse"),
    path("add/", views.skill_add, name="add"),
    path("my/", views.my_skills, name="my_skills"),
    path("<int:pk>/", views.skill_detail, name="detail"),
    path("<int:pk>/edit/", views.skill_edit, name="edit"),
    path("<int:pk>/delete/", views.skill_delete, name="delete"),
    path("<slug:slug>/", views.public_skill_detail, name="public_detail"),
]
