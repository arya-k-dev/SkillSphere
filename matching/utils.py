from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, Prefetch, Q

from matching.models import MatchRequest
from skills.models import Skill
from sessions.models import SessionFeedback


def normalize_text(value):
    return (value or "").strip().lower()


def quality_label(score):
    if score >= 80:
        return "Excellent Match"
    if score >= 60:
        return "Strong Match"
    if score >= 40:
        return "Good Match"
    return "Basic Match"


def user_display_name(user):
    profile = getattr(user, "profile", None)
    if profile and profile.full_name:
        return profile.full_name
    return user.get_full_name() or user.username


def get_match_request_state(current_user, other_user, offered_skill=None, requested_skill=None):
    active_request = (
        MatchRequest.objects.filter(
            sender=current_user,
            receiver=other_user,
            offered_skill=offered_skill,
            requested_skill=requested_skill,
            status__in=[MatchRequest.PENDING, MatchRequest.ACCEPTED],
        )
        .order_by("-updated_at", "-created_at", "-pk")
        .first()
    )
    if active_request:
        return {
            "request": active_request,
            "status": active_request.status,
        }
    return {
        "request": None,
        "status": None,
    }


def get_user_skill_groups(user):
    skills = list(getattr(user, "prefetched_skills", user.skills.all()))
    teach_skills = [skill for skill in skills if skill.skill_type == Skill.TEACH]
    learn_skills = [skill for skill in skills if skill.skill_type == Skill.LEARN]
    return teach_skills, learn_skills


def build_match_data(current_user, other_user):
    current_teach, current_learn = get_user_skill_groups(current_user)
    other_teach, other_learn = get_user_skill_groups(other_user)
    received_feedback = SessionFeedback.objects.filter(
        Q(session__mentor=other_user) | Q(session__learner=other_user)
    ).exclude(given_by=other_user)
    rating_summary = received_feedback.aggregate(average=Avg("rating"), total=Count("id"))

    score = 0
    reasons = []
    matched_partner_teach_skills = set()
    matched_partner_learn_skills = set()

    for wanted_skill in current_learn:
        wanted_title = normalize_text(wanted_skill.title)
        for teaching_skill in other_teach:
            if wanted_title and wanted_title == normalize_text(teaching_skill.title):
                score += 50
                matched_partner_teach_skills.add(teaching_skill.title)
                reasons.append(
                    f"{user_display_name(other_user)} can teach {teaching_skill.title}, which you want to learn."
                )
                break

    for teaching_skill in current_teach:
        teaching_title = normalize_text(teaching_skill.title)
        for wanted_skill in other_learn:
            if teaching_title and teaching_title == normalize_text(wanted_skill.title):
                score += 30
                matched_partner_learn_skills.add(wanted_skill.title)
                reasons.append(
                    f"You can teach {teaching_skill.title}, which {user_display_name(other_user)} wants to learn."
                )
                break

    current_categories = {normalize_text(skill.category) for skill in current_teach + current_learn}
    other_categories = {normalize_text(skill.category) for skill in other_teach + other_learn}
    shared_categories = current_categories.intersection(other_categories)
    if shared_categories:
        score += 10
        reasons.append("You share interest in the same skill category.")

    current_levels = {skill.level for skill in current_teach + current_learn if skill.level}
    other_levels = {skill.level for skill in other_teach + other_learn if skill.level}
    if current_levels.intersection(other_levels):
        score += 5
        reasons.append("Your skill levels line up well for an exchange.")

    current_profile = getattr(current_user, "profile", None)
    other_profile = getattr(other_user, "profile", None)
    current_location = normalize_text(getattr(current_profile, "location", ""))
    other_location = normalize_text(getattr(other_profile, "location", ""))
    if current_location and current_location == other_location:
        score += 5
        reasons.append("You are listed in the same location.")

    score = min(score, 100)

    return {
        "user": other_user,
        "score": score,
        "quality": quality_label(score),
        "teach_skills": other_teach,
        "learn_skills": other_learn,
        "reasons": reasons,
        "matched_teach_skills": sorted(matched_partner_teach_skills),
        "matched_learn_skills": sorted(matched_partner_learn_skills),
        "average_rating": rating_summary["average"],
        "rating_count": rating_summary["total"],
    }


def get_exchange_skill_pair(current_user, other_user):
    current_teach, current_learn = get_user_skill_groups(current_user)
    other_teach, other_learn = get_user_skill_groups(other_user)

    requested_skill = None
    offered_skill = None

    for wanted_skill in current_learn:
        wanted_title = normalize_text(wanted_skill.title)
        if any(wanted_title and wanted_title == normalize_text(skill.title) for skill in other_teach):
            requested_skill = wanted_skill
            break

    for teaching_skill in current_teach:
        teaching_title = normalize_text(teaching_skill.title)
        if any(teaching_title and teaching_title == normalize_text(skill.title) for skill in other_learn):
            offered_skill = teaching_skill
            break

    return offered_skill or (current_teach[0] if current_teach else None), requested_skill or (
        current_learn[0] if current_learn else None
    )


def calculate_match_score(current_user, other_user):
    return build_match_data(current_user, other_user)["score"]


def get_recommended_matches(current_user):
    User = get_user_model()
    skills_prefetch = Prefetch("skills", queryset=Skill.objects.order_by("title"))

    current_user = (
        User.objects.filter(pk=current_user.pk)
        .select_related("profile")
        .prefetch_related(skills_prefetch)
        .get()
    )

    users = (
        User.objects.exclude(pk=current_user.pk)
        .annotate(skill_count=Count("skills"))
        .filter(skill_count__gt=0)
        .select_related("profile")
        .prefetch_related(skills_prefetch)
    )

    matches = []
    seen_user_ids = set()
    for user in users:
        if user.pk in seen_user_ids:
            continue
        seen_user_ids.add(user.pk)

        match_data = build_match_data(current_user, user)
        if match_data["score"] > 0:
            offered_skill, requested_skill = get_exchange_skill_pair(current_user, user)
            match_data["request_state"] = get_match_request_state(
                current_user,
                user,
                offered_skill,
                requested_skill,
            )
            matches.append(match_data)

    return sorted(matches, key=lambda match: match["score"], reverse=True)
