# TrainForge

A personal training management web application for personal trainers. Built for INFS3202 (Web Information Systems) at The University of Queensland.

TrainForge lets trainers manage clients, build training plans, schedule appointments, log progress, and generate AI-assisted exercise programs.

## Tech Stack

- **Backend**: Django 5.2 (Python 3.13)
- **Database**: PostgreSQL 18
- **Frontend**: Server-rendered Django templates with Tailwind CSS (CDN)
- **AI**: OpenAI gpt-5.4-mini (via API key)
- **Email**: Resend (with iCalendar `.ics` attachments)

## Prerequisites

- Python 3.13
- PostgreSQL 18
- An OpenAI API key (for AI exercise generation)
- A Resend API key (for email features)

## Setup

### 1. Clone and create a virtual environment

```bash
git clone https://github.com/Revaldyhfz/TrainForge.git
cd TrainForge
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Create the database

```bash
createdb trainforge
```

### 3. Configure environment variables

Copy `.env.example` to `.env` and fill in the values:

```bash
cp .env.example .env
```

Then edit `.env`. The most important ones:

- `SECRET_KEY` — generate one with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
- `DATABASE_URL` — your PostgreSQL connection string
- `OPENAI_API_KEY` — for AI features
- `RESEND_API_KEY` — for email features

### 4. Run migrations

```bash
python manage.py migrate
```

### 5. Create an admin user

```bash
python manage.py createsuperuser
```

After creating, log in to `http://localhost:8000/admin/` and create a `Profile` for this user with role set to `admin`. This grants access to the custom admin dashboard at `/admin-overview/`.

### 6. Run the development server

```bash
python manage.py runserver
```

Visit `http://localhost:8000/`.

## Test Accounts

The marker should register their own trainer account via `/register/`. Each new registration:

- Creates a User with role `trainer`
- Creates a default Free subscription valid for 1 year
- Redirects to the trainer dashboard

For admin access, follow Step 5 above to promote a superuser.

## Project Structure

```
trainforge/
├── config/                 # Django project settings
│   ├── settings.py         # Includes production security flags under `if not DEBUG`
│   └── urls.py
├── core/                   # Main app
│   ├── models.py           # All domain models
│   ├── views.py            # All view functions (function-based)
│   ├── urls.py
│   ├── admin.py            # Django Admin registration
│   ├── permissions.py      # Role-based access decorators
│   ├── ai_service.py       # OpenAI integration
│   ├── email_service.py    # Resend integration
│   ├── ics_service.py      # iCalendar file generation
│   ├── calendar_helper.py  # Month grid builder for appointments
│   ├── migrations/
│   └── templates/
│       ├── core/           # Page templates
│       │   └── includes/   # Reusable partials (header, footer, nav)
│       └── emails/         # Email templates
├── manage.py
├── requirements.txt
├── .env.example
└── README.md
```

## Key Features

### Trainer features

- **Clients** — full CRUD with soft-delete (archive/restore)
- **Training Plans** — full CRUD with nested Exercises
- **Exercises** — three types: reps-based, duration-based, distance-based
- **Appointments** — calendar view with month navigation
- **Progress Logs** — per-exercise performance tracking
- **Body Weight** — inline weight tracking on the progress page
- **AI Exercise Generator** — conversational refinement loop using OpenAI
- **Email Plans** — send a training plan to a client
- **Email Appointments** — auto-send a session confirmation with `.ics` attachment

### Admin features

- Custom admin overview at `/admin-overview/` with stats and paginated subscription table
- Django Admin at `/admin/` for full CRUD on all models

## Security Notes

- Passwords hashed with Django's default `pbkdf2_sha256` (salted, 600,000 iterations, OWASP-compliant)
- CSRF protection on every form
- Role-based access via `@trainer_required` and `@admin_required` decorators
- Per-trainer data isolation: every query filters by `trainer=request.user`; cross-trainer access returns 404
- SQL injection protection via Django ORM (parameterised queries throughout)
- Secrets loaded from environment variables; `.env` is gitignored
- Production-only security flags (HTTPS redirect, HSTS, secure cookies, X-Frame-Options) wrapped in `if not DEBUG`

## Accessibility Notes

The interface targets WCAG 2.1 Level AA:

- Semantic HTML throughout (`<main>`, `<nav>`, `<aside>`, `<header>`, `<footer>`)
- Skip-to-content link on every page (visible on keyboard focus)
- All form labels programmatically bound to inputs via matching `for` and `id` attributes
- Flash messages announced via `role="status" aria-live="polite"`
- Decorative SVGs hidden from screen readers via `aria-hidden="true"`
- Icon-only buttons (hamburger toggle) have descriptive `aria-label`
- Visible focus states on all interactive elements via `:focus-visible`
- Mobile responsive with hamburger sidebar toggle below 768px
- Confirmation prompts on all destructive actions and irreversible operations (email sending)

## Notes for Marker

- The AI feature uses OpenAI's `gpt-5.4-mini` model with `response_format=json_object` for structured output. The conversational refinement loop is in `core/views.py` (`ai_chat` view) and `core/ai_service.py`.
- Free tier of Resend can only send emails to the email registered with the Resend account, so test client emails may need to use that address.
- Subscriptions belong to trainers and represent the trainer's SaaS access tier. They are admin-managed metadata and do not currently gate trainer features (out of scope for the rubric).
- The data model uses soft-delete (archive/restore) for top-level entities (clients, plans, subscriptions) and hard-delete for sub-entities (exercises, progress logs, appointments — cancel preserves history).

## License

This project was built for academic assessment at The University of Queensland and is not licensed for redistribution.
