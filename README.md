# TrainForge

A personal training management application for individual trainers to manage clients, create custom training plans, schedule appointments, and track client progress over time.

## Tech Stack

- **Backend**: Django 5.2 (Python)
- **Database**: PostgreSQL 18
- **Frontend**: Tailwind CSS, vanilla JavaScript
- **Email**: Resend
- **AI**: OpenAI API for exercise suggestion generation
- **Calendar**: iCalendar format for appointment exports

## Prerequisites

- Python 3.13+
- PostgreSQL 18+ (or SQLite for development)
- pip (Python package manager)

## Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd trainforge-fresh
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create a `.env` file

Copy `.env.example` to `.env` and fill in the required values:

```bash
cp .env.example .env
```

Edit `.env` with your actual secrets (SECRET_KEY, DATABASE_URL, API keys).

### 5. Apply migrations

```bash
python manage.py migrate
```

### 6. Create a superuser (admin account)

```bash
python manage.py createsuperuser
```

Follow the prompts to set a username, email, and password.

### 7. Run the development server

```bash
python manage.py runserver
```

The app is now running at `http://localhost:8000/`.

## Accessing the App

- **Home page**: `http://localhost:8000/`
- **Admin**: `http://localhost:8000/admin/` (use superuser credentials)
- **Register**: `http://localhost:8000/register/` to create a trainer account
- **Login**: `http://localhost:8000/login/` to log in

## Test Accounts

The app uses Django's built-in user system. To test functionality:

1. Create a trainer account via `/register/` or using the `createsuperuser` command
2. Log in and start adding clients, plans, and appointments
3. The marker should create their own test accounts to verify features

## Environment Variables Required

See `.env.example` for the full list. Key variables:

- `SECRET_KEY`: Django secret key (generate via `django-insecure-...` pattern)
- `DEBUG`: Set to `False` for production
- `DATABASE_URL`: PostgreSQL connection string
- `OPENAI_API_KEY`: Your OpenAI API key (for AI exercise generation)
- `RESEND_API_KEY`: Your Resend email API key
- `EMAIL_FROM_ADDRESS`: Email address for sending plan/appointment notifications
- `EMAIL_FROM_NAME`: Display name for emails

## Project Structure

```
trainforge-fresh/
├── config/              # Django project settings and routing
│   ├── settings.py      # Main Django configuration
│   ├── urls.py          # Top-level URL routing
│   ├── asgi.py
│   └── wsgi.py
├── core/                # Main app: models, views, business logic
│   ├── models.py        # Database models (Client, TrainingPlan, Exercise, etc.)
│   ├── views.py         # View functions and route handlers
│   ├── urls.py          # App-specific URL routing
│   ├── admin.py         # Django admin registration
│   ├── permissions.py   # Role-based access control decorators
│   ├── ai_service.py    # OpenAI integration for plan generation
│   ├── email_service.py # Email sending via Resend
│   ├── ics_service.py   # iCalendar file generation for appointments
│   ├── calendar_helper.py # Month grid building for calendar view
│   └── migrations/      # Database schema versions
├── core/templates/      # Django HTML templates
│   ├── core/            # Page templates
│   ├── core/includes/   # Reusable template components
│   └── emails/          # Email templates
├── static/              # CSS, JavaScript, images (empty, using Tailwind CDN)
├── manage.py            # Django management command entry point
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
├── .gitignore           # Git ignore file
└── README.md            # This file
```

## Key Features for the Marker

### Client Management

- Add/edit/archive clients with profile details (age, height, weight, fitness level, goals)
- Track client availability preferences

### Training Plans

- Create custom training plans with multiple exercises
- AI-powered exercise suggestion using OpenAI API
- View plan details and exercise lists
- Email plans to clients in HTML format

### Exercises

- Create exercises with three types: reps-based, duration-based, distance-based
- Set sets/reps, duration (minutes), or distance (km) as appropriate
- Add descriptions and form cues

### Appointments

- Calendar view for scheduling sessions
- Book appointments with clients
- Automatic iCalendar (.ics) file generation
- Email appointment confirmation to clients

### Progress Tracking

- Log exercise performance (sets completed, reps, weight)
- Log body weight/measurements
- Filter by client and exercise
- View progress history over time

### Admin Dashboard

- View trainer subscriptions
- Search and manage trainers

## Production Notes

For production deployment:

- Set `DEBUG=False` in your `.env`
- Configure `SECRET_KEY` with a strong random value
- Use HTTPS and secure database connection
- Set `ALLOWED_HOSTS` appropriately
- Run `python manage.py collectstatic` to gather static files
- Use a production WSGI server (e.g., Gunicorn)

## Notes for the Marker

- The app emphasizes simplicity and clarity over advanced patterns
- All views use Django's built-in authentication and ORM
- Role-based access is enforced via decorator functions on views
- Templates are written in plain Django template language without custom tags
- Styling uses Tailwind CSS via CDN
- The project uses PostgreSQL; SQLite is also supported by default Django config

---

**Course**: INFS3202 · University of Queensland · 2026
