import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from datetime import datetime
from .models import PatientProfile, Appointment
from doctors.models import DoctorProfile, TimeSlot
from hospital_dashboard.integrations import EmailNotificationService
from hospital_dashboard.integrations.calendar_sync import AppointmentCalendarSync

# Initialize logger
logger = logging.getLogger(__name__)

# Create your views here.

@login_required(login_url='login_page')
def patient_dashboard(request):
    """Main patient dashboard showing booked appointments"""
    try:
        patient = PatientProfile.objects.get(user=request.user)
    except PatientProfile.DoesNotExist:
        # Auto-create patient profile if it doesn't exist
        patient = PatientProfile.objects.create(user=request.user)

    # Get patient's appointments ordered by date
    appointments = Appointment.objects.filter(patient=patient).select_related('doctor', 'time_slot').order_by('-time_slot__date')

    # Separate upcoming and past appointments
    today = datetime.now().date()
    upcoming_appointments = appointments.filter(time_slot__date__gte=today)
    past_appointments = appointments.filter(time_slot__date__lt=today)

    context = {
        'patient': patient,
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments,
        'total_appointments': appointments.count(),
    }
    return render(request, 'patient_dashboard.html', context)


@login_required(login_url='login_page')
def view_doctors(request):
    """List all available doctors"""
    try:
        patient = PatientProfile.objects.get(user=request.user)
    except PatientProfile.DoesNotExist:
        patient = PatientProfile.objects.create(user=request.user)

    # Get all doctors
    doctors = DoctorProfile.objects.filter(is_available=True).select_related('user')

    # Optional: Filter by specialization
    specialization = request.GET.get('specialization', '')
    if specialization:
        doctors = doctors.filter(specialization__icontains=specialization)

    context = {
        'patient': patient,
        'doctors': doctors,
        'specialization_filter': specialization,
    }
    return render(request, 'view_doctors.html', context)


@login_required(login_url='login_page')
def view_time_slots(request, doctor_id):
    """View available time slots for a specific doctor"""
    try:
        patient = PatientProfile.objects.get(user=request.user)
    except PatientProfile.DoesNotExist:
        patient = PatientProfile.objects.create(user=request.user)

    doctor = get_object_or_404(DoctorProfile, id=doctor_id)

    # Get all available time slots for this doctor
    today = datetime.now().date()
    available_slots = TimeSlot.objects.filter(
        doctor=doctor,
        date__gte=today,
        is_available=True
    ).select_related('doctor').order_by('date', 'start_time')

    # Check which slots are already booked by this patient
    patient_booked_slots = Appointment.objects.filter(patient=patient).values_list('time_slot_id', flat=True)

    context = {
        'patient': patient,
        'doctor': doctor,
        'available_slots': available_slots,
        'patient_booked_slots': patient_booked_slots,
    }
    return render(request, 'view_time_slots.html', context)


@login_required(login_url='login_page')
def book_appointment(request, slot_id):
    """Book an appointment for a patient"""
    try:
        patient = PatientProfile.objects.get(user=request.user)
    except PatientProfile.DoesNotExist:
        patient = PatientProfile.objects.create(user=request.user)

    slot = get_object_or_404(TimeSlot, id=slot_id)

    # Check if slot is still available
    if not slot.is_available:
        messages.error(request, "This time slot is no longer available!")
        return redirect('view_time_slots', doctor_id=slot.doctor.id)

    # Check if patient already has an appointment for this slot
    if Appointment.objects.filter(patient=patient, time_slot=slot).exists():
        messages.warning(request, "You already have an appointment for this time slot!")
        return redirect('view_time_slots', doctor_id=slot.doctor.id)

    if request.method == 'POST':
        notes = request.POST.get('notes', '')

        try:
            # Use transaction to ensure data consistency
            with transaction.atomic():
                # Create appointment
                appointment = Appointment.objects.create(
                    patient=patient,
                    doctor=slot.doctor,
                    time_slot=slot,
                    status='confirmed',
                    notes=notes
                )

                # Mark slot as unavailable
                slot.is_available = False
                slot.save()

            logger.info(f"Appointment {appointment.id} created for patient {patient.user.email}")

            # Send confirmation email (non-blocking)
            try:
                EmailNotificationService.send_appointment_confirmation(appointment)
                logger.debug(f"Confirmation email sent for appointment {appointment.id}")
            except Exception as e:
                logger.warning(f"Failed to send confirmation email for appointment {appointment.id}: {e}")
            
            # Sync to Google Calendar (non-blocking)
            calendar_synced = False
            try:
                logger.info(f"Syncing appointment {appointment.id} to Google Calendar...")
                sync_service = AppointmentCalendarSync()
                calendar_synced = sync_service.sync_appointment_to_calendar(appointment)
                
                if calendar_synced:
                    logger.info(f"✅ Appointment {appointment.id} successfully synced to Google Calendar")
                else:
                    logger.warning(f"⚠️  Appointment {appointment.id} could not be synced to Google Calendar (check credentials)")
            except Exception as e:
                logger.error(f"Error syncing appointment {appointment.id} to Google Calendar: {e}", exc_info=True)

            # Success message
            success_msg = f"Appointment booked successfully with Dr. {slot.doctor.user.first_name}!"
            if calendar_synced:
                success_msg += " The appointment has been added to your Google Calendar."
            messages.success(request, success_msg)
            return redirect('patient_dashboard')

        except Exception as e:
            logger.error(f"Error booking appointment: {e}", exc_info=True)
            messages.error(request, f"Error booking appointment: {str(e)}")
            return redirect('view_time_slots', doctor_id=slot.doctor.id)

    context = {
        'patient': patient,
        'slot': slot,
        'doctor': slot.doctor,
    }
    return render(request, 'book_appointment.html', context)


