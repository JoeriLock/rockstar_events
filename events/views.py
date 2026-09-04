from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core import signing
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DetailView, ListView

from .forms import AvatarForm, EventForm, RegistrationForm, UsernameForm
from .models import Event, EventRegistration, Profile, Tag

_TOKEN_SALT = "email-verify"
_TOKEN_MAX_AGE = 60 * 60 * 24  # 24 hours


def _make_token(user):
    return signing.dumps(user.pk, salt=_TOKEN_SALT)


def _verify_token(token):
    return signing.loads(token, salt=_TOKEN_SALT, max_age=_TOKEN_MAX_AGE)


class EventListView(LoginRequiredMixin, ListView):
    model = Event
    template_name = "events/event_list.html"
    context_object_name = "events"

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(starts_at__date__gte=timezone.localdate())
        selected = self.request.GET.getlist("tags")
        if selected:
            qs = qs.filter(tags__name__in=selected).distinct()
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["all_tags"] = Tag.objects.order_by("name")
        ctx["selected_tags"] = set(self.request.GET.getlist("tags"))
        return ctx


class EventDetailView(LoginRequiredMixin, DetailView):
    model = Event
    template_name = "events/event_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            ctx["is_registered"] = self.object.registrations.filter(user=self.request.user).exists()
        else:
            ctx["is_registered"] = False
        return ctx


@login_required
def create_event(request):
    if request.method == "POST":
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.organizer = request.user
            event.save()
            form.save_tags(event)
            return redirect("event_detail", pk=event.pk)
    else:
        form = EventForm()
    all_tags = list(Tag.objects.values_list("name", flat=True))
    return render(request, "events/event_form.html", {"form": form, "all_tags": all_tags})


@login_required
def delete_event(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if event.organizer != request.user:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Only the organiser can delete this event.")
    if request.method == "POST":
        event.delete()
        return redirect("event_list")
    return render(request, "events/event_confirm_delete.html", {"event": event})


@login_required
def edit_event(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if event.organizer != request.user:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Only the organiser can edit this event.")
    if request.method == "POST":
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            form.save_tags(event)
            return redirect("event_detail", pk=event.pk)
    else:
        form = EventForm(instance=event)
    all_tags = list(Tag.objects.values_list("name", flat=True))
    return render(request, "events/event_form.html", {"form": form, "event": event, "all_tags": all_tags})


@login_required
def register(request, pk):
    if request.method == "POST":
        event = get_object_or_404(Event, pk=pk)
        if not event.is_full:
            EventRegistration.objects.get_or_create(event=event, user=request.user)
    return redirect("event_detail", pk=pk)


@login_required
def unregister(request, pk):
    if request.method == "POST":
        event = get_object_or_404(Event, pk=pk)
        EventRegistration.objects.filter(event=event, user=request.user).delete()
    return redirect("event_detail", pk=pk)


@login_required
def my_events(request):
    registrations = (
        EventRegistration.objects.filter(user=request.user, event__starts_at__date__gte=timezone.localdate())
        .select_related("event")
        .order_by("event__starts_at")
    )
    return render(request, "events/my_events.html", {"registrations": registrations})


@login_required
def edit_profile(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST" and request.POST.get("form") == "profile":
        username_form = UsernameForm(request.POST, instance=request.user)
        avatar_form = AvatarForm(request.POST, request.FILES, instance=profile)
        if username_form.is_valid() and avatar_form.is_valid():
            username_form.save()
            avatar_form.save()
            messages.success(request, "Profile updated.")
            return redirect("edit_profile")
    else:
        username_form = UsernameForm(instance=request.user)
        avatar_form = AvatarForm(instance=profile)

    if request.method == "POST" and request.POST.get("form") == "password":
        password_form = PasswordChangeForm(request.user, request.POST)
        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Password updated.")
            return redirect("edit_profile")
    else:
        password_form = PasswordChangeForm(request.user)

    return render(request, "events/edit_profile.html", {
        "username_form": username_form,
        "avatar_form": avatar_form,
        "password_form": password_form,
    })


def poc_login(request):
    if request.user.is_authenticated:
        return redirect("event_list")
    error = None
    if request.method == "POST":
        from django.contrib.auth import authenticate
        email = request.POST.get("email", "")
        username = User.objects.filter(email__iexact=email).values_list("username", flat=True).first()
        user = authenticate(request, username=username, password=request.POST.get("password")) if username else None
        if user is not None:
            login(request, user)
            return redirect(request.GET.get("next", "event_list"))
        error = "Invalid email or password."
    return render(request, "registration/login.html", {"error": error, "email": request.POST.get("email", "")})


def poc_logout(request):
    logout(request)
    return redirect("poc_login")


def signup(request):
    if request.user.is_authenticated:
        return redirect("event_list")
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            if settings.REQUIRE_EMAIL_VERIFICATION:
                token = _make_token(user)
                verify_url = request.build_absolute_uri(reverse("verify_email", args=[token]))
                send_mail(
                    subject="Verify your Rockstar Events account",
                    message=f"Hi {user.username},\n\nClick the link below to verify your account:\n\n{verify_url}\n\nThis link expires in 24 hours.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                )
            return render(request, "registration/register_pending.html", {
                "email": user.email,
                "email_verification": settings.REQUIRE_EMAIL_VERIFICATION,
            })
    else:
        form = RegistrationForm()
    return render(request, "registration/register.html", {"form": form})


def verify_email(request, token):
    try:
        user_pk = _verify_token(token)
        user = User.objects.get(pk=user_pk)
        user.is_active = True
        user.save()
        return render(request, "registration/email_verified.html")
    except (signing.BadSignature, signing.SignatureExpired, User.DoesNotExist):
        return render(request, "registration/email_verify_invalid.html")
