from django.urls import path
from patients import views

urlpatterns = [
    path('dashboard/', views.patient_dashboard, name='patient_dashboard'),
    path('doctors/', views.view_doctors, name='view_doctors'),
    path('doctors/<int:doctor_id>/slots/', views.view_time_slots, name='view_time_slots'),
    path('book/<int:slot_id>/', views.book_appointment, name='book_appointment'),
    path('appointment/<int:appointment_id>/cancel/', views.cancel_appointment, name='cancel_appointment'),
    path('appointment/<int:appointment_id>/add-to-calendar/', views.add_to_google_calendar, name='add_to_google_calendar'),
    path('profile/edit/', views.edit_patient_profile, name='edit_patient_profile'),
]
