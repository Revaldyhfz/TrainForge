# core/urls.py
# URL routes for the core app.

from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),

    path('clients/', views.clients_list, name='clients_list'),
    path('clients/new/', views.client_create, name='client_create'),
    path('clients/<int:client_id>/edit/', views.client_edit, name='client_edit'),
    path('clients/<int:client_id>/archive/', views.client_archive, name='client_archive'),
    path('clients/<int:client_id>/restore/', views.client_restore, name='client_restore'),

    path('plans/', views.plans_list, name='plans_list'),
    path('plans/new/', views.plan_create, name='plan_create'),
    path('plans/<int:plan_id>/edit/', views.plan_edit, name='plan_edit'),
    path('plans/<int:plan_id>/archive/', views.plan_archive, name='plan_archive'),
    path('plans/<int:plan_id>/restore/', views.plan_restore, name='plan_restore'),
    path('plans/<int:plan_id>/', views.plan_detail, name='plan_detail'),

    path('plans/<int:plan_id>/send-email/', views.plan_send_email, name='plan_send_email'),
    path('plans/<int:plan_id>/exercises/new/', views.exercise_create, name='exercise_create'),
    
    path('exercises/<int:exercise_id>/edit/', views.exercise_edit, name='exercise_edit'),
    path('exercises/<int:exercise_id>/delete/', views.exercise_delete, name='exercise_delete'),
    
    path('appointments/', views.appointments_list, name='appointments_list'),
    path('appointments/new/', views.appointment_create, name='appointment_create'),
    path('appointments/<int:appointment_id>/edit/', views.appointment_edit, name='appointment_edit'),
    path('appointments/<int:appointment_id>/cancel/', views.appointment_cancel, name='appointment_cancel'),

    path('progress/', views.progress_list, name='progress_list'),
    path('progress/new/', views.progress_create, name='progress_create'),
    path('progress/<int:log_id>/edit/', views.progress_edit, name='progress_edit'),
    path('progress/<int:log_id>/delete/', views.progress_delete, name='progress_delete'),
    
    path('progress/body-weight/log/', views.body_weight_log, name='body_weight_log'),
    path('progress/body-weight/<int:measurement_id>/delete/', views.body_weight_delete, name='body_weight_delete'),
    
    path('progress/body-weight/<int:measurement_id>/delete/', views.body_weight_delete, name='body_weight_delete'),
    
    path('plans/<int:plan_id>/ai/questionnaire/', views.ai_questionnaire, name='ai_questionnaire'),
    path('plans/<int:plan_id>/ai/chat/', views.ai_chat, name='ai_chat'),
    
    path('admin-overview/', views.admin_overview, name='admin_overview'),
]