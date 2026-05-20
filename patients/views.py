from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from datetime import datetime
import json
from django.urls import reverse

from .models import PatientProfile, Appointment
from doctors.models import DoctorProfile, TimeSlot
from hospital_dashboard.integrations.email_service import EmailNotificationService
from hospital_dashboard.integrations.calendar_sync import AppointmentCalendarSync

# ---------------------------
# DASHBOARD
# ---------------------------

@login_required(login_url='login_page')
def patient_dashboard(request):

    patient, _ = PatientProfile.objects.get_or_create(user=request.user)

    appointments = Appointment.objects.filter(
        patient=patient
    ).select_related('doctor', 'time_slot').order_by('-time_slot__date')
    today = datetime.now().date()

    upcoming_appointments = appointments.filter(time_slot__date__gte=today)
    past_appointments = appointments.filter(time_slot__date__lt=today)

    return render(request, "patient_dashboard.html", {
        "patient": patient,
        "upcoming_appointments": upcoming_appointments,
        "past_appointments": past_appointments
    })


# ---------------------------
# VIEW DOCTORS
# ---------------------------

@login_required(login_url='login_page')
def view_doctors(request):

    patient, _ = PatientProfile.objects.get_or_create(user=request.user)

    # Support simple search/filter via GET parameter `q` or `specialization`
    q = request.GET.get('q') or request.GET.get('specialization') or ''

    doctors = DoctorProfile.objects.filter(is_available=True)

    if q:
        from django.db.models import Q
        doctors = doctors.filter(
            Q(user__first_name__icontains=q) |
            Q(user__last_name__icontains=q) |
            Q(specialization__icontains=q)
        )

    doctors = doctors.order_by('-experience_years', 'user__first_name')

    return render(request, "view_doctors.html", {
        "patient": patient,
        "doctors": doctors,
        "specialization_filter": q
    })


# ---------------------------
# VIEW TIME SLOTS
# ---------------------------

@login_required(login_url='login_page')
@login_required(login_url='login_page')
def view_time_slots(request, doctor_id):

    patient = PatientProfile.objects.get(user=request.user)
    doctor = get_object_or_404(DoctorProfile, id=doctor_id)

    # 🔥 SHOW ALL FUTURE SLOTS (NO EXTRA FILTERING)
    available_slots = TimeSlot.objects.filter(
        doctor=doctor
    ).order_by('date', 'start_time')

    context = {
        'patient': patient,
        'doctor': doctor,
        'available_slots': available_slots,
    }

    return render(request, 'view_time_slots.html', context)



# ---------------------------
# BOOK APPOINTMENT
# ---------------------------

@login_required(login_url='login_page')
def book_appointment(request, slot_id):

    patient = PatientProfile.objects.get(user=request.user)
    slot = get_object_or_404(TimeSlot, id=slot_id)

    if not slot.is_available:
        messages.error(request, "Slot not available")
        return redirect("patient_dashboard")

    with transaction.atomic():
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=slot.doctor,
            time_slot=slot,
            status="confirmed"
        )

        slot.is_available = False
        slot.save()

    # EMAIL
    EmailNotificationService.send_appointment_confirmation(appointment)

    # GOOGLE CALENDAR
    sync = AppointmentCalendarSync()
    sync.sync_appointment_to_calendar(appointment)

    messages.success(request, "Appointment booked successfully!")

    return redirect("patient_dashboard")


# ---------------------------
# CANCEL APPOINTMENT
# ---------------------------

@login_required(login_url='login_page')
def cancel_appointment(request, appointment_id):

    appointment = get_object_or_404(Appointment, id=appointment_id)

    slot = appointment.time_slot
    slot.is_available = True
    slot.save()

    appointment.status = "cancelled"
    appointment.save()

    EmailNotificationService.send_appointment_cancellation(appointment)

    sync = AppointmentCalendarSync()
    sync.delete_appointment_from_calendar(appointment)

    messages.success(request, "Appointment cancelled")

    return redirect("patient_dashboard")


# ---------------------------
# EDIT PROFILE
# ---------------------------

@login_required(login_url='login_page')
def edit_patient_profile(request):

    patient, _ = PatientProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        patient.phone = request.POST.get("phone")
        patient.save()
        messages.success(request, "Profile updated")

    return render(request, "edit_patient_profile.html", {
        "patient": patient
    })


# ---------------------------
# MANUAL GOOGLE SYNC
# ---------------------------

@login_required(login_url='login_page')
def add_to_google_calendar(request, appointment_id):

    appointment = get_object_or_404(Appointment, id=appointment_id)

    sync = AppointmentCalendarSync()
    result = sync.sync_appointment_to_calendar(appointment)

    if result:
        messages.success(request, "Added to Google Calendar")
    else:
        messages.error(request, "Google Calendar sync failed")

    return redirect("patient_dashboard")


# ---------------------------
# APPOINTMENTS CALENDAR
# ---------------------------


@login_required(login_url='login_page')
def appointments_calendar(request):
    """Render a calendar view (FullCalendar) with the patient's confirmed appointments."""
    patient, _ = PatientProfile.objects.get_or_create(user=request.user)

    appointments = Appointment.objects.filter(patient=patient, status='confirmed').select_related('doctor', 'time_slot')

    events = []
    for a in appointments:
        ts = a.time_slot
        start_dt = datetime.combine(ts.date, ts.start_time)
        end_dt = datetime.combine(ts.date, ts.end_time)
        title = f"Dr. {a.doctor.user.first_name} {a.doctor.user.last_name}"
        events.append({
            "id": a.id,
            "title": title,
            "start": start_dt.isoformat(),
            "end": end_dt.isoformat(),
            "status": a.status,
            "doctor_id": a.doctor.id,
        })

    events_json = json.dumps(events)

    return render(request, 'appointments_calendar.html', {
        'events_json': events_json,
        'patient': patient
    })
