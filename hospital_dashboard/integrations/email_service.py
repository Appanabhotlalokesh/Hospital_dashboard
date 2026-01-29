"""
AWS SES Email Notification Service
Handles sending emails via AWS Simple Email Service
"""

import os
import boto3
from botocore.exceptions import ClientError
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings

class AWSSESBackend(BaseEmailBackend):
    """Django email backend for AWS SES"""
    
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently)
        self.connection = None
        self._connect()
    
    def _connect(self):
        """Initialize SES client"""
        try:
            self.connection = boto3.client(
                'ses',
                region_name=os.getenv('AWS_REGION', 'us-east-1'),
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
        except Exception as e:
            if not self.fail_silently:
                raise
            self.connection = None
    
    def send_messages(self, email_messages):
        """
        Send email messages via AWS SES
        
        Args:
            email_messages: List of EmailMessage objects
        
        Returns:
            Number of messages sent successfully
        """
        if not self.connection:
            return 0
        
        msg_count = 0
        for message in email_messages:
            try:
                self.connection.send_email(
                    Source=message.from_email,
                    Destination={
                        'ToAddresses': message.to,
                        'CcAddresses': message.cc if message.cc else [],
                        'BccAddresses': message.bcc if message.bcc else []
                    },
                    Message={
                        'Subject': {
                            'Data': message.subject,
                            'Charset': 'UTF-8'
                        },
                        'Body': {
                            'Text': {
                                'Data': message.body,
                                'Charset': 'UTF-8'
                            } if message.body else {},
                            'Html': {
                                'Data': message.alternatives[0][0] if message.alternatives else '',
                                'Charset': 'UTF-8'
                            } if message.alternatives else {}
                        }
                    }
                )
                msg_count += 1
            except ClientError as e:
                if not self.fail_silently:
                    raise
        
        return msg_count


class EmailNotificationService:
    """Service for sending appointment notifications"""
    
    @staticmethod
    def send_appointment_confirmation(appointment):
        """
        Send appointment confirmation email
        
        Args:
            appointment: Appointment object
        """
        try:
            from django.core.mail import EmailMultiAlternatives
            from django.template.loader import render_to_string
            
            subject = f"Appointment Confirmation - {appointment.appointment_date.strftime('%Y-%m-%d')}"
            
            context = {
                'patient_name': appointment.patient.user.get_full_name() or appointment.patient.user.username,
                'doctor_name': appointment.doctor.user.get_full_name() or appointment.doctor.user.username,
                'appointment_date': appointment.appointment_date,
                'appointment_time': appointment.appointment_date.strftime('%H:%M'),
                'appointment_notes': appointment.notes,
            }
            
            html_content = render_to_string('emails/appointment_confirmation.html', context)
            text_content = render_to_string('emails/appointment_confirmation.txt', context)
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=os.getenv('EMAIL_FROM_ADDRESS', 'noreply@hospital.com'),
                to=[appointment.patient.user.email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=False)
            
            return True
        except Exception as e:
            print(f"Error sending appointment confirmation: {e}")
            return False
    
    @staticmethod
    def send_appointment_cancellation(appointment, reason=None):
        """
        Send appointment cancellation email
        
        Args:
            appointment: Appointment object
            reason: Cancellation reason
        """
        try:
            from django.core.mail import EmailMultiAlternatives
            from django.template.loader import render_to_string
            
            subject = f"Appointment Cancelled - {appointment.appointment_date.strftime('%Y-%m-%d')}"
            
            context = {
                'patient_name': appointment.patient.user.get_full_name() or appointment.patient.user.username,
                'doctor_name': appointment.doctor.user.get_full_name() or appointment.doctor.user.username,
                'appointment_date': appointment.appointment_date,
                'appointment_time': appointment.appointment_date.strftime('%H:%M'),
                'reason': reason or 'No reason provided',
            }
            
            html_content = render_to_string('emails/appointment_cancellation.html', context)
            text_content = render_to_string('emails/appointment_cancellation.txt', context)
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=os.getenv('EMAIL_FROM_ADDRESS', 'noreply@hospital.com'),
                to=[appointment.patient.user.email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=False)
            
            return True
        except Exception as e:
            print(f"Error sending cancellation email: {e}")
            return False
    
    @staticmethod
    def send_appointment_reminder(appointment, hours_before=24):
        """
        Send appointment reminder email
        
        Args:
            appointment: Appointment object
            hours_before: Hours before appointment to send reminder
        """
        try:
            from django.core.mail import EmailMultiAlternatives
            from django.template.loader import render_to_string
            
            subject = f"Appointment Reminder - {appointment.appointment_date.strftime('%Y-%m-%d')}"
            
            context = {
                'patient_name': appointment.patient.user.get_full_name() or appointment.patient.user.username,
                'doctor_name': appointment.doctor.user.get_full_name() or appointment.doctor.user.username,
                'appointment_date': appointment.appointment_date,
                'appointment_time': appointment.appointment_date.strftime('%H:%M'),
            }
            
            html_content = render_to_string('emails/appointment_reminder.html', context)
            text_content = render_to_string('emails/appointment_reminder.txt', context)
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=os.getenv('EMAIL_FROM_ADDRESS', 'noreply@hospital.com'),
                to=[appointment.patient.user.email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=False)
            
            return True
        except Exception as e:
            print(f"Error sending reminder email: {e}")
            return False
