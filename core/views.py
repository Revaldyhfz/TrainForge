# core/views.py
# View functions for public pages, auth, and clients.

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Profile, UserRole, Client, ClientStatus
from .permissions import trainer_required, admin_required, get_user_role
from .models import Profile, UserRole, Client, ClientStatus, TrainingPlan, TrainingPlanStatus, Exercise


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


# Trainer pages

@trainer_required
def dashboard(request):
    return render(request, 'core/dashboard.html', {'active_nav': 'dashboard'})


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

# Admin pages

@admin_required
def admin_overview(request):
    return render(request, 'core/admin_overview.html')

