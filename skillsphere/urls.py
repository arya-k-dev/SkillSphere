"""
URL configuration for skillsphere project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path

from matching import views as matching_views
from messaging import views as messaging_views
from sessions import views as sessions_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('accounts/', include('accounts.urls')),
    path('skills/', include('skills.urls')),
    path('matching/', include('matching.urls')),
    path('messages/', include('messaging.urls')),
    path('sessions/', include('sessions.urls')),
    path('', include('engagement.urls')),
    path('ratings/', sessions_views.ratings_page, name='ratings'),
    path('notifications/', messaging_views.notification_list, name='notifications'),
    path('notifications/<int:notification_id>/read/', messaging_views.mark_notification_read, name='notification_read'),
    path('notifications/read-all/', messaging_views.mark_all_notifications_read, name='notifications_read_all'),
    path('notifications/clear-read/', messaging_views.clear_read_notifications, name='notifications_clear_read'),
    path('requests/', matching_views.match_requests, name='requests_list'),
    path('requests/send/<int:user_id>/', matching_views.send_match_request, name='requests_send'),
    path('requests/accept/<int:request_id>/', matching_views.accept_match_request, name='requests_accept'),
    path('requests/decline/<int:request_id>/', matching_views.decline_match_request, name='requests_decline'),
    path('requests/cancel/<int:request_id>/', matching_views.cancel_match_request, name='requests_cancel'),
]
