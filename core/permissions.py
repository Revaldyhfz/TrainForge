# core/permissions.py
# Helpers and decorators for role-based access control.

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from .models import UserRole


def get_user_role(user):
    if not user.is_authenticated:
        return None
    profile = getattr(user, 'profile', None)
    if profile is None:
        return None
    return profile.role


def trainer_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if get_user_role(request.user) != UserRole.TRAINER:
            messages.error(request, 'Trainer access required.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if get_user_role(request.user) != UserRole.ADMIN:
            messages.error(request, 'Admin access required.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper