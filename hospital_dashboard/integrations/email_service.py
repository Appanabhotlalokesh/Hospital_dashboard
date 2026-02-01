from django.core.mail import send_mail
from django.conf import settings


class EmailNotificationService:

    @staticmethod
    def send_appointment_confirmation(appointment):

        subject = "Appointment Confirmation - Hospital Dashboard"

        message = f"""
Hello {appointment.patient.user.get_full_name()},

Your appointment has been successfully booked.

Doctor: Dr. {appointment.doctor.user.get_full_name()}
Date: {appointment.time_slot.date}
Time: {appointment.time_slot.start_time} - {appointment.time_slot.end_time}

Hospital Dashboard
"""

        recipients = [
            appointment.patient.user.email,
            appointment.doctor.user.email
        ]

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            recipients,
            fail_silently=False
        )
