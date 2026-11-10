# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Rockstar Events is a Django 5 event management app for `@teamrockstars.nl` users. Users sign up with username/email/password, verify by email (optional), then create events, register/unregister, see attendees, and manage a profile (username, avatar, password). SQLite, deployed on PythonAnywhere. `django-allauth` SSO for Microsoft is planned but not installed.

## Brand

- Primary yellow: `#FFE000`
- Dark: `#232323`

Defined as CSS variables `--yellow` and `--dark` in `events/templates/base.html`. Use these for any new UI elements.

## Commands

```bash
make setup                                          # first-time: venv, pip install, migrate
make dev                                            # dev server at http://localhost:8123 (not 8000)

.venv/bin/python manage.py makemigrations events    # after model changes
.venv/bin/python manage.py migrate
.venv/bin/python manage.py createsuperuser          # for /admin/
.venv/bin/python manage.py shell
.venv/bin/ruff check .                              # lint (ruff is in requirements.txt; no config file, defaults)
.venv/bin/python manage.py test events              # runs the suite; there are currently 0 tests
.venv/bin/python manage.py test events.tests.<ClassName>.<test_name>   # single test (once tests exist)
```

Note: `frontend/` contains only a stray Vite cache directory. There is no frontend app; ignore it.

## Architecture

Single Django project: `rockstar_events/` (settings, root urls) and one app, `events/`. Everything routes through `events/urls.py`, which is included at `/`.

**Models** (`events/models.py`): `Event` (organizer FK to User, optional `max_attendees`, `image`, M2M `tags`), `EventRegistration` (unique on event+user; `Event.registrations` is the attendee relation), `Profile` (1:1 to User, holds avatar), `Tag` (names are lowercased and stripped on save).

**Auth and signup flow** (`views.py`, `forms.py`):
- `poc_login` logs in by *email*: it looks up the username via `User.objects.filter(email__iexact=...)`, then calls `authenticate` with the password. The login view is still named `poc_login` from the old name-only POC.
- `signup` uses `RegistrationForm`, which rejects any email not ending in `@teamrockstars.nl` and creates the user with `is_active=False`.
- When `REQUIRE_EMAIL_VERIFICATION` is true, a signed token (`django.core.signing`, salt `email-verify`, 24h max age) is emailed. `verify_email` activates the user. When it is false, the user is still inactive, so activation is manual (admin).
- Email backend is chosen in `settings.py` from env: Brevo via `django-anymail` if `EMAIL_API_KEY` is set, Gmail-style SMTP if `EMAIL_HOST_USER` is set, otherwise console (emails print to the terminal in dev).

**Permissions:** views use `@login_required` (or `LoginRequiredMixin` on the class views). Edit and delete check `event.organizer == request.user` inline and return `HttpResponseForbidden`. Register and unregister are POST-only, plain HTML forms, no JavaScript.

**Event lists:** `EventListView` and `my_events` hide events by date, not time: they keep events whose `starts_at__date >= localdate()`, so an event disappears the day after it starts. The tag filter is a `?tags=` GET parameter that repeats.

**Forms and uploads** (`forms.py`): `EventForm` has a hidden `tags` CharField that takes comma-separated text; `save_tags()` does get-or-create and `set()`s the M2M. Images go through `compress_image()`, which re-encodes to JPEG at or under 250 KB. Avatars use `AvatarForm`, which also caps uploads at 5 MB. Capacity is enforced only in `register()` (`event.is_full`).

**Media and static:** settings use `whitenoise` with a manifest storage. `rockstar_events/urls.py` serves `MEDIA_URL` through `django.conf.urls.static.static()`, which only does anything when `DEBUG=True`. In production, media must be served by the host (PythonAnywhere).

**Templates:** all pages extend `events/templates/base.html`, which holds the nav and inline CSS. Feature pages live under `events/templates/events/`; auth-flow pages live under `events/templates/registration/`.

**Config:** `python-decouple` reads `.env` (see `.env.example`). Defaults in `settings.py` are dev-friendly (`DEBUG=True`, localhost hosts), so production needs `DEBUG=False`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, and `REQUIRE_EMAIL_VERIFICATION=True`. The deploy steps are in `README.md`.

## SSO upgrade path

Install `django-allauth`, add `allauth` to `INSTALLED_APPS`, configure the Microsoft provider, and set `LOGIN_URL = '/accounts/login/'`. `poc_login`, `signup`, `verify_email`, and `RegistrationForm`'s domain check are what allauth would replace; the rest of the app should not change.