@login_required(login_url='login_page')
def cancel_appointment(request, appointment_id):
    """Cancel an existing appointment"""
    try:
        patient = PatientProfile.objects.get(user=request.user)
    except PatientProfile.DoesNotExist:
        messages.error(request, "Patient profile not found.")
        return redirect('patient_dashboard')

    appointment = get_object_or_404(Appointment, id=appointment_id)

    # Verify this appointment belongs to the logged-in patient
    if appointment.patient != patient:
        messages.error(request, "You can only cancel your own appointments!")
        return redirect('patient_dashboard')

    if request.method == 'POST':
        try:
            reason = request.POST.get('reason', 'Patient requested cancellation')
            
            # Use transaction for data consistency
            with transaction.atomic():
                # Mark slot as available again
                slot = appointment.time_slot
                slot.is_available = True
                slot.save()

                # Mark appointment as cancelled
                appointment.status = 'cancelled'
                appointment.save()

            logger.info(f"Appointment {appointment.id} cancelled by patient {patient.user.email}")

            # Send cancellation email (non-blocking)
            try:
                EmailNotificationService.send_appointment_cancellation(appointment, reason=reason)
                logger.debug(f"Cancellation email sent for appointment {appointment.id}")
            except Exception as e:
                logger.warning(f"Failed to send cancellation email for appointment {appointment.id}: {e}")
            
            # Delete from Google Calendar (non-blocking)
            calendar_deleted = False
            try:
                sync_service = AppointmentCalendarSync()
                calendar_deleted = sync_service.delete_appointment_from_calendar(appointment)
                
                if calendar_deleted:
                    logger.info(f"✅ Appointment {appointment.id} deleted from Google Calendar")
            except Exception as e:
                logger.error(f"Error deleting appointment {appointment.id} from Google Calendar: {e}", exc_info=True)

            success_msg = "Appointment cancelled successfully!"
            if calendar_deleted:
                success_msg += " The appointment has been removed from your Google Calendar."
            messages.success(request, success_msg)
            return redirect('patient_dashboard')
        except Exception as e:
            logger.error(f"Error cancelling appointment: {e}", exc_info=True)
            messages.error(request, f"Error cancelling appointment: {str(e)}")
            return redirect('patient_dashboard')

    context = {
        'appointment': appointment,
    }
    return render(request, 'cancel_appointment.html', context)


@login_required(login_url='login_page')
def edit_patient_profile(request):
    """Edit patient profile information"""
    try:
        patient = PatientProfile.objects.get(user=request.user)
    except PatientProfile.DoesNotExist:
        patient = PatientProfile.objects.create(user=request.user)

    if request.method == 'POST':
        # Update user info
        request.user.first_name = request.POST.get('first_name', request.user.first_name)
        request.user.last_name = request.POST.get('last_name', request.user.last_name)
        request.user.email = request.POST.get('email', request.user.email)
        request.user.save()

        # Update patient profile
        patient.phone = request.POST.get('phone', patient.phone)
        patient.age = request.POST.get('age') or patient.age
        patient.gender = request.POST.get('gender', patient.gender)
        patient.address = request.POST.get('address', patient.address)
        patient.medical_history = request.POST.get('medical_history', patient.medical_history)
        patient.save()

        messages.success(request, "Profile updated successfully!")
        return redirect('patient_dashboard')

    context = {
        'patient': patient,
    }
    return render(request, 'edit_patient_profile.html', context)


@login_required(login_url='login_page')
def add_to_google_calendar(request, appointment_id):
    """Add appointment to Google Calendar manually"""
    try:
        appointment = Appointment.objects.get(id=appointment_id)
        patient = PatientProfile.objects.get(user=request.user)
        
        # Verify the appointment belongs to the logged-in patient
        if appointment.patient != patient:
            messages.error(request, "Unauthorized access!")
            return redirect('patient_dashboard')
        
        # If already synced, return
        if appointment.google_calendar_event_id:
            messages.warning(request, "This appointment is already synced to Google Calendar!")
            return redirect('patient_dashboard')
        
        # Sync to Google Calendar
        try:
            logger.info(f"Manually syncing appointment {appointment_id} to Google Calendar...")
            sync_service = AppointmentCalendarSync()
            result = sync_service.sync_appointment_to_calendar(appointment)
            
            if result:
                messages.success(request, "✅ Appointment added to Google Calendar successfully!")
                logger.info(f"✅ Appointment {appointment_id} manually synced to Google Calendar")
            else:
                messages.error(request, "❌ Failed to add appointment to Google Calendar. Please check your credentials.")
                logger.warning(f"Failed to manually sync appointment {appointment_id} to Google Calendar")
        except Exception as e:
            logger.error(f"Error manually syncing appointment {appointment_id} to Google Calendar: {e}", exc_info=True)
            messages.error(request, f"Error syncing to Google Calendar: {str(e)}")
        
        return redirect('patient_dashboard')
    
    except Appointment.DoesNotExist:
        messages.error(request, "Appointment not found!")
        return redirect('patient_dashboard')
    except PatientProfile.DoesNotExist:
        messages.error(request, "Patient profile not found!")
        return redirect('patient_dashboard')
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return redirect('patient_dashboard')
