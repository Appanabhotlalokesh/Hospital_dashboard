"""
Appointment Calendar Sync Utility
Handles syncing appointments between Django and Google Calendar
Optimized with proper error handling, validation, and timezone support
"""

import logging
from datetime import datetime
from django.utils import timezone
from django.db import transaction
from hospital_dashboard.integrations.google_calendar import GoogleCalendarService
from patients.models import Appointment

# Initialize logger
logger = logging.getLogger(__name__)


class AppointmentCalendarSync:
    """Service for syncing appointments with Google Calendar"""

    def __init__(self):
        self.calendar_service = GoogleCalendarService()

    def _validate_appointment(self, appointment):
        """Validate appointment has all required fields"""
        if not appointment:
            logger.error("Cannot sync: appointment is None")
            return False
        
        if not hasattr(appointment, 'time_slot') or not appointment.time_slot:
            logger.error(f"Cannot sync appointment {appointment.id}: missing time_slot")
            return False
        
        if not hasattr(appointment, 'patient') or not appointment.patient:
            logger.error(f"Cannot sync appointment {appointment.id}: missing patient")
            return False
        
        if not hasattr(appointment, 'doctor') or not appointment.doctor:
            logger.error(f"Cannot sync appointment {appointment.id}: missing doctor")
            return False
        
        time_slot = appointment.time_slot
        if not time_slot.date or not time_slot.start_time or not time_slot.end_time:
            logger.error(f"Cannot sync appointment {appointment.id}: incomplete time_slot data")
            return False
        
        return True

    def _get_user_name(self, user):
        """Get user's full name, fallback to email if name not available"""
        if not user:
            return "Unknown User"
        
        full_name = user.get_full_name().strip()
        if full_name:
            return full_name
        return user.email or "Unknown User"

    def sync_appointment_to_calendar(self, appointment):
        """
        Sync a new appointment to Google Calendar
        
        Args:
            appointment: Appointment instance to sync
        
        Returns:
            True if synced successfully, False otherwise
        """
        if not self.calendar_service.service:
            logger.warning("Google Calendar service not available - skipping sync")
            return False

        if not self._validate_appointment(appointment):
            return False

        try:
            # Get user names with fallbacks
            patient_name = self._get_user_name(appointment.patient.user)
            doctor_name = self._get_user_name(appointment.doctor.user)
            
            # Build summary & description
            summary = f"Appointment: {patient_name} with Dr. {doctor_name}"
            
            description_parts = [
                f"Patient: {patient_name}",
                f"Doctor: Dr. {doctor_name}",
            ]
            
            if appointment.patient.user.email:
                description_parts.append(f"Patient Email: {appointment.patient.user.email}")
            
            if appointment.doctor.user.email:
                description_parts.append(f"Doctor Email: {appointment.doctor.user.email}")
            
            if appointment.notes:
                description_parts.append(f"Notes: {appointment.notes}")
            else:
                description_parts.append("Notes: No additional notes")
            
            description = "\n".join(description_parts)

            # Combine date & time from TimeSlot
            time_slot = appointment.time_slot
            start_dt = datetime.combine(time_slot.date, time_slot.start_time)
            end_dt = datetime.combine(time_slot.date, time_slot.end_time)
            
            # Validate end time is after start time
            if end_dt <= start_dt:
                logger.error(f"Invalid appointment times: end_time must be after start_time")
                return False

            # Collect attendee emails
            attendees = []
            if appointment.patient.user.email:
                attendees.append(appointment.patient.user.email)
            if appointment.doctor.user.email:
                attendees.append(appointment.doctor.user.email)

            logger.info(f"Syncing appointment {appointment.id} to Google Calendar...")
            logger.debug(f"Event details: {start_dt} to {end_dt}, Attendees: {attendees}")

            # Create event in Google Calendar
            event = self.calendar_service.create_event(
                summary=summary,
                description=description,
                start_time=start_dt,
                end_time=end_dt,
                attendees=attendees if attendees else None
            )

            if event:
                event_id = event.get("id")
                if event_id:
                    # Save event ID to appointment
                    with transaction.atomic():
                        appointment.google_calendar_event_id = event_id
                        appointment.save(update_fields=['google_calendar_event_id'])
                    
                    logger.info(f"✅ Appointment {appointment.id} synced to Google Calendar: {event_id}")
                    return True
                else:
                    logger.error(f"Event created but no ID returned")
                    return False
            else:
                logger.error(f"Failed to create Google Calendar event for appointment {appointment.id}")
                return False

        except Exception as e:
            logger.error(f"Error syncing appointment {appointment.id} to calendar: {e}", exc_info=True)
            return False

    def update_appointment_in_calendar(self, appointment):
        """
        Update an existing appointment in Google Calendar
        
        Args:
            appointment: Appointment instance to update
        
        Returns:
            True if updated successfully, False otherwise
        """
        if not self.calendar_service.service:
            return False

        if not appointment.google_calendar_event_id:
            logger.warning(f"Appointment {appointment.id} has no Google Calendar event ID - cannot update")
            return False

        if not self._validate_appointment(appointment):
            return False

        try:
            patient_name = self._get_user_name(appointment.patient.user)
            doctor_name = self._get_user_name(appointment.doctor.user)
            
            summary = f"Appointment: {patient_name} with Dr. {doctor_name}"
            
            description_parts = [
                f"Patient: {patient_name}",
                f"Doctor: Dr. {doctor_name}",
            ]
            
            if appointment.patient.user.email:
                description_parts.append(f"Patient Email: {appointment.patient.user.email}")
            
            if appointment.doctor.user.email:
                description_parts.append(f"Doctor Email: {appointment.doctor.user.email}")
            
            if appointment.notes:
                description_parts.append(f"Notes: {appointment.notes}")
            else:
                description_parts.append("Notes: No additional notes")
            
            description = "\n".join(description_parts)

            time_slot = appointment.time_slot
            start_dt = datetime.combine(time_slot.date, time_slot.start_time)
            end_dt = datetime.combine(time_slot.date, time_slot.end_time)
            
            if end_dt <= start_dt:
                logger.error(f"Invalid appointment times for update")
                return False

            attendees = []
            if appointment.patient.user.email:
                attendees.append(appointment.patient.user.email)
            if appointment.doctor.user.email:
                attendees.append(appointment.doctor.user.email)

            event = self.calendar_service.update_event(
                event_id=appointment.google_calendar_event_id,
                summary=summary,
                description=description,
                start_time=start_dt,
                end_time=end_dt,
                attendees=attendees if attendees else None
            )

            if event:
                logger.info(f" Appointment {appointment.id} updated in Google Calendar")
                return True
            else:
                logger.error(f"Failed to update Google Calendar event for appointment {appointment.id}")
                return False

        except Exception as e:
            logger.error(f"Error updating appointment {appointment.id} in calendar: {e}", exc_info=True)
            return False

    def delete_appointment_from_calendar(self, appointment):
        """
        Delete an appointment from Google Calendar
        
        Args:
            appointment: Appointment instance to delete
        
        Returns:
            True if deleted successfully, False otherwise
        """
        if not self.calendar_service.service:
            return False

        if not appointment.google_calendar_event_id:
            logger.warning(f"Appointment {appointment.id} has no Google Calendar event ID - nothing to delete")
            return True  # Not an error if there's nothing to delete

        try:
            success = self.calendar_service.delete_event(
                event_id=appointment.google_calendar_event_id
            )
            
            if success:
                # Clear event ID from appointment
                with transaction.atomic():
                    appointment.google_calendar_event_id = None
                    appointment.save(update_fields=['google_calendar_event_id'])
                
                logger.info(f"✅ Appointment {appointment.id} deleted from Google Calendar")
            
            return success

        except Exception as e:
            logger.error(f"Error deleting appointment {appointment.id} from calendar: {e}", exc_info=True)
            return False

    def sync_all_appointments(self):
        """
        Sync all future appointments that haven't been synced yet
        
        Returns:
            Number of appointments successfully synced
        """
        synced_count = 0

        try:
            today = timezone.now().date()
            future_appointments = Appointment.objects.filter(
                time_slot__date__gte=today,
                google_calendar_event_id__isnull=True,
                status='confirmed'  # Only sync confirmed appointments
            ).select_related('patient__user', 'doctor__user', 'time_slot')

            total_count = future_appointments.count()
            logger.info(f"Syncing {total_count} unsynced future appointments...")

            for appointment in future_appointments:
                if self.sync_appointment_to_calendar(appointment):
                    synced_count += 1

            logger.info(f"✅ Successfully synced {synced_count} out of {total_count} appointments")
            return synced_count

        except Exception as e:
            logger.error(f"Error syncing all appointments: {e}", exc_info=True)
            return synced_count
