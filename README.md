# Rockstar Events

Event management web app. Create events, register, and see who's attending. Login with just your name (SSO can be added later via `django-allauth`).

## Stack

- **Framework** — Django 5
- **Database** — SQLite (Django ORM, zero config)
- **Auth** — Name-based session login for POC; `django-allauth` for SSO later
- **Admin** — Django admin at `/admin/` for managing users and events
- **Hosting** — PythonAnywhere ($5/month Hacker plan)

## Getting started

```bash
make setup   # creates venv, installs deps, runs migrations
make dev     # starts server at http://localhost:8000
```

Then open `http://localhost:8000`, enter your name, and you're in.

## Django admin

Create a superuser to access `/admin/`:

```bash
.venv/bin/python manage.py createsuperuser
```

## Environment variables

Copy `.env.example` to `.env` and fill in:

```
SECRET_KEY=change-me-to-a-long-random-string
DEBUG=True
```

## Deploying to PythonAnywhere

```bash
# In a PythonAnywhere Bash console:
git pull
.venv/bin/python manage.py migrate          # if models changed
.venv/bin/python manage.py collectstatic --noinput  # if static files changed
```

Then click **Reload** in the Web tab.

On first deploy, also set these in `.env` on PythonAnywhere:

```
SECRET_KEY=<long random string>
DEBUG=False
ALLOWED_HOSTS=<yourusername>.pythonanywhere.com
CSRF_TRUSTED_ORIGINS=https://<yourusername>.pythonanywhere.com
REQUIRE_EMAIL_VERIFICATION=True
```

## Adding SSO later (Microsoft Azure AD)

```bash
.venv/bin/pip install django-allauth
```

Then add `allauth` to `INSTALLED_APPS`, configure the Microsoft provider in `settings.py`, and set `LOGIN_URL = '/accounts/login/'`. The rest of the app is unchanged.
