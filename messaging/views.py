from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from matching.models import MatchRequest, SkillExchange

from .models import ChatThread, Message, Notification
from .services import ensure_exchange_communication, notify_message_received


def _accepted_exchange_queryset(user):
    return SkillExchange.objects.select_related(
        "request",
        "requester",
        "requester__profile",
        "responder",
        "responder__profile",
        "offered_skill",
        "requested_skill",
    ).filter(
        Q(requester=user) | Q(responder=user),
        request__status=MatchRequest.ACCEPTED,
    )


def _exchange_summary(exchange, user):
    if exchange.requester_id == user.pk:
        return {
            "teach": exchange.offered_skill.title if exchange.offered_skill else "Skill not selected",
            "learn": exchange.requested_skill.title if exchange.requested_skill else "Skill not selected",
        }

    return {
        "teach": exchange.requested_skill.title if exchange.requested_skill else "Skill not selected",
        "learn": exchange.offered_skill.title if exchange.offered_skill else "Skill not selected",
    }


@login_required
def messages_inbox(request):
    threads = (
        ChatThread.objects.select_related(
            "exchange",
            "exchange__request",
            "exchange__requester",
            "exchange__requester__profile",
            "exchange__responder",
            "exchange__responder__profile",
            "exchange__offered_skill",
            "exchange__requested_skill",
            "user_one",
            "user_two",
        )
        .prefetch_related("messages")
        .filter(
            Q(user_one=request.user) | Q(user_two=request.user),
            is_active=True,
            exchange__request__status=MatchRequest.ACCEPTED,
        )
    )

    thread_cards = []
    for thread in threads:
        last_message = thread.messages.last()
        partner = thread.get_partner(request.user)
        thread_cards.append(
            {
                "thread": thread,
                "partner": partner,
                "summary": _exchange_summary(thread.exchange, request.user),
                "last_message": last_message,
                "unread_count": thread.unread_count_for(request.user),
            }
        )

    return render(request, "messaging/inbox.html", {"thread_cards": thread_cards})


@login_required
def exchange_chat(request, exchange_id):
    exchange = get_object_or_404(_accepted_exchange_queryset(request.user), pk=exchange_id)
    if exchange.requester_id == exchange.responder_id:
        raise PermissionDenied("You cannot message yourself.")

    thread = ensure_exchange_communication(exchange)
    if not thread.includes_user(request.user):
        raise PermissionDenied("You do not have access to this chat.")

    if request.method == "POST":
        body = request.POST.get("body", "").strip()
        if not body:
            messages.error(request, "Message cannot be empty.")
            return redirect("messaging:exchange_chat", exchange_id=exchange.pk)

        chat_message = Message.objects.create(thread=thread, sender=request.user, body=body)
        notify_message_received(chat_message)
        thread.updated_at = timezone.now()
        thread.save(update_fields=["updated_at"])
        return redirect("messaging:exchange_chat", exchange_id=exchange.pk)

    thread.messages.exclude(sender=request.user).filter(is_read=False).update(is_read=True)
    partner = thread.get_partner(request.user)
    context = {
        "exchange": exchange,
        "thread": thread,
        "partner": partner,
        "summary": _exchange_summary(exchange, request.user),
        "chat_messages": thread.messages.select_related("sender", "sender__profile"),
    }
    return render(request, "messaging/chat.html", context)


@login_required
def notification_list(request):
    notifications = Notification.objects.filter(user=request.user)
    return render(request, "messaging/notifications.html", {"notifications": notifications})


@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, pk=notification_id, user=request.user)
    if not notification.is_read:
        notification.is_read = True
        notification.save(update_fields=["is_read"])
    return redirect(notification.related_url or "notifications")


@login_required
def mark_all_notifications_read(request):
    if request.method == "POST":
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect("notifications")


@login_required
def clear_read_notifications(request):
    if request.method == "POST":
        Notification.objects.filter(user=request.user, is_read=True).delete()
    return redirect("notifications")
