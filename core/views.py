from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, Q, Sum
from django.shortcuts import redirect, render
from django.utils import timezone

from matching.models import MatchRequest, SkillExchange
from matching.utils import get_recommended_matches
from messaging.models import ChatThread
from sessions.models import Session, SessionFeedback
from skills.models import Skill

from .public_skills import PUBLIC_SKILLS, PUBLIC_SKILLS_BY_SLUG


def _display_name(user):
    profile = getattr(user, "profile", None)
    return (getattr(profile, "full_name", "") or user.get_full_name() or user.username).strip()


def _matches_user_query(user, query):
    query = query.lower()
    return query in _display_name(user).lower() or query in user.username.lower()


def home(request):
    User = get_user_model()
    avg_rating = SessionFeedback.objects.aggregate(avg=Avg("rating"))["avg"] or 0
    match_satisfaction = round((avg_rating / 5) * 100) if avg_rating else 0
    homepage_stats = {
        "skills_listed": Skill.objects.count(),
        "active_users": User.objects.filter(is_active=True).count(),
        "skill_exchanges": SkillExchange.objects.count(),
        "match_satisfaction": match_satisfaction,
    }
    recent_feedback = (
        SessionFeedback.objects.select_related(
            "given_by",
            "given_by__profile",
            "session",
            "session__mentor",
            "session__learner",
            "session__exchange",
            "session__exchange__requester",
            "session__exchange__responder",
            "session__exchange__offered_skill",
            "session__exchange__requested_skill",
        )
        .filter(session__status=Session.COMPLETED)
        .exclude(comments="")
        .order_by("-created_at")[:6]
    )
    learner_stories = []
    for feedback in recent_feedback:
        if not feedback.comments.strip():
            continue
        exchange = feedback.session.exchange
        if feedback.session.mentor_id == exchange.requester_id:
            mentor_skill = exchange.offered_skill
            learner_skill = exchange.requested_skill
        else:
            mentor_skill = exchange.requested_skill
            learner_skill = exchange.offered_skill
        learner_stories.append(
            {
                "comment": feedback.comments,
                "reviewer": feedback.given_by.profile.full_name
                or feedback.given_by.get_full_name()
                or feedback.given_by.username,
                "mentor_skill": mentor_skill.title if mentor_skill else "Skill exchange",
                "learner_skill": learner_skill.title if learner_skill else "Skill exchange",
                "session_title": feedback.session.title,
                "role": "Mentor Feedback" if feedback.given_by_id == feedback.session.mentor_id else "Learner Feedback",
                "rating": feedback.rating,
            }
        )
        if len(learner_stories) == 3:
            break

    return render(
        request,
        "core/home.html",
        {
            "public_skills": PUBLIC_SKILLS,
            "homepage_stats": homepage_stats,
            "learner_stories": learner_stories,
        },
    )


def explore_skills(request):
    return redirect("skills:browse")


@login_required
def explore_skill_detail(request, slug):
    public_skill = PUBLIC_SKILLS_BY_SLUG.get(slug)
    if not public_skill:
        return redirect("skills:browse")
    return redirect("skills:public_detail", slug=slug)


