# core/views.py
# View functions for public pages, auth, and clients.

from datetime import datetime, date, timedelta
import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator

from .models import (
    Profile, UserRole,
    Client, ClientStatus, ClientFitnessLevel,
    TrainingPlan, TrainingPlanStatus,
    Exercise, ExerciseType,
    Appointment, AppointmentStatus,
    ProgressLog, BodyMeasurement,
    Subscription, SubscriptionStatus, SubscriptionPlanType,
)
from .permissions import trainer_required, admin_required, get_user_role
from .email_service import send_appointment_email, send_training_plan_email
from .calendar_helper import build_month_grid, get_prev_next_month
from .ai_service import generate_exercises, build_progress_summary
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

        # Give every new trainer a free 1-year subscription by default.
        Subscription.objects.create(
            trainer=user,
            plan_type=SubscriptionPlanType.FREE,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
        )

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
        age = request.POST.get('age', '').strip()
        height_cm = request.POST.get('height_cm', '').strip()
        weight_kg = request.POST.get('weight_kg', '').strip()
        fitness_level = request.POST.get('fitness_level', '').strip()

        if not name or not email:
            messages.error(request, 'Name and email are required.')
            return render(request, 'core/client_form.html', {
                'active_nav': 'clients',
                'form_title': 'Add Client',
                'submit_label': 'Create Client',
                'client': None,
                'values': {
                    'name': name, 'email': email, 'phone': phone, 'goals': goals,
                    'age': age, 'height_cm': height_cm, 'weight_kg': weight_kg,
                    'fitness_level': fitness_level,
                },
            })

        Client.objects.create(
            trainer=request.user,
            name=name,
            email=email,
            phone=phone,
            goals=goals,
            age=int(age) if age else None,
            height_cm=int(height_cm) if height_cm else None,
            weight_kg=float(weight_kg) if weight_kg else None,
            fitness_level=fitness_level,
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
        age = request.POST.get('age', '').strip()
        height_cm = request.POST.get('height_cm', '').strip()
        weight_kg = request.POST.get('weight_kg', '').strip()
        fitness_level = request.POST.get('fitness_level', '').strip()

        if not name or not email:
            messages.error(request, 'Name and email are required.')
            return render(request, 'core/client_form.html', {
                'active_nav': 'clients',
                'form_title': 'Edit Client',
                'submit_label': 'Save Changes',
                'client': client,
                'values': {
                    'name': name, 'email': email, 'phone': phone, 'goals': goals,
                    'age': age, 'height_cm': height_cm, 'weight_kg': weight_kg,
                    'fitness_level': fitness_level,
                },
            })

        client.name = name
        client.email = email
        client.phone = phone
        client.goals = goals
        client.age = int(age) if age else None
        client.height_cm = int(height_cm) if height_cm else None
        client.weight_kg = float(weight_kg) if weight_kg else None
        client.fitness_level = fitness_level
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
            'age': client.age or '',
            'height_cm': client.height_cm or '',
            'weight_kg': client.weight_kg or '',
            'fitness_level': client.fitness_level,
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
def plan_detail(request, plan_id):
    plan = get_object_or_404(TrainingPlan, id=plan_id, trainer=request.user)
    exercises = plan.exercises.all()
    return render(request, 'core/plan_detail.html', {
        'active_nav': 'plans',
        'plan': plan,
        'exercises': exercises,
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

@trainer_required
def plan_send_email(request, plan_id):
    plan = get_object_or_404(TrainingPlan, id=plan_id, trainer=request.user)

    if request.method == 'POST':
        if plan.exercises.count() == 0:
            messages.error(request, 'Cannot send a plan with no exercises.')
            return redirect('plan_detail', plan_id=plan.id)

        try:
            send_training_plan_email(plan, plan.client.email)
            messages.success(request, f'Plan emailed to {plan.client.name}.')
        except Exception as e:
            messages.error(request, f'Email failed: {str(e)}')

    return redirect('plan_detail', plan_id=plan.id)

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
        exercise_type = request.POST.get('exercise_type', ExerciseType.REPS)

        if not name:
            messages.error(request, 'Exercise name is required.')
        else:
            kwargs = _exercise_kwargs_from_post(exercise_type, request.POST)
            exercise.name = name
            exercise.description = description
            exercise.exercise_type = exercise_type
            exercise.sets = kwargs.get('sets')
            exercise.reps = kwargs.get('reps')
            exercise.duration_minutes = kwargs.get('duration_minutes')
            exercise.distance_km = kwargs.get('distance_km')
            exercise.save()
            messages.success(request, 'Exercise updated.')
            return redirect('plan_edit', plan_id=plan.id)

    values = {
        'name': exercise.name,
        'description': exercise.description,
        'exercise_type': exercise.exercise_type,
        'sets': exercise.sets,
        'reps': exercise.reps,
        'duration_minutes': exercise.duration_minutes,
        'distance_km': exercise.distance_km,
    }
    return render(request, 'core/exercise_form.html',
                  _exercise_form_context(plan, exercise, 'Edit Exercise', 'Save Changes', values))

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

        appointment = Appointment.objects.create(
            trainer=request.user,
            client=client,
            scheduled_at=scheduled_at,
            duration_minutes=int(duration_minutes or 60),
            notes=notes,
        )

        try:
            send_appointment_email(appointment)
            messages.success(request, f'Session booked. Confirmation emailed to {client.name}.')
        except Exception as e:
            messages.warning(request, f'Session booked but email failed: {str(e)}')

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

    selected_client_id = request.GET.get('client_id', '')
    selected_exercise_id = request.GET.get('exercise_id', '')
    selected_client = None
    exercises = []
    logs = []
    body_measurements = []

    if selected_client_id:
        selected_client = get_object_or_404(Client, id=selected_client_id, trainer=request.user)
        exercises = Exercise.objects.filter(
            training_plan__client=selected_client, training_plan__trainer=request.user
        ).select_related('training_plan').order_by('training_plan__title', 'order_index')

        body_measurements = BodyMeasurement.objects.filter(client=selected_client).order_by('-logged_at')[:10]

        log_qs = ProgressLog.objects.filter(client=selected_client).select_related('exercise')
        if selected_exercise_id:
            log_qs = log_qs.filter(exercise_id=selected_exercise_id)
        logs = log_qs.order_by('-logged_at')

    return render(request, 'core/progress_list.html', {
        'active_nav': 'progress',
        'clients': clients,
        'exercises': exercises,
        'logs': logs,
        'body_measurements': body_measurements,
        'selected_client': selected_client,
        'selected_client_id': selected_client_id,
        'selected_exercise_id': selected_exercise_id,
    })

@trainer_required
def body_weight_log(request):
    if request.method == 'POST':
        client_id = request.POST.get('client_id', '')
        weight_kg = request.POST.get('weight_kg', '').strip()
        logged_at = request.POST.get('logged_at', '').strip()

        if not client_id or not weight_kg or not logged_at:
            messages.error(request, 'Client, weight, and date are required.')
        else:
            client = get_object_or_404(Client, id=client_id, trainer=request.user)
            BodyMeasurement.objects.create(
                client=client,
                weight_kg=weight_kg,
                logged_at=logged_at,
            )
            messages.success(request, 'Body weight logged.')
            return redirect(f"/progress/?client_id={client.id}")

    return redirect('progress_list')


@trainer_required
def body_weight_delete(request, measurement_id):
    measurement = get_object_or_404(BodyMeasurement, id=measurement_id, client__trainer=request.user)
    client_id = measurement.client.id

    if request.method == 'POST':
        measurement.delete()
        messages.success(request, 'Body weight entry removed.')

    return redirect(f"/progress/?client_id={client_id}")

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

# AI training plan generation

@trainer_required
def ai_questionnaire(request, plan_id):
    plan = get_object_or_404(TrainingPlan, id=plan_id, trainer=request.user)

    if request.method == 'POST':
        questionnaire = {
            'muscle_groups': request.POST.get('muscle_groups', '').strip(),
            'session_duration': request.POST.get('session_duration', '').strip(),
            'goal': request.POST.get('goal', '').strip(),
            'target_date': request.POST.get('target_date', '').strip(),
            'equipment': request.POST.get('equipment', '').strip(),
        }

        if not all(questionnaire.values()):
            messages.error(request, 'All fields are required.')
            return render(request, 'core/ai_questionnaire.html', {
                'active_nav': 'plans',
                'plan': plan,
                'values': questionnaire,
            })

        # Store questionnaire in session and trigger first AI call.
        request.session['ai_plan_id'] = plan.id
        request.session['ai_questionnaire'] = questionnaire
        request.session['ai_conversation'] = []

        return redirect('ai_chat', plan_id=plan.id)

    return render(request, 'core/ai_questionnaire.html', {
        'active_nav': 'plans',
        'plan': plan,
        'values': {},
    })


@trainer_required
def ai_chat(request, plan_id):
    plan = get_object_or_404(TrainingPlan, id=plan_id, trainer=request.user)

    # Session guard — must have completed the questionnaire first.
    if request.session.get('ai_plan_id') != plan.id or 'ai_questionnaire' not in request.session:
        return redirect('ai_questionnaire', plan_id=plan.id)

    questionnaire = request.session['ai_questionnaire']
    conversation = request.session.get('ai_conversation', [])

    # Handle the "Complete" action — append AI's exercises to the plan.
    if request.method == 'POST' and request.POST.get('action') == 'complete':
        last_exercises = request.session.get('ai_last_exercises', [])
        next_order = plan.exercises.count()

        saved_count = 0
        for i, ex in enumerate(last_exercises):
            ex_type = ex.get('exercise_type', 'reps')
            sets = _int_or_none(ex.get('sets'))
            reps = _int_or_none(ex.get('reps'))
            duration = _int_or_none(ex.get('duration_minutes'))
            distance = _float_or_none(ex.get('distance_km'))

            # Validate: at least one type-relevant field must be filled.
            if ex_type == 'reps' and not (sets and reps):
                continue
            if ex_type == 'duration' and not (sets and duration):
                continue
            if ex_type == 'distance' and not distance:
                continue

            Exercise.objects.create(
                training_plan=plan,
                name=ex.get('name', 'Untitled'),
                description=ex.get('description', ''),
                exercise_type=ex_type,
                sets=sets,
                reps=reps,
                duration_minutes=duration,
                distance_km=distance,
                order_index=next_order + saved_count,
            )
            saved_count += 1

        plan.generated_by_ai = True
        plan.save()

        # Clean up session.
        for key in ('ai_plan_id', 'ai_questionnaire', 'ai_conversation', 'ai_last_exercises', 'ai_last_message'):
            request.session.pop(key, None)

        if saved_count < len(last_exercises):
            messages.warning(request, f'{saved_count} exercises added. {len(last_exercises) - saved_count} skipped due to incomplete data.')
        else:
            messages.success(request, f'{saved_count} exercises added.')
        return redirect('plan_edit', plan_id=plan.id)
    # Handle the "Refine" action — send feedback to AI.
    refinement_feedback = None
    if request.method == 'POST' and request.POST.get('action') == 'refine':
        refinement_feedback = request.POST.get('feedback', '').strip()

    # Run the AI call (first load OR refinement).
    if request.method == 'POST' or 'ai_last_message' not in request.session:
        try:
            result = generate_exercises(
                plan=plan,
                questionnaire=questionnaire,
                client_obj=plan.client,
                progress_summary=build_progress_summary(plan.client),
                conversation_history=conversation,
                refinement_feedback=refinement_feedback,
            )

            # Update conversation history with this turn.
            new_history = list(conversation)
            if refinement_feedback:
                new_history.append({"role": "user", "content": f"Feedback: {refinement_feedback}"})
            new_history.append({"role": "assistant", "content": result['assistant_response']})

            request.session['ai_conversation'] = new_history
            request.session['ai_last_message'] = result['message']
            request.session['ai_last_exercises'] = result['exercises']

        except json.JSONDecodeError:
            messages.error(request, 'AI returned an unexpected format. Please try again.')
        except Exception as e:
            messages.error(request, f'AI generation failed: {str(e)}')

    return render(request, 'core/ai_chat.html', {
        'active_nav': 'plans',
        'plan': plan,
        'ai_message': request.session.get('ai_last_message', ''),
        'ai_exercises': request.session.get('ai_last_exercises', []),
        'questionnaire': questionnaire,
    })
    
# Admin pages

@admin_required
def admin_overview(request):

    search = request.GET.get('search', '').strip()

    subscriptions = Subscription.objects.select_related('trainer').order_by('-created_at')
    if search:
        subscriptions = subscriptions.filter(
            trainer__username__icontains=search,
        ) | subscriptions.filter(
            trainer__email__icontains=search,
        )

    paginator = Paginator(subscriptions, 10)
    page_number = request.GET.get('page', 1)
    page = paginator.get_page(page_number)

    total_trainers = User.objects.filter(profile__role=UserRole.TRAINER).count()
    active_subs = Subscription.objects.filter(status=SubscriptionStatus.ACTIVE).count()
    archived_subs = Subscription.objects.filter(status=SubscriptionStatus.ARCHIVED).count()

    return render(request, 'core/admin_overview.html', {
        'page': page,
        'search': search,
        'total_trainers': total_trainers,
        'active_subs': active_subs,
        'archived_subs': archived_subs,
    })
    
def _exercise_kwargs_from_post(exercise_type, post):
    if exercise_type == ExerciseType.REPS:
        return {
            'sets': _int_or_none(post.get('sets')),
            'reps': _int_or_none(post.get('reps')),
            'duration_minutes': None,
            'distance_km': None,
        }
    if exercise_type == ExerciseType.DURATION:
        return {
            'sets': _int_or_none(post.get('sets_duration')),
            'reps': None,
            'duration_minutes': _int_or_none(post.get('duration_minutes')),
            'distance_km': None,
        }
    if exercise_type == ExerciseType.DISTANCE:
        return {
            'sets': None,
            'reps': None,
            'duration_minutes': None,
            'distance_km': _float_or_none(post.get('distance_km')),
        }
    return {}


def _int_or_none(value):
    try:
        return int(value) if value not in (None, '') else None
    except (ValueError, TypeError):
        return None


def _float_or_none(value):
    try:
        return float(value) if value not in (None, '') else None
    except (ValueError, TypeError):
        return None


def _exercise_form_context(plan, exercise, form_title, submit_label, values):
    return {
        'active_nav': 'plans',
        'form_title': form_title,
        'submit_label': submit_label,
        'plan': plan,
        'exercise': exercise,
        'values': values,
    }