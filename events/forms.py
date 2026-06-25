import io
import os

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from .models import Event, Tag


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def clean_email(self):
        email = self.cleaned_data["email"]
        if not email.endswith("@teamrockstars.nl"):
            raise forms.ValidationError("Only @teamrockstars.nl email addresses are allowed.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.is_active = False  # inactive until email is verified
        if commit:
            user.save()
        return user


class EventForm(forms.ModelForm):
    tags = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
    )

    class Meta:
        model = Event
        fields = ["title", "description", "location", "starts_at", "ends_at", "max_attendees", "image", "tags"]
        widgets = {
            "starts_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "ends_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["starts_at"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["ends_at"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["ends_at"].required = False
        self.fields["max_attendees"].required = False
        if self.instance.pk:
            self.fields["tags"].initial = ",".join(
                self.instance.tags.values_list("name", flat=True)
            )

    def clean_image(self):
        image = self.cleaned_data.get("image")
        if not image or not hasattr(image, "read"):
            return image

        from PIL import Image

        img = Image.open(image)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        max_bytes = 250 * 1024
        quality = 85

        for quality in range(85, 5, -5):
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=quality, optimize=True)
            if buffer.tell() <= max_bytes:
                break

        while buffer.tell() > max_bytes:
            img = img.resize((img.width * 3 // 4, img.height * 3 // 4), Image.LANCZOS)
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=quality, optimize=True)

        name = os.path.splitext(image.name)[0] + ".jpg"
        return ContentFile(buffer.getvalue(), name=name)

    def save_tags(self, event):
        tag_names = [t.strip().lower() for t in self.cleaned_data.get("tags", "").split(",") if t.strip()]
        tags = [Tag.objects.get_or_create(name=name)[0] for name in tag_names]
        event.tags.set(tags)