@login_required
def dashboard(request):
    if not getattr(request.user.profile, "is_onboarding_completed", True):
        return redirect("accounts:onboarding_profile")

    user_skills = Skill.objects.filter(user=request.user)
    recommended_matches = get_recommended_matches(request.user)[:4]
    request_queryset = MatchRequest.objects.select_related(
        "sender",
        "sender__profile",
        "receiver",
        "receiver__profile",
        "offered_skill",
        "requested_skill",
    )
    pending_received_requests = request_queryset.filter(
        receiver=request.user,
        status=MatchRequest.PENDING,
    )
    accepted_exchanges = SkillExchange.objects.select_related(
        "requester",
        "requester__profile",
        "responder",
        "responder__profile",
        "offered_skill",
        "requested_skill",
    ).filter(Q(requester=request.user) | Q(responder=request.user))
    active_threads = ChatThread.objects.select_related(
        "exchange",
        "exchange__request",
        "user_one",
        "user_one__profile",
        "user_two",
        "user_two__profile",
    ).filter(
        Q(user_one=request.user) | Q(user_two=request.user),
        is_active=True,
        exchange__request__status=MatchRequest.ACCEPTED,
    )
    recent_threads = []
    for thread in active_threads[:3]:
        thread.partner = thread.get_partner(request.user)
        recent_threads.append(thread)
    user_sessions = Session.objects.select_related(
        "mentor",
        "mentor__profile",
        "learner",
        "learner__profile",
    ).filter(Q(mentor=request.user) | Q(learner=request.user))
    upcoming_session_list = list(
        user_sessions.filter(status__in=[Session.SCHEDULED, Session.IN_PROGRESS]).order_by(
            "scheduled_date", "scheduled_time"
        )[:3]
    )
    for session in upcoming_session_list:
        session.partner = session.partner_for(request.user)
    completed_sessions_count = user_sessions.filter(status=Session.COMPLETED).count()
    upcoming_sessions_count = user_sessions.filter(status__in=[Session.SCHEDULED, Session.IN_PROGRESS]).count()
    pending_sessions_count = pending_received_requests.count()
    hours_taught = user_sessions.filter(mentor=request.user, status=Session.COMPLETED).aggregate(total=Sum("hours_taught"))[
        "total"
    ] or 0
    hours_learned = user_sessions.filter(learner=request.user, status=Session.COMPLETED).aggregate(
        total=Sum("hours_learned")
    )["total"] or 0
    session_average_rating = SessionFeedback.objects.filter(session__in=user_sessions).aggregate(avg=Avg("rating"))[
        "avg"
    ] or 0
    active_learning_skills = list(user_skills.filter(skill_type=Skill.LEARN)[:4])
    progress_skills = []
    for index, skill in enumerate(active_learning_skills):
        progress_skills.append(
            {
                "title": skill.title,
                "category": skill.category,
                "percent": min(88, 38 + (index * 14) + pending_received_requests.count() * 3),
            }
        )

    User = get_user_model()
    top_experts = (
        User.objects.exclude(pk=request.user.pk)
        .select_related("profile")
        .annotate(
            skill_count=Count("skills", distinct=True),
            exchange_count=Count("responded_skill_exchanges", distinct=True),
        )
        .filter(skill_count__gt=0)
        .order_by("-exchange_count", "-skill_count", "username")[:5]
    )

    recent_activity = []
    for skill in user_skills[:2]:
        recent_activity.append(
            {
                "label": "New skill added",
                "title": skill.title,
                "meta": skill.get_skill_type_display(),
            }
        )
    for match_request in request_queryset.filter(Q(sender=request.user) | Q(receiver=request.user))[:2]:
        recent_activity.append(
            {
                "label": match_request.get_status_display(),
                "title": "Exchange request",
                "meta": match_request.offered_skill.title if match_request.offered_skill else "Skill exchange",
            }
        )
    if accepted_exchanges.exists():
        recent_activity.insert(
            0,
            {
                "label": "Completed exchange",
                "title": "Skill exchange milestone",
                "meta": "Keep the momentum going",
            },
        )

    xp_balance = (user_skills.count() * 120) + (accepted_exchanges.count() * 240) + (
        pending_received_requests.count() * 30
    )
    today = timezone.localdate()
    week_start = today - timedelta(days=today.weekday())
    weekly_labels = []
    weekly_sessions = []
    weekly_hours = []
    for offset in range(7):
        day = week_start + timedelta(days=offset)
        day_sessions = user_sessions.filter(scheduled_date=day)
        day_totals = day_sessions.aggregate(taught=Sum("hours_taught"), learned=Sum("hours_learned"))
        weekly_labels.append(day.strftime("%a"))
        weekly_sessions.append(day_sessions.count())
        weekly_hours.append(float((day_totals["taught"] or 0) + (day_totals["learned"] or 0)))

    profile_fields = [
        request.user.profile.full_name,
        request.user.email,
        request.user.profile.headline,
        request.user.profile.bio,
        request.user.profile.location,
        request.user.profile.availability,
        request.user.profile.learning_goal,
    ]
    profile_completion = round((sum(1 for field in profile_fields if field) / len(profile_fields)) * 100)
    progress_items = [
        {
            "label": "Profile Completion",
            "value": f"{profile_completion}%",
            "percent": profile_completion,
            "helper": "Keep your profile fresh for better matches.",
        },
        {
            "label": "Skill Points",
            "value": xp_balance,
            "percent": min(100, round((xp_balance / 1200) * 100)) if xp_balance else 0,
            "helper": "Earned from skills, requests, and exchanges.",
        },
        {
            "label": "Exchanges Completed",
            "value": accepted_exchanges.count(),
            "percent": min(100, round((accepted_exchanges.count() / 8) * 100)) if accepted_exchanges.count() else 0,
            "helper": "Accepted exchanges and milestones.",
        },
        {
            "label": "Sessions Completed",
            "value": completed_sessions_count,
            "percent": min(100, round((completed_sessions_count / 10) * 100)) if completed_sessions_count else 0,
            "helper": "Completed learning sessions.",
        },
    ]
    average_rating = session_average_rating or min(5, 4 + (accepted_exchanges.count() * 0.1))
    context = {
        "teach_count": user_skills.filter(skill_type=Skill.TEACH).count(),
        "learn_count": user_skills.filter(skill_type=Skill.LEARN).count(),
        "total_count": user_skills.count(),
        "recent_skills": user_skills[:3],
        "recommended_matches": recommended_matches,
        "pending_received_requests_count": pending_received_requests.count(),
        "pending_received_requests": pending_received_requests[:3],
        "recent_requests": request_queryset.filter(receiver=request.user)[:3],
        "total_exchanges_count": accepted_exchanges.count(),
        "active_threads_count": active_threads.count(),
        "recent_threads": recent_threads,
        "upcoming_sessions": upcoming_session_list,
        "upcoming_sessions_count": upcoming_sessions_count,
        "completed_sessions_count": completed_sessions_count,
        "hours_taught": hours_taught,
        "hours_learned": hours_learned,
        "recent_activity": recent_activity[:5],
        "progress_skills": progress_skills,
        "top_experts": top_experts,
        "xp_balance": xp_balance,
        "average_rating": average_rating,
        "dashboard_charts": {
            "weekly": {
                "labels": weekly_labels,
                "sessions": weekly_sessions,
                "hours": weekly_hours,
            },
            "sessions": {
                "completed": completed_sessions_count,
                "upcoming": upcoming_sessions_count,
                "pending": pending_sessions_count,
            },
            "skills": {
                "teaching": user_skills.filter(skill_type=Skill.TEACH).count(),
                "learning": user_skills.filter(skill_type=Skill.LEARN).count(),
                "both": min(
                    user_skills.filter(skill_type=Skill.TEACH).count(),
                    user_skills.filter(skill_type=Skill.LEARN).count(),
                ),
            },
        },
        "progress_items": progress_items,
    }
    return render(request, "core/dashboard.html", context)


@login_required
def global_search(request):
    query = (request.GET.get("q") or "").strip()
    results = {
        "skills": [],
        "users": [],
        "sessions": [],
        "requests": [],
    }

    if query:
        User = get_user_model()
        results["skills"] = list(
            Skill.objects.select_related("user", "user__profile")
            .filter(Q(title__icontains=query) | Q(description__icontains=query))
            .order_by("title")[:5]
        )
        results["users"] = list(
            User.objects.select_related("profile")
            .exclude(pk=request.user.pk)
            .filter(
                Q(username__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(profile__full_name__icontains=query)
            )
            .order_by("username")[:5]
        )
        results["sessions"] = list(
            Session.objects.select_related("mentor", "mentor__profile", "learner", "learner__profile")
            .filter(Q(mentor=request.user) | Q(learner=request.user))
            .filter(Q(title__icontains=query) | Q(description__icontains=query))
            .order_by("-scheduled_date", "-scheduled_time")[:5]
        )

        request_candidates = (
            MatchRequest.objects.select_related(
                "sender",
                "sender__profile",
                "receiver",
                "receiver__profile",
                "offered_skill",
                "requested_skill",
            )
            .filter(Q(sender=request.user) | Q(receiver=request.user))
            .order_by("-updated_at")[:30]
        )
        exchange_candidates = (
            SkillExchange.objects.select_related(
                "requester",
                "requester__profile",
                "responder",
                "responder__profile",
                "offered_skill",
                "requested_skill",
            )
            .filter(Q(requester=request.user) | Q(responder=request.user))
            .order_by("-created_at")[:30]
        )

        request_results = []
        for match_request in request_candidates:
            partner = match_request.receiver if match_request.sender_id == request.user.pk else match_request.sender
            if _matches_user_query(partner, query):
                request_results.append(
                    {
                        "title": _display_name(partner),
                        "type": "Request",
                        "description": f"{match_request.get_status_display()} request",
                        "meta": f"{match_request.offered_skill.title if match_request.offered_skill else 'Skill'} <-> {match_request.requested_skill.title if match_request.requested_skill else 'Skill'}",
                        "url_name": "requests_list",
                    }
                )
            if len(request_results) == 5:
                break

        if len(request_results) < 5:
            for exchange in exchange_candidates:
                partner = exchange.responder if exchange.requester_id == request.user.pk else exchange.requester
                if _matches_user_query(partner, query):
                    request_results.append(
                        {
                            "title": _display_name(partner),
                            "type": "Exchange",
                            "description": "Accepted skill exchange",
                            "meta": f"{exchange.offered_skill.title if exchange.offered_skill else 'Skill'} <-> {exchange.requested_skill.title if exchange.requested_skill else 'Skill'}",
                            "url_name": "matching:exchanges",
                        }
                    )
                if len(request_results) == 5:
                    break
        results["requests"] = request_results

    has_results = any(results[group] for group in results)
    return render(
        request,
        "core/search_results.html",
        {
            "query": query,
            "results": results,
            "has_results": has_results,
        },
    )
