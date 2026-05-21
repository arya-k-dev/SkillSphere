from django import forms
from django.forms import formset_factory
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from skills.models import Skill

from .models import Profile


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
        ]


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["full_name", "headline", "bio", "location", "availability", "learning_goal", "role"]
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 5}),
            "learning_goal": forms.Textarea(attrs={"rows": 4}),
        }


class OnboardingProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["full_name", "bio", "location", "availability", "learning_goal"]
        labels = {
            "full_name": "Full name",
            "learning_goal": "Learning goal",
        }
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 4}),
            "learning_goal": forms.Textarea(attrs={"rows": 4}),
        }


class OnboardingSkillForm(forms.Form):
    title = forms.CharField(label="Skill name", max_length=120, required=False)
    category = forms.CharField(max_length=80, required=False)
    description = forms.CharField(
        label="Description",
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
    )
    level = forms.ChoiceField(choices=[("", "Select level"), *Skill.LEVEL_CHOICES], required=False)
    mode = forms.ChoiceField(choices=[("", "Select mode"), *Skill.MODE_CHOICES], required=False)

    def clean(self):
        cleaned_data = super().clean()
        has_any_value = any(
            cleaned_data.get(field)
            for field in ["title", "category", "description", "level", "mode"]
        )
        if has_any_value and not cleaned_data.get("title"):
            self.add_error("title", "Add a skill name or remove this row.")
        return cleaned_data

    @property
    def has_skill_data(self):
        return bool(self.cleaned_data.get("title")) and not self.cleaned_data.get("DELETE", False)


TeachSkillFormSet = formset_factory(OnboardingSkillForm, extra=0, can_delete=True, min_num=1, validate_min=False)
LearnSkillFormSet = formset_factory(OnboardingSkillForm, extra=0, can_delete=True, min_num=1, validate_min=False)
