# core/admin.py
# Register models with Django Admin for CRUD interface.

from django.contrib import admin
from .models import (
    Profile,
    Subscription,
    Client,
    ClientAvailability,
    TrainingPlan,
    Exercise,
    Appointment,
    ProgressLog,
)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'created_at']
    list_filter = ['role']
    search_fields = ['user__username', 'user__email']


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['trainer', 'plan_type', 'start_date', 'end_date', 'status']
    list_filter = ['status', 'plan_type']
    search_fields = ['trainer__username', 'trainer__email']
    list_per_page = 20
    actions = ['archive_selected', 'restore_selected']

    def archive_selected(self, request, queryset):
        queryset.update(status='archived')
    archive_selected.short_description = 'Archive selected subscriptions'

    def restore_selected(self, request, queryset):
        queryset.update(status='active')
    restore_selected.short_description = 'Restore selected subscriptions'


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'trainer', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['name', 'email', 'trainer__username']
    list_per_page = 20


@admin.register(ClientAvailability)
class ClientAvailabilityAdmin(admin.ModelAdmin):
    list_display = ['client', 'day_of_week', 'preferred_time_start', 'preferred_time_end']
    list_filter = ['day_of_week']
    search_fields = ['client__name']


# Inline exercises so they show up inside the TrainingPlan edit page.
class ExerciseInline(admin.TabularInline):
    model = Exercise
    extra = 1


@admin.register(TrainingPlan)
class TrainingPlanAdmin(admin.ModelAdmin):
    list_display = ['title', 'client', 'trainer', 'status', 'generated_by_ai', 'created_at']
    list_filter = ['status', 'generated_by_ai']
    search_fields = ['title', 'client__name', 'trainer__username']
    inlines = [ExerciseInline]
    list_per_page = 20


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ['name', 'training_plan', 'sets', 'reps', 'duration_seconds', 'order_index']
    search_fields = ['name', 'training_plan__title']


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['client', 'trainer', 'scheduled_at', 'duration_minutes', 'status']
    list_filter = ['status']
    search_fields = ['client__name', 'trainer__username']
    date_hierarchy = 'scheduled_at'
    list_per_page = 20


@admin.register(ProgressLog)
class ProgressLogAdmin(admin.ModelAdmin):
    list_display = ['client', 'exercise', 'logged_at', 'sets_completed', 'reps_completed', 'weight_kg']
    list_filter = ['exercise']
    search_fields = ['client__name', 'exercise__name']
    date_hierarchy = 'logged_at'
    list_per_page = 20