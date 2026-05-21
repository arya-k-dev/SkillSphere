from django import forms

from .models import Skill


class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ["title", "category", "skill_type", "level", "mode", "description"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
        }
