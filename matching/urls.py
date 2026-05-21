from django.urls import path

from . import views

app_name = "matching"

urlpatterns = [
    path("", views.recommended_matches, name="recommended"),
    path("user/<int:user_id>/", views.match_detail, name="detail"),
    path("request/<int:user_id>/send/", views.send_match_request, name="send_request"),
    path("requests/send/<int:user_id>/", views.send_match_request, name="send_request_alias"),
    path("requests/", views.match_requests, name="requests"),
    path("exchanges/", views.my_exchanges, name="exchanges"),
    path("requests/accept/<int:request_id>/", views.accept_match_request, name="accept_request_alias"),
    path("requests/decline/<int:request_id>/", views.decline_match_request, name="decline_request_alias"),
    path("requests/cancel/<int:request_id>/", views.cancel_match_request, name="cancel_request_alias"),
    path("request/<int:request_id>/accept/", views.accept_match_request, name="accept_request"),
    path("request/<int:request_id>/decline/", views.decline_match_request, name="decline_request"),
    path("request/<int:request_id>/cancel/", views.cancel_match_request, name="cancel_request"),
]
