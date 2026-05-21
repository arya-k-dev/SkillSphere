from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from skills.models import Skill

from .forms import (
    LearnSkillFormSet,
    OnboardingProfileForm,
    ProfileForm,
    RegistrationForm,
    TeachSkillFormSet,
)


def _sync_user_name_from_profile(user, full_name):
    full_name = (full_name or "").strip()
    if not full_name:
        return

    first_name, _, last_name = full_name.partition(" ")
    user.first_name = first_name
    user.last_name = last_name.strip()
    user.save(update_fields=["first_name", "last_name"])


def user_needs_onboarding(user):
    return user.is_authenticated and not getattr(user.profile, "is_onboarding_completed", True)


def register(request):
    if request.user.is_authenticated:
        if user_needs_onboarding(request.user):
            return redirect("accounts:onboarding_profile")
        return redirect("core:dashboard")

    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome to SkillSphere. Let's set up your profile.")
            return redirect("accounts:onboarding_profile")
    else:
        form = RegistrationForm()

    return render(request, "accounts/register.html", {"form": form})


@login_required
def profile_view(request):
    profile = request.user.profile
    return render(request, "accounts/profile_view.html", {"profile": profile})


@login_required
def profile_edit(request):
    profile = request.user.profile

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save()
            _sync_user_name_from_profile(request.user, profile.full_name)
            messages.success(request, "Your profile has been updated.")
            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=profile)

    return render(request, "accounts/profile_form.html", {"form": form})


@login_required
def onboarding_profile(request):
    profile = request.user.profile
    if profile.is_onboarding_completed:
        return redirect("core:dashboard")

    if request.method == "POST":
        form = OnboardingProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            profile = form.save()
            _sync_user_name_from_profile(request.user, profile.full_name)
            return redirect("accounts:onboarding_skills")
    else:
        form = OnboardingProfileForm(instance=profile)

    return render(request, "accounts/onboarding_profile.html", {"form": form})


def _skill_count(formset):
    return sum(1 for form in formset if getattr(form, "has_skill_data", False))


def _save_onboarding_skills(user, formset, skill_type):
    Skill.objects.filter(user=user, skill_type=skill_type).delete()
    skills = []
    for form in formset:
        if not getattr(form, "has_skill_data", False):
            continue
        skills.append(
            Skill(
                user=user,
                title=form.cleaned_data["title"].strip(),
                category=form.cleaned_data.get("category", "").strip(),
                description=form.cleaned_data.get("description", "").strip(),
                skill_type=skill_type,
                level=form.cleaned_data.get("level") or Skill.BEGINNER,
                mode=form.cleaned_data.get("mode") or Skill.ONLINE,
            )
        )
    Skill.objects.bulk_create(skills)


@login_required
def onboarding_skills(request):
    profile = request.user.profile
    if profile.is_onboarding_completed:
        return redirect("core:dashboard")

    if request.method == "POST":
        teach_formset = TeachSkillFormSet(request.POST, prefix="teach")
        learn_formset = LearnSkillFormSet(request.POST, prefix="learn")
        teach_valid = teach_formset.is_valid()
        learn_valid = learn_formset.is_valid()

        if teach_valid and learn_valid:
            teach_count = _skill_count(teach_formset)
            learn_count = _skill_count(learn_formset)
            if teach_count < 1:
                teach_formset.non_form_errors()
                messages.error(request, "Add at least one skill you can teach.")
            if learn_count < 1:
                learn_formset.non_form_errors()
                messages.error(request, "Add at least one skill you want to learn.")
            if teach_count >= 1 and learn_count >= 1:
                _save_onboarding_skills(request.user, teach_formset, Skill.TEACH)
                _save_onboarding_skills(request.user, learn_formset, Skill.LEARN)
                profile.is_onboarding_completed = True
                profile.save(update_fields=["is_onboarding_completed", "updated_at"])
                messages.success(request, "Your SkillSphere setup is complete.")
                return redirect("core:dashboard")
    else:
        teach_formset = TeachSkillFormSet(prefix="teach", initial=[{}])
        learn_formset = LearnSkillFormSet(prefix="learn", initial=[{}])

    return render(
        request,
        "accounts/onboarding_skills.html",
        {
            "teach_formset": teach_formset,
            "learn_formset": learn_formset,
        },
    )
