from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError
from django.db.models import Avg, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from decimal import Decimal

from matching.models import MatchRequest, SkillExchange

from .forms import SessionCompleteForm, SessionEditForm, SessionFeedbackForm, SessionScheduleForm
from .models import Session, SessionFeedback


def _display_name(user):
    return user.profile.full_name or user.get_full_name() or user.username


def _exchange_queryset(user):
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


def _session_queryset(user):
    return Session.objects.select_related(
        "exchange",
        "exchange__request",
        "mentor",
        "mentor__profile",
        "learner",
        "learner__profile",
    ).filter(Q(mentor=user) | Q(learner=user))


def _get_user_session(user, session_id):
    return get_object_or_404(_session_queryset(user), pk=session_id)


def _participant_ids(exchange):
    return {exchange.requester_id, exchange.responder_id}


@login_required
def schedule_session(request, exchange_id):
    exchange = get_object_or_404(_exchange_queryset(request.user), pk=exchange_id)
    initial_title = exchange.offered_skill.title if exchange.offered_skill else "Skill exchange session"
    form = SessionScheduleForm(request.POST or None, exchange=exchange, initial={"title": initial_title})

    if request.method == "POST" and form.is_valid():
        mentor_id = form.cleaned_data["mentor_user"]
        learner = exchange.responder if mentor_id == exchange.requester_id else exchange.requester
        mentor = exchange.requester if mentor_id == exchange.requester_id else exchange.responder
        session = form.save(commit=False)
        session.exchange = exchange
        session.request = exchange.request
        session.mentor = mentor
        session.learner = learner
        try:
            session.full_clean()
            session.save()
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, "Session scheduled.")
            return redirect("sessions:detail", session_id=session.pk)

    return render(request, "sessions/schedule_session.html", {"form": form, "exchange": exchange})


@login_required
def sessions_list(request):
    status = request.GET.get("status", "upcoming")
    sessions = _session_queryset(request.user)
    if status == "completed":
        sessions = sessions.filter(status=Session.COMPLETED)
    elif status == "cancelled":
        sessions = sessions.filter(status=Session.CANCELLED)
    else:
        status = "upcoming"
        sessions = sessions.filter(status__in=[Session.SCHEDULED, Session.IN_PROGRESS])
    sessions = list(sessions)
    for session in sessions:
        session.partner = session.partner_for(request.user)

    stats_source = _session_queryset(request.user)
    stats = {
        "completed_count": stats_source.filter(status=Session.COMPLETED).count(),
        "upcoming_count": stats_source.filter(status__in=[Session.SCHEDULED, Session.IN_PROGRESS]).count(),
        "hours_taught": stats_source.filter(mentor=request.user, status=Session.COMPLETED).aggregate(
            total=Sum("hours_taught")
        )["total"] or 0,
        "hours_learned": stats_source.filter(learner=request.user, status=Session.COMPLETED).aggregate(
            total=Sum("hours_learned")
        )["total"] or 0,
        "average_rating": SessionFeedback.objects.filter(session__in=stats_source).aggregate(avg=Avg("rating"))["avg"] or 0,
    }
    return render(request, "sessions/sessions_list.html", {"sessions": sessions, "active_status": status, "stats": stats})


@login_required
def session_detail(request, session_id):
    session = _get_user_session(request.user, session_id)
    session_feedback = session.feedback.select_related("given_by", "given_by__profile")
    your_feedback = session_feedback.filter(given_by=request.user).first()
    partner_feedback = session_feedback.exclude(given_by=request.user).first()
    feedback_given = your_feedback is not None
    feedback_count = session_feedback.count()
    return render(
        request,
        "sessions/session_detail.html",
        {
            "session": session,
            "partner": session.partner_for(request.user),
            "your_feedback": your_feedback,
            "partner_feedback": partner_feedback,
            "feedback_given": feedback_given,
            "feedback_count": feedback_count,
        },
    )


