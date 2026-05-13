# core/models.py
# Domain models for TrainForge.

from django.db import models
from django.contrib.auth.models import User


# Roles and status enums used across multiple models.

class UserRole(models.TextChoices):
    ADMIN = 'admin', 'Admin'
    TRAINER = 'trainer', 'Trainer'


class SubscriptionStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    ARCHIVED = 'archived', 'Archived'


class ClientStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    INACTIVE = 'inactive', 'Inactive'

class ClientFitnessLevel(models.TextChoices):
    BEGINNER = 'beginner', 'Beginner'
    INTERMEDIATE = 'intermediate', 'Intermediate'
    ADVANCED = 'advanced', 'Advanced'
    
class TrainingPlanStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    ARCHIVED = 'archived', 'Archived'


class AppointmentStatus(models.TextChoices):
    SCHEDULED = 'scheduled', 'Scheduled'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'


# Profile extends Django's built-in User with role information.
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=UserRole.choices, default=UserRole.TRAINER)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"


# Subscription tracks which trainers have paid access and for how long.
class Subscription(models.Model):
    trainer = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    plan_type = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=10, choices=SubscriptionStatus.choices, default=SubscriptionStatus.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.trainer.username} - {self.plan_type}"


class Client(models.Model):
    trainer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='clients')
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    goals = models.TextField(blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    height_cm = models.PositiveIntegerField(null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    fitness_level = models.CharField(
        max_length=15, choices=ClientFitnessLevel.choices, blank=True
    )
    status = models.CharField(max_length=10, choices=ClientStatus.choices, default=ClientStatus.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

# ClientAvailability stores a client's preferred training days/times.
class ClientAvailability(models.Model):
    DAY_CHOICES = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='availabilities')
    day_of_week = models.CharField(max_length=10, choices=DAY_CHOICES)
    preferred_time_start = models.TimeField()
    preferred_time_end = models.TimeField()

    def __str__(self):
        return f"{self.client.name} - {self.day_of_week}"


# TrainingPlan is a structured program assigned to a client.
class TrainingPlan(models.Model):
    trainer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='training_plans')
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='training_plans')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=TrainingPlanStatus.choices, default=TrainingPlanStatus.ACTIVE)
    generated_by_ai = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.client.name})"


# Exercise is one entry inside a training plan.
class Exercise(models.Model):
    training_plan = models.ForeignKey(TrainingPlan, on_delete=models.CASCADE, related_name='exercises')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    sets = models.PositiveIntegerField(default=0)
    reps = models.PositiveIntegerField(default=0)
    duration_seconds = models.PositiveIntegerField(default=0)
    order_index = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order_index']

    def __str__(self):
        return self.name


# Appointment is a scheduled session between a trainer and a client.
class Appointment(models.Model):
    trainer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments')
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='appointments')
    title = models.CharField(max_length=200, blank=True)
    scheduled_at = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=60)
    status = models.CharField(max_length=10, choices=AppointmentStatus.choices, default=AppointmentStatus.SCHEDULED)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['scheduled_at']

    def __str__(self):
        return f"{self.client.name} - {self.scheduled_at}"


# ProgressLog records performance for an exercise on a given date.
class ProgressLog(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='progress_logs')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='progress_logs')
    logged_at = models.DateTimeField()
    sets_completed = models.PositiveIntegerField(default=0)
    reps_completed = models.PositiveIntegerField(default=0)
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-logged_at']

    def __str__(self):
        return f"{self.client.name} - {self.exercise.name} - {self.logged_at}"