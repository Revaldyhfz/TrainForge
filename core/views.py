# core/views.py
# View functions for public pages, auth, and clients.

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Profile, UserRole, Client, ClientStatus
from .permissions import trainer_required, admin_required, get_user_role
from .models import Profile, UserRole, Client, ClientStatus, TrainingPlan, TrainingPlanStatus, Exercise

from datetime import datetime, date, timedelta
from .models import (
    Profile, UserRole, Client, ClientStatus,
    TrainingPlan, TrainingPlanStatus, Exercise,
    Appointment, AppointmentStatus,
)
from .calendar_helper import build_month_grid, get_prev_next_month

from .models import (
    Profile, UserRole, Client, ClientStatus,
    TrainingPlan, TrainingPlanStatus, Exercise,
    Appointment, AppointmentStatus,
    ProgressLog,
)

# Public pages and auth

def home(request):
    if request.user.is_authenticated:
        role = get_user_role(request.user)
        if role == UserRole.ADMIN:
            return redirect('admin_overview')
        return redirect('dashboard')
    return render(request, 'core/home.html')


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')

        if not username or not email or not password:
            messages.error(request, 'All fields are required.')
            return render(request, 'core/register.html')

        if password != password_confirm:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'core/register.html')

        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
            return render(request, 'core/register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
            return render(request, 'core/register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return render(request, 'core/register.html')

        user = User.objects.create_user(username=username, email=email, password=password)
        Profile.objects.create(user=user, role=UserRole.TRAINER)

        login(request, user)
        return redirect('dashboard')

    return render(request, 'core/register.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=username, password=password)
        if user is None:
            messages.error(request, 'Invalid username or password.')
            return render(request, 'core/login.html')

        login(request, user)
        role = get_user_role(user)
        if role == UserRole.ADMIN:
            return redirect('admin_overview')
        return redirect('dashboard')

    return render(request, 'core/login.html')


def logout_view(request):
    logout(request)
    return redirect('home')

@trainer_required
def dashboard(request):
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    next_seven_days = today + timedelta(days=7)

    total_clients = Client.objects.filter(
        trainer=request.user,
        status=ClientStatus.ACTIVE,
    ).count()

    sessions_this_week = Appointment.objects.filter(
        trainer=request.user,
        scheduled_at__date__gte=week_start,
        scheduled_at__date__lte=week_end,
        status=AppointmentStatus.SCHEDULED,
    ).count()

    active_plans = TrainingPlan.objects.filter(
        trainer=request.user,
        status=TrainingPlanStatus.ACTIVE,
    ).count()

    todays_appointments = Appointment.objects.filter(
        trainer=request.user,
        scheduled_at__date=today,
    ).order_by('scheduled_at')

    upcoming_appointments = Appointment.objects.filter(
        trainer=request.user,
        scheduled_at__date__gt=today,
        scheduled_at__date__lte=next_seven_days,
        status=AppointmentStatus.SCHEDULED,
    ).order_by('scheduled_at')[:5]

    recent_clients = Client.objects.filter(
        trainer=request.user,
        status=ClientStatus.ACTIVE,
    ).order_by('-created_at')[:5]

    recent_logs = ProgressLog.objects.filter(
        client__trainer=request.user,
    ).select_related('client', 'exercise').order_by('-logged_at')[:5]

    return render(request, 'core/dashboard.html', {
        'active_nav': 'dashboard',
        'total_clients': total_clients,
        'sessions_this_week': sessions_this_week,
        'active_plans': active_plans,
        'todays_count': todays_appointments.count(),
        'todays_appointments': todays_appointments,
        'upcoming_appointments': upcoming_appointments,
        'recent_clients': recent_clients,
        'recent_logs': recent_logs,
    })

@trainer_required
def clients_list(request):
    clients = Client.objects.filter(trainer=request.user).order_by('name')
    return render(request, 'core/clients_list.html', {
        'active_nav': 'clients',
        'clients': clients,
    })


@trainer_required
def client_create(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        goals = request.POST.get('goals', '').strip()

        if not name or not email:
            messages.error(request, 'Name and email are required.')
            return render(request, 'core/client_form.html', {
                'active_nav': 'clients',
                'form_title': 'Add Client',
                'submit_label': 'Create Client',
                'client': None,
                'values': {'name': name, 'email': email, 'phone': phone, 'goals': goals},
            })

        Client.objects.create(
            trainer=request.user,
            name=name,
            email=email,
            phone=phone,
            goals=goals,
        )
        messages.success(request, 'Client created.')
        return redirect('clients_list')

    return render(request, 'core/client_form.html', {
        'active_nav': 'clients',
        'form_title': 'Add Client',
        'submit_label': 'Create Client',
        'client': None,
        'values': {},
    })


@trainer_required
def client_edit(request, client_id):
    client = get_object_or_404(Client, id=client_id, trainer=request.user)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        goals = request.POST.get('goals', '').strip()

        if not name or not email:
            messages.error(request, 'Name and email are required.')
            return render(request, 'core/client_form.html', {
                'active_nav': 'clients',
                'form_title': 'Edit Client',
                'submit_label': 'Save Changes',
                'client': client,
                'values': {'name': name, 'email': email, 'phone': phone, 'goals': goals},
            })

        client.name = name
        client.email = email
        client.phone = phone
        client.goals = goals
        client.save()
        messages.success(request, 'Client updated.')
        return redirect('clients_list')

    return render(request, 'core/client_form.html', {
        'active_nav': 'clients',
        'form_title': 'Edit Client',
        'submit_label': 'Save Changes',
        'client': client,
        'values': {
            'name': client.name,
            'email': client.email,
            'phone': client.phone,
            'goals': client.goals,
        },
    })


@trainer_required
def client_archive(request, client_id):
    client = get_object_or_404(Client, id=client_id, trainer=request.user)

    if request.method == 'POST':
        client.status = ClientStatus.INACTIVE
        client.save()
        messages.success(request, 'Client archived.')

    return redirect('clients_list')


@trainer_required
def client_restore(request, client_id):
    client = get_object_or_404(Client, id=client_id, trainer=request.user)

    if request.method == 'POST':
        client.status = ClientStatus.ACTIVE
        client.save()
        messages.success(request, 'Client restored.')

    return redirect('clients_list')


# Training plans

@trainer_required
def plans_list(request):
    plans = TrainingPlan.objects.filter(trainer=request.user).order_by('-created_at')
    return render(request, 'core/plans_list.html', {
        'active_nav': 'plans',
        'plans': plans,
    })


@trainer_required
def plan_create(request):
    clients = Client.objects.filter(trainer=request.user, status=ClientStatus.ACTIVE).order_by('name')

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        client_id = request.POST.get('client_id', '')
        description = request.POST.get('description', '').strip()

        if not title or not client_id:
            messages.error(request, 'Title and client are required.')
            return render(request, 'core/plan_form.html', {
                'active_nav': 'plans',
                'form_title': 'New Training Plan',
                'submit_label': 'Create Plan',
                'plan': None,
                'clients': clients,
                'values': {'title': title, 'client_id': client_id, 'description': description},
            })

        client = get_object_or_404(Client, id=client_id, trainer=request.user)

        plan = TrainingPlan.objects.create(
            trainer=request.user,
            client=client,
            title=title,
            description=description,
        )
        messages.success(request, 'Training plan created.')
        return redirect('plan_edit', plan_id=plan.id)

    return render(request, 'core/plan_form.html', {
        'active_nav': 'plans',
        'form_title': 'New Training Plan',
        'submit_label': 'Create Plan',
        'plan': None,
        'clients': clients,
        'values': {},
    })


@trainer_required
def plan_edit(request, plan_id):
    plan = get_object_or_404(TrainingPlan, id=plan_id, trainer=request.user)
    clients = Client.objects.filter(trainer=request.user, status=ClientStatus.ACTIVE).order_by('name')

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        client_id = request.POST.get('client_id', '')
        description = request.POST.get('description', '').strip()

        if not title or not client_id:
            messages.error(request, 'Title and client are required.')
        else:
            client = get_object_or_404(Client, id=client_id, trainer=request.user)
            plan.title = title
            plan.client = client
            plan.description = description
            plan.save()
            messages.success(request, 'Plan updated.')
            return redirect('plan_edit', plan_id=plan.id)

    exercises = plan.exercises.all()

    return render(request, 'core/plan_form.html', {
        'active_nav': 'plans',
        'form_title': 'Edit Training Plan',
        'submit_label': 'Save Changes',
        'plan': plan,
        'clients': clients,
        'exercises': exercises,
        'values': {
            'title': plan.title,
            'client_id': plan.client_id,
            'description': plan.description,
        },
    })


@trainer_required
def plan_archive(request, plan_id):
    plan = get_object_or_404(TrainingPlan, id=plan_id, trainer=request.user)
    if request.method == 'POST':
        plan.status = TrainingPlanStatus.ARCHIVED
        plan.save()
        messages.success(request, 'Plan archived.')
    return redirect('plans_list')


@trainer_required
def plan_restore(request, plan_id):
    plan = get_object_or_404(TrainingPlan, id=plan_id, trainer=request.user)
    if request.method == 'POST':
        plan.status = TrainingPlanStatus.ACTIVE
        plan.save()
        messages.success(request, 'Plan restored.')
    return redirect('plans_list')


# Exercises (always within a plan)

@trainer_required
def exercise_create(request, plan_id):
    plan = get_object_or_404(TrainingPlan, id=plan_id, trainer=request.user)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        sets = request.POST.get('sets', '')
        reps = request.POST.get('reps', '')

        if not name or not sets or not reps:
            messages.error(request, 'Name, sets, and reps are required.')
            return render(request, 'core/exercise_form.html', {
                'active_nav': 'plans',
                'form_title': 'Add Exercise',
                'submit_label': 'Add Exercise',
                'plan': plan,
                'exercise': None,
                'values': {'name': name, 'description': description, 'sets': sets, 'reps': reps},
            })

        next_order = plan.exercises.count()
        Exercise.objects.create(
            training_plan=plan,
            name=name,
            description=description,
            sets=int(sets),
            reps=int(reps),
            duration_seconds=0,
            order_index=next_order,
        )
        messages.success(request, 'Exercise added.')
        return redirect('plan_edit', plan_id=plan.id)

    return render(request, 'core/exercise_form.html', {
        'active_nav': 'plans',
        'form_title': 'Add Exercise',
        'submit_label': 'Add Exercise',
        'plan': plan,
        'exercise': None,
        'values': {},
    })


@trainer_required
def exercise_edit(request, exercise_id):
    exercise = get_object_or_404(Exercise, id=exercise_id, training_plan__trainer=request.user)
    plan = exercise.training_plan

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        sets = request.POST.get('sets', '0')
        reps = request.POST.get('reps', '0')
        duration_seconds = request.POST.get('duration_seconds', '0')

        if not name:
            messages.error(request, 'Exercise name is required.')
        else:
            exercise.name = name
            exercise.description = description
            exercise.sets = int(sets or 0)
            exercise.reps = int(reps or 0)
            exercise.duration_seconds = int(duration_seconds or 0)
            exercise.save()
            messages.success(request, 'Exercise updated.')
            return redirect('plan_edit', plan_id=plan.id)

    return render(request, 'core/exercise_form.html', {
        'active_nav': 'plans',
        'form_title': 'Edit Exercise',
        'submit_label': 'Save Changes',
        'plan': plan,
        'exercise': exercise,
        'values': {
            'name': exercise.name,
            'description': exercise.description,
            'sets': exercise.sets,
            'reps': exercise.reps,
            'duration_seconds': exercise.duration_seconds,
        },
    })


@trainer_required
def exercise_delete(request, exercise_id):
    exercise = get_object_or_404(Exercise, id=exercise_id, training_plan__trainer=request.user)
    plan_id = exercise.training_plan.id

    if request.method == 'POST':
        exercise.delete()
        messages.success(request, 'Exercise removed.')

    return redirect('plan_edit', plan_id=plan_id)


# Appointments

@trainer_required
def appointments_list(request):
    today = date.today()
    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
    except ValueError:
        year, month = today.year, today.month

    appointments = Appointment.objects.filter(
        trainer=request.user,
        scheduled_at__year=year,
        scheduled_at__month=month,
    ).order_by('scheduled_at')

    upcoming = Appointment.objects.filter(
        trainer=request.user,
        scheduled_at__gte=datetime.now(),
        status=AppointmentStatus.SCHEDULED,
    ).order_by('scheduled_at')[:5]

    weeks = build_month_grid(year, month, appointments)
    (prev_year, prev_month), (next_year, next_month) = get_prev_next_month(year, month)

    return render(request, 'core/appointments_list.html', {
        'active_nav': 'appointments',
        'weeks': weeks,
        'upcoming': upcoming,
        'year': year,
        'month': month,
        'month_name': date(year, month, 1).strftime('%B'),
        'prev_year': prev_year,
        'prev_month': prev_month,
        'next_year': next_year,
        'next_month': next_month,
    })


@trainer_required
def appointment_create(request):
    clients = Client.objects.filter(trainer=request.user, status=ClientStatus.ACTIVE).order_by('name')

    if request.method == 'POST':
        client_id = request.POST.get('client_id', '')
        scheduled_date = request.POST.get('scheduled_date', '')
        scheduled_time = request.POST.get('scheduled_time', '')
        duration_minutes = request.POST.get('duration_minutes', '60')
        notes = request.POST.get('notes', '').strip()

        if not client_id or not scheduled_date or not scheduled_time:
            messages.error(request, 'Client, date, and time are required.')
            return render(request, 'core/appointment_form.html', {
                'active_nav': 'appointments',
                'form_title': 'Book Session',
                'submit_label': 'Book Session',
                'appointment': None,
                'clients': clients,
                'values': {
                    'client_id': client_id, 'scheduled_date': scheduled_date,
                    'scheduled_time': scheduled_time, 'duration_minutes': duration_minutes,
                    'notes': notes,
                },
            })

        client = get_object_or_404(Client, id=client_id, trainer=request.user)
        scheduled_at = datetime.strptime(f"{scheduled_date} {scheduled_time}", "%Y-%m-%d %H:%M")

        Appointment.objects.create(
            trainer=request.user,
            client=client,
            scheduled_at=scheduled_at,
            duration_minutes=int(duration_minutes or 60),
            notes=notes,
        )
        messages.success(request, 'Session booked.')
        return redirect('appointments_list')

    return render(request, 'core/appointment_form.html', {
        'active_nav': 'appointments',
        'form_title': 'Book Session',
        'submit_label': 'Book Session',
        'appointment': None,
        'clients': clients,
        'values': {'duration_minutes': 60},
    })


@trainer_required
def appointment_edit(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, trainer=request.user)
    clients = Client.objects.filter(trainer=request.user, status=ClientStatus.ACTIVE).order_by('name')

    if request.method == 'POST':
        client_id = request.POST.get('client_id', '')
        scheduled_date = request.POST.get('scheduled_date', '')
        scheduled_time = request.POST.get('scheduled_time', '')
        duration_minutes = request.POST.get('duration_minutes', '60')
        notes = request.POST.get('notes', '').strip()

        if not client_id or not scheduled_date or not scheduled_time:
            messages.error(request, 'Client, date, and time are required.')
        else:
            client = get_object_or_404(Client, id=client_id, trainer=request.user)
            appointment.client = client
            appointment.scheduled_at = datetime.strptime(f"{scheduled_date} {scheduled_time}", "%Y-%m-%d %H:%M")
            appointment.duration_minutes = int(duration_minutes or 60)
            appointment.notes = notes
            appointment.save()
            messages.success(request, 'Session updated.')
            return redirect('appointments_list')

    return render(request, 'core/appointment_form.html', {
        'active_nav': 'appointments',
        'form_title': 'Edit Session',
        'submit_label': 'Save Changes',
        'appointment': appointment,
        'clients': clients,
        'values': {
            'client_id': appointment.client_id,
            'scheduled_date': appointment.scheduled_at.strftime('%Y-%m-%d'),
            'scheduled_time': appointment.scheduled_at.strftime('%H:%M'),
            'duration_minutes': appointment.duration_minutes,
            'notes': appointment.notes,
        },
    })


@trainer_required
def appointment_cancel(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, trainer=request.user)
    if request.method == 'POST':
        appointment.status = AppointmentStatus.CANCELLED
        appointment.save()
        messages.success(request, 'Session cancelled.')
    return redirect('appointments_list')

# Progress logs

@trainer_required
def progress_list(request):
    clients = Client.objects.filter(trainer=request.user, status=ClientStatus.ACTIVE).order_by('name')

    selected_client_id = request.GET.get('client', '')
    selected_exercise_id = request.GET.get('exercise', '')

    selected_client = None
    exercises = []
    logs = []

    if selected_client_id:
        selected_client = get_object_or_404(Client, id=selected_client_id, trainer=request.user)
        # Show all exercises across all of this client's plans.
        exercises = Exercise.objects.filter(
            training_plan__client=selected_client,
            training_plan__trainer=request.user,
        ).order_by('name')

        log_query = ProgressLog.objects.filter(client=selected_client).order_by('-logged_at')
        if selected_exercise_id:
            log_query = log_query.filter(exercise_id=selected_exercise_id)
        logs = log_query

    return render(request, 'core/progress_list.html', {
        'active_nav': 'progress',
        'clients': clients,
        'exercises': exercises,
        'logs': logs,
        'selected_client': selected_client,
        'selected_client_id': selected_client_id,
        'selected_exercise_id': selected_exercise_id,
    })


@trainer_required
def progress_create(request):
    clients = Client.objects.filter(trainer=request.user, status=ClientStatus.ACTIVE).order_by('name')

    # Build a flat list of (exercise_id, "Plan Title — Exercise Name") so the form
    # can show ONE dropdown of exercises, scoped to this trainer.
    exercises = Exercise.objects.filter(
        training_plan__trainer=request.user,
    ).select_related('training_plan', 'training_plan__client').order_by('training_plan__client__name', 'name')

    if request.method == 'POST':
        client_id = request.POST.get('client_id', '')
        exercise_id = request.POST.get('exercise_id', '')
        logged_date = request.POST.get('logged_date', '')
        sets_completed = request.POST.get('sets_completed', '')
        reps_completed = request.POST.get('reps_completed', '')
        weight_kg = request.POST.get('weight_kg', '0')
        notes = request.POST.get('notes', '').strip()

        if not client_id or not exercise_id or not logged_date or not sets_completed or not reps_completed:
            messages.error(request, 'Client, exercise, date, sets, and reps are required.')
            return render(request, 'core/progress_form.html', {
                'active_nav': 'progress',
                'form_title': 'Log Session',
                'submit_label': 'Save Log',
                'log': None,
                'clients': clients,
                'exercises': exercises,
                'values': {
                    'client_id': client_id, 'exercise_id': exercise_id,
                    'logged_date': logged_date,
                    'sets_completed': sets_completed, 'reps_completed': reps_completed,
                    'weight_kg': weight_kg, 'notes': notes,
                },
            })

        client = get_object_or_404(Client, id=client_id, trainer=request.user)
        exercise = get_object_or_404(Exercise, id=exercise_id, training_plan__trainer=request.user)

        ProgressLog.objects.create(
            client=client,
            exercise=exercise,
            logged_at=datetime.strptime(logged_date, "%Y-%m-%d"),
            sets_completed=int(sets_completed),
            reps_completed=int(reps_completed),
            weight_kg=float(weight_kg or 0),
            notes=notes,
        )
        messages.success(request, 'Progress logged.')
        return redirect('progress_list')

    return render(request, 'core/progress_form.html', {
        'active_nav': 'progress',
        'form_title': 'Log Session',
        'submit_label': 'Save Log',
        'log': None,
        'clients': clients,
        'exercises': exercises,
        'values': {},
    })


@trainer_required
def progress_edit(request, log_id):
    log = get_object_or_404(ProgressLog, id=log_id, client__trainer=request.user)
    clients = Client.objects.filter(trainer=request.user, status=ClientStatus.ACTIVE).order_by('name')
    exercises = Exercise.objects.filter(
        training_plan__trainer=request.user,
    ).select_related('training_plan', 'training_plan__client').order_by('training_plan__client__name', 'name')

    if request.method == 'POST':
        client_id = request.POST.get('client_id', '')
        exercise_id = request.POST.get('exercise_id', '')
        logged_date = request.POST.get('logged_date', '')
        sets_completed = request.POST.get('sets_completed', '')
        reps_completed = request.POST.get('reps_completed', '')
        weight_kg = request.POST.get('weight_kg', '0')
        notes = request.POST.get('notes', '').strip()

        if not client_id or not exercise_id or not logged_date or not sets_completed or not reps_completed:
            messages.error(request, 'Client, exercise, date, sets, and reps are required.')
        else:
            client = get_object_or_404(Client, id=client_id, trainer=request.user)
            exercise = get_object_or_404(Exercise, id=exercise_id, training_plan__trainer=request.user)
            log.client = client
            log.exercise = exercise
            log.logged_at = datetime.strptime(logged_date, "%Y-%m-%d")
            log.sets_completed = int(sets_completed)
            log.reps_completed = int(reps_completed)
            log.weight_kg = float(weight_kg or 0)
            log.notes = notes
            log.save()
            messages.success(request, 'Log updated.')
            return redirect('progress_list')

    return render(request, 'core/progress_form.html', {
        'active_nav': 'progress',
        'form_title': 'Edit Log',
        'submit_label': 'Save Changes',
        'log': log,
        'clients': clients,
        'exercises': exercises,
        'values': {
            'client_id': log.client_id,
            'exercise_id': log.exercise_id,
            'logged_date': log.logged_at.strftime('%Y-%m-%d'),
            'sets_completed': log.sets_completed,
            'reps_completed': log.reps_completed,
            'weight_kg': log.weight_kg,
            'notes': log.notes,
        },
    })


@trainer_required
def progress_delete(request, log_id):
    log = get_object_or_404(ProgressLog, id=log_id, client__trainer=request.user)
    if request.method == 'POST':
        log.delete()
        messages.success(request, 'Log removed.')
    return redirect('progress_list')

# Admin pages

@admin_required
def admin_overview(request):
    return render(request, 'core/admin_overview.html')