@login_required
def ratings_page(request):
    active_tab = request.GET.get("tab", "received")
    user_sessions = _session_queryset(request.user)
    feedback_queryset = SessionFeedback.objects.select_related(
        "session",
        "session__mentor",
        "session__mentor__profile",
        "session__learner",
        "session__learner__profile",
        "given_by",
        "given_by__profile",
    ).filter(session__in=user_sessions)

    ratings_given = list(feedback_queryset.filter(given_by=request.user))
    ratings_received = list(feedback_queryset.exclude(given_by=request.user))

    for feedback in ratings_given:
        feedback.partner = feedback.session.partner_for(request.user)
    for feedback in ratings_received:
        feedback.partner = feedback.given_by

    if active_tab not in ["received", "given"]:
        active_tab = "received"

    return render(
        request,
        "sessions/ratings.html",
        {
            "active_tab": active_tab,
            "ratings_given": ratings_given,
            "ratings_received": ratings_received,
        },
    )


@login_required
def edit_session(request, session_id):
    session = _get_user_session(request.user, session_id)
    if session.status in [Session.COMPLETED, Session.CANCELLED]:
        messages.error(request, "Completed or cancelled sessions cannot be edited.")
        return redirect("sessions:detail", session_id=session.pk)

    form = SessionEditForm(request.POST or None, instance=session)
    if request.method == "POST" and form.is_valid():
        edited_session = form.save(commit=False)
        try:
            edited_session.full_clean()
            edited_session.save()
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, "Session updated.")
            return redirect("sessions:detail", session_id=session.pk)

    return render(request, "sessions/schedule_session.html", {"form": form, "session": session, "is_edit": True})


@login_required
def cancel_session(request, session_id):
    session = _get_user_session(request.user, session_id)
    if request.method == "POST":
        if session.status in [Session.COMPLETED, Session.CANCELLED]:
            messages.error(request, "Completed or cancelled sessions cannot be cancelled.")
            return redirect("sessions:detail", session_id=session.pk)
        session.status = Session.CANCELLED
        session.save(update_fields=["status", "updated_at"])
        messages.success(request, "Session cancelled.")
    return redirect("sessions:detail", session_id=session.pk)


@login_required
def mark_session_complete(request, session_id):
    session = _get_user_session(request.user, session_id)
    if session.mentor != request.user:
        raise PermissionDenied("Only the mentor can mark this session complete.")
    if session.status == Session.CANCELLED:
        messages.error(request, "Cancelled sessions cannot be completed.")
        return redirect("sessions:detail", session_id=session.pk)
    if session.status == Session.COMPLETED:
        messages.info(request, "This session is already completed.")
        return redirect("sessions:detail", session_id=session.pk)

    form = SessionCompleteForm(request.POST or None, instance=session)
    if request.method == "POST" and form.is_valid():
        completed_session = form.save(commit=False)
        completed_session.status = Session.COMPLETED
        completed_session.completed_at = timezone.now()
        duration_hours = (Decimal(completed_session.duration_minutes) / Decimal("60")).quantize(Decimal("0.01"))
        completed_session.hours_taught = duration_hours if completed_session.mentor_attendance else Decimal("0.00")
        completed_session.hours_learned = duration_hours if completed_session.learner_attendance else Decimal("0.00")
        completed_session.save()
        from engagement.services import ensure_certificates_for_user

        ensure_certificates_for_user(completed_session.mentor)
        ensure_certificates_for_user(completed_session.learner)
        messages.success(request, "Session marked complete.")
        return redirect("sessions:detail", session_id=session.pk)

    return render(request, "sessions/complete_session.html", {"form": form, "session": session})


@login_required
def submit_session_feedback(request, session_id):
    session = _get_user_session(request.user, session_id)
    if not session.user_is_participant(request.user):
        raise PermissionDenied("Only session participants can submit feedback.")
    if session.status != Session.COMPLETED:
        messages.error(request, "Feedback opens after the session is completed.")
        return redirect("sessions:detail", session_id=session.pk)
    if session.feedback.filter(given_by=request.user).exists():
        messages.info(request, "You already submitted feedback for this session.")
        return redirect("sessions:detail", session_id=session.pk)

    form = SessionFeedbackForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        feedback = form.save(commit=False)
        feedback.session = session
        feedback.given_by = request.user
        try:
            feedback.full_clean()
            feedback.save()
        except (ValidationError, IntegrityError) as error:
            form.add_error(None, error)
        else:
            from engagement.services import ensure_certificates_for_user

            ensure_certificates_for_user(session.mentor)
            ensure_certificates_for_user(session.learner)
            messages.success(request, "Feedback submitted.")
            return redirect("sessions:detail", session_id=session.pk)

    return render(request, "sessions/feedback_form.html", {"form": form, "session": session})
