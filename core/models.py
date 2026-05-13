# core/models.py
# Domain models for TrainForge.

from django.db import models
from django.contrib.auth.models import User


# Enums

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


class ExerciseType(models.TextChoices):
    REPS = 'reps', 'Reps-based (sets × reps)'
    DURATION = 'duration', 'Duration-based (sets × minutes)'
    DISTANCE = 'distance', 'Distance-based (e.g., 5km run)'


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


# Client represents a person the trainer is working with.
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
    exercise_type = models.CharField(
        max_length=15, choices=ExerciseType.choices, default=ExerciseType.REPS
    )
    sets = models.PositiveIntegerField(null=True, blank=True)
    reps = models.PositiveIntegerField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    distance_km = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    order_index = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order_index']

    def __str__(self):
        return self.name

    def summary(self):
        if self.exercise_type == ExerciseType.REPS:
            return f"{self.sets} sets × {self.reps} reps"
        if self.exercise_type == ExerciseType.DURATION:
            return f"{self.sets} sets × {self.duration_minutes} min"
        if self.exercise_type == ExerciseType.DISTANCE:
            return f"{self.distance_km} km"
        return ""


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
    sets_completed = models.PositiveIntegerField(null=True, blank=True)
    reps_completed = models.PositiveIntegerField(null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    distance_km = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-logged_at']

    def __str__(self):
        return f"{self.client.name} - {self.exercise.name} - {self.logged_at}"

    def summary(self):
        ex_type = self.exercise.exercise_type
        if ex_type == ExerciseType.REPS:
            base = f"{self.sets_completed} × {self.reps_completed}"
            if self.weight_kg:
                base += f" @ {self.weight_kg} kg"
            return base
        if ex_type == ExerciseType.DURATION:
            return f"{self.sets_completed} × {self.duration_minutes} min"
        if ex_type == ExerciseType.DISTANCE:
            return f"{self.distance_km} km"
        return ""
    
# BodyMeasurement records a client's body weight at a point in time.
class BodyMeasurement(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='body_measurements')
    weight_kg = models.DecimalField(max_digits=5, decimal_places=1)
    logged_at = models.DateField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-logged_at']

    def __str__(self):
        return f"{self.client.name} - {self.weight_kg}kg on {self.logged_at}"