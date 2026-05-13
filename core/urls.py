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

    path('admin-overview/', views.admin_overview, name='admin_overview'),
]