# core/views.py
# View functions for public pages, auth, and clients.

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Profile, UserRole, Client, ClientStatus
from .permissions import trainer_required, admin_required, get_user_role


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


# Admin pages

@admin_required
def admin_overview(request):
    return render(request, 'core/admin_overview.html')