from django import forms

from .models import MatchRequest


class MatchRequestForm(forms.ModelForm):
    class Meta:
        model = MatchRequest
        fields = ["message"]
        widgets = {
            "message": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Share a short note about what you would like to learn or exchange.",
                }
            )
        }
