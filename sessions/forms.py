from django import forms
from django.core.exceptions import ValidationError

from .models import Session, SessionFeedback


def _display_name(user):
    return user.profile.full_name or user.get_full_name() or user.username


class SessionScheduleForm(forms.ModelForm):
    mentor_user = forms.ChoiceField(label="Mentor")

    class Meta:
        model = Session
        fields = [
            "title",
            "description",
            "scheduled_date",
            "scheduled_time",
            "duration_minutes",
            "format",
            "location",
            "meeting_link",
        ]
        widgets = {
            "scheduled_date": forms.DateInput(attrs={"type": "date"}),
            "scheduled_time": forms.TimeInput(attrs={"type": "time"}),
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, exchange=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.exchange = exchange
        if exchange:
            self.fields["mentor_user"].choices = [
                (exchange.requester_id, _display_name(exchange.requester)),
                (exchange.responder_id, _display_name(exchange.responder)),
            ]
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")

    def clean_duration_minutes(self):
        duration = self.cleaned_data["duration_minutes"]
        if duration <= 0:
            raise ValidationError("Duration must be positive.")
        return duration

    def clean_mentor_user(self):
        mentor_id = int(self.cleaned_data["mentor_user"])
        participant_ids = {self.exchange.requester_id, self.exchange.responder_id}
        if mentor_id not in participant_ids:
            raise ValidationError("Choose a mentor from this exchange.")
        return mentor_id


class SessionEditForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = [
            "title",
            "description",
            "scheduled_date",
            "scheduled_time",
            "duration_minutes",
            "format",
            "location",
            "meeting_link",
            "status",
        ]
        widgets = {
            "scheduled_date": forms.DateInput(attrs={"type": "date"}),
            "scheduled_time": forms.TimeInput(attrs={"type": "time"}),
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


class SessionCompleteForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = [
            "mentor_attendance",
            "learner_attendance",
            "topics_covered",
            "notes",
            "shared_resources",
            "assignments",
        ]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
            "topics_covered": forms.Textarea(attrs={"rows": 3}),
            "shared_resources": forms.Textarea(attrs={"rows": 3}),
            "assignments": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


class SessionFeedbackForm(forms.ModelForm):
    class Meta:
        model = SessionFeedback
        fields = ["rating", "comments", "tags"]
        widgets = {
            "rating": forms.RadioSelect(choices=[(value, f"{value} star") for value in range(1, 6)]),
            "comments": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name != "rating":
                field.widget.attrs.setdefault("class", "form-control")
