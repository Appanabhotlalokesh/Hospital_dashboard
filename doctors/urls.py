from django.contrib import admin
from django.urls import path
from hospital_dashboard import views
from doctors import views as doctor_views


urlpatterns = [ 
    path("", views.index, name = 'index'),
    path("login", views.login_page, name = 'login_page'),
    path("logout", views.logout_page, name = 'logout_page'),
    path("signup", views.signup_page, name = 'signup_page'),
    path("doctors", doctor_views.doctor_dashboard, name = 'doctor_dashboard'),
    path("doctor/profile", doctor_views.doctor_profile, name = 'doctor_profile'),
    path("doctor/add-slot", doctor_views.add_time_slot, name = 'add_time_slot'),
    path("doctor/edit-slot/<int:slot_id>", doctor_views.edit_time_slot, name = 'edit_time_slot'),
    path("doctor/delete-slot/<int:slot_id>", doctor_views.delete_time_slot, name = 'delete_time_slot'),
    path("doctor/toggle-availability/<int:slot_id>", doctor_views.toggle_availability, name = 'toggle_availability'),
]