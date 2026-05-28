from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import MatchRequestForm
from .models import MatchRequest, SkillExchange
from .utils import (
    build_match_data,
    calculate_match_score,
    get_exchange_skill_pair,
    get_match_request_state,
    get_recommended_matches,
)
from messaging.models import Notification
from messaging.services import notify_request_rejected, notify_request_sent


ACTIVE_REQUEST_STATUSES = [MatchRequest.PENDING, MatchRequest.ACCEPTED]
REQUEST_STATUS_PRIORITY = {
    "completed": 4,
    MatchRequest.ACCEPTED: 3,
    MatchRequest.PENDING: 2,
    MatchRequest.DECLINED: 1,
    MatchRequest.CANCELLED: 1,
}


def get_match_user(user_id, current_user):
    User = get_user_model()
    return get_object_or_404(
        User.objects.exclude(pk=current_user.pk).select_related("profile").prefetch_related("skills"),
        pk=user_id,
    )


def pending_request_exists(sender, receiver, offered_skill=None, requested_skill=None):
    return MatchRequest.objects.filter(
        sender=sender,
        receiver=receiver,
        offered_skill=offered_skill,
        requested_skill=requested_skill,
        status=MatchRequest.PENDING,
    ).exists()


def get_active_request(sender, receiver, offered_skill=None, requested_skill=None):
    return (
        MatchRequest.objects.filter(
            sender=sender,
            receiver=receiver,
            offered_skill=offered_skill,
            requested_skill=requested_skill,
            status__in=ACTIVE_REQUEST_STATUSES,
        )
        .order_by("-updated_at", "-created_at", "-pk")
        .first()
    )


def current_requests_only(requests):
    current_by_key = {}
    for match_request in requests:
        key = (
            match_request.sender_id,
            match_request.receiver_id,
            match_request.offered_skill_id,
            match_request.requested_skill_id,
        )
        existing = current_by_key.get(key)
        request_rank = (
            REQUEST_STATUS_PRIORITY.get(match_request.status, 0),
            match_request.updated_at,
            match_request.created_at,
            match_request.pk,
        )
        existing_rank = (
            REQUEST_STATUS_PRIORITY.get(existing.status, 0),
            existing.updated_at,
            existing.created_at,
            existing.pk,
        ) if existing else None
        if existing is None or request_rank > existing_rank:
            current_by_key[key] = match_request
    return sorted(current_by_key.values(), key=lambda item: (item.updated_at, item.created_at, item.pk), reverse=True)


@login_required
def recommended_matches(request):
    matches = get_recommended_matches(request.user)
    return render(request, "matching/recommended_matches.html", {"matches": matches})


@login_required
def match_detail(request, user_id):
    other_user = get_match_user(user_id, request.user)
    match_data = build_match_data(request.user, other_user)
    form = MatchRequestForm()
    offered_skill, requested_skill = get_exchange_skill_pair(request.user, other_user)
    active_request = get_active_request(request.user, other_user, offered_skill, requested_skill)
    match_data["request_state"] = get_match_request_state(request.user, other_user, offered_skill, requested_skill)
    existing_request = MatchRequest.objects.filter(
        sender=request.user,
        receiver=other_user,
        offered_skill=offered_skill,
        requested_skill=requested_skill,
        status=MatchRequest.PENDING,
    ).first()

    return render(
        request,
        "matching/match_detail.html",
        {
            "match": match_data,
            "form": form,
            "existing_request": existing_request,
            "active_request": active_request,
        },
    )


@login_required
def send_match_request(request, user_id):
    other_user = get_match_user(user_id, request.user)
    offered_skill, requested_skill = get_exchange_skill_pair(request.user, other_user)
    active_request = get_active_request(request.user, other_user, offered_skill, requested_skill)

    if active_request and active_request.status == MatchRequest.ACCEPTED:
        messages.info(request, "Exchange already accepted.")
        return redirect("matching:exchanges")
    if active_request:
        messages.info(request, "Request already sent.")
        return redirect("matching:requests")

    if request.method == "POST":
        form = MatchRequestForm(request.POST)
        if form.is_valid():
            match_request = form.save(commit=False)
            match_request.sender = request.user
            match_request.receiver = other_user
            match_request.offered_skill = offered_skill
            match_request.requested_skill = requested_skill
            match_request.score = calculate_match_score(request.user, other_user)
            try:
                match_request.full_clean()
                match_request.save()
            except IntegrityError:
                messages.info(request, "Request already sent.")
                return redirect("matching:requests")
            except ValidationError as error:
                form.add_error(None, error)
            else:
                notify_request_sent(match_request)
                messages.success(request, "Request sent successfully.")
                return redirect("matching:requests")
    else:
        form = MatchRequestForm()

    match_data = build_match_data(request.user, other_user)
    match_data["request_state"] = get_match_request_state(request.user, other_user, offered_skill, requested_skill)
    return render(
        request,
        "matching/match_detail.html",
        {"match": match_data, "form": form, "existing_request": None},
    )


@login_required
def match_requests(request):
    request_queryset = MatchRequest.objects.select_related(
        "sender",
        "sender__profile",
        "receiver",
        "receiver__profile",
        "offered_skill",
        "requested_skill",
    )
    sent_requests = current_requests_only(request_queryset.filter(sender=request.user))
    received_requests = current_requests_only(request_queryset.filter(receiver=request.user))
    notifications = Notification.objects.filter(user=request.user)[:5]
    return render(
        request,
        "matching/match_requests.html",
        {
            "sent_requests": sent_requests,
            "received_requests": received_requests,
            "notifications": notifications,
        },
    )


@login_required
def my_exchanges(request):
    exchanges = SkillExchange.objects.select_related(
        "request",
        "requester",
        "requester__profile",
        "responder",
        "responder__profile",
        "offered_skill",
        "requested_skill",
    ).filter(
        Q(requester=request.user) | Q(responder=request.user),
        request__status=MatchRequest.ACCEPTED,
    )

    exchange_cards = []
    for exchange in exchanges:
        partner = exchange.responder if exchange.requester_id == request.user.pk else exchange.requester
        if exchange.requester_id == request.user.pk:
            teach_skill = exchange.offered_skill
            learn_skill = exchange.requested_skill
        else:
            teach_skill = exchange.requested_skill
            learn_skill = exchange.offered_skill
        exchange_cards.append(
            {
                "exchange": exchange,
                "partner": partner,
                "teach_skill": teach_skill,
                "learn_skill": learn_skill,
            }
        )

    return render(request, "matching/my_exchanges.html", {"exchange_cards": exchange_cards})


@login_required
def accept_match_request(request, request_id):
    match_request = get_object_or_404(MatchRequest, pk=request_id, receiver=request.user)
    if request.method != "POST":
        return redirect("matching:requests")

    if match_request.status != MatchRequest.PENDING:
        messages.error(request, "Only pending requests can be accepted.")
        return redirect("matching:requests")

    try:
        match_request.accept(request.user)
    except PermissionDenied:
        messages.error(request, "Only the receiver can accept this request.")
    except ValidationError as error:
        messages.error(request, error.messages[0] if hasattr(error, "messages") else str(error))
    else:
        messages.success(request, "Request accepted.")
    return redirect("matching:requests")


@login_required
def decline_match_request(request, request_id):
    match_request = get_object_or_404(MatchRequest, pk=request_id, receiver=request.user)
    if request.method != "POST":
        return redirect("matching:requests")

    if match_request.status != MatchRequest.PENDING:
        messages.error(request, "Only pending requests can be declined.")
        return redirect("matching:requests")

    try:
        match_request.decline(request.user)
    except PermissionDenied:
        messages.error(request, "Only the receiver can decline this request.")
    else:
        notify_request_rejected(match_request)
        messages.success(request, "Request declined.")
    return redirect("matching:requests")


@login_required
def cancel_match_request(request, request_id):
    match_request = get_object_or_404(MatchRequest, pk=request_id, sender=request.user)
    if request.method != "POST":
        return redirect("matching:requests")

    if match_request.status != MatchRequest.PENDING:
        messages.error(request, "Only pending requests can be cancelled.")
        return redirect("matching:requests")

    try:
        match_request.cancel(request.user)
    except PermissionDenied:
        messages.error(request, "Only the sender can cancel this request.")
    else:
        messages.success(request, "Request cancelled.")
    return redirect("matching:requests")
