# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Rockstar Events is a Django event management app. Users log in with just their name (POC mode), create events, register for events, and see who's attending. SSO can be added later via `django-allauth`.

## Brand

- Primary yellow: `#FFE000`
- Dark: `#232323`

Defined as CSS variables `--yellow` and `--dark` in `events/templates/base.html`. Use these for any new UI elements.

## Commands

```bash
make setup                                          # first-time setup (venv + migrate)
make dev                                            # run dev server at http://localhost:8000

.venv/bin/python manage.py makemigrations events   # generate migration after model changes
.venv/bin/python manage.py migrate                 # apply migrations
.venv/bin/python manage.py createsuperuser         # create admin user
.venv/bin/python manage.py shell                   # Django shell
```

## Architecture

Single Django project with one app (`events`):

```
rockstar_events/   # Django settings package (settings.py, urls.py, wsgi.py)
events/            # main app
  models.py        # Event, EventRegistration (uses built-in User)
  views.py         # EventListView, EventDetailView, create_event, register, unregister, poc_login
  forms.py         # EventForm (ModelForm for Event)
  admin.py         # EventAdmin, EventRegistrationAdmin
  urls.py          # all URL patterns
  templates/
    base.html                    # shared layout, nav, inline CSS
    registration/login.html      # POC name-entry login
    events/event_list.html
    events/event_detail.html
    events/event_form.html
```

## Key patterns

- **Auth:** `poc_login` view calls `User.objects.get_or_create(username=name)` and `login(request, user)` — no password needed for POC. Protected views use `@login_required`.
- **Register/unregister:** plain HTML `<form method="post">` submissions, no JavaScript. `EventRegistration.unique_together` prevents duplicates.
- **Capacity check:** `Event.is_full` property compares `registrations.count()` to `max_attendees`. Checked in the `register` view and the detail template.
- **Admin:** `Event` and `EventRegistration` registered with `@admin.register`. Access at `/admin/` after `createsuperuser`.
- **Settings:** `SECRET_KEY` and `DEBUG` read from `.env` via `python-decouple`.

## SSO upgrade path

Install `django-allauth`, add to `INSTALLED_APPS`, configure the Microsoft provider, set `LOGIN_URL = '/accounts/login/'`. No other app code changes needed.
