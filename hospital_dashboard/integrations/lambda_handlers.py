"""
AWS Lambda Handler Functions for Serverless Operations
This module contains Lambda handlers for asynchronous tasks
"""

import json
import os
import sys
from datetime import datetime

# Add project to path for Lambda
sys.path.insert(0, '/var/task')

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hospital_dashboard.settings')

try:
    import django
    django.setup()
except:
    pass

from hospital_dashboard.integrations import EmailNotificationService
from hospital_dashboard.integrations.calendar_sync import AppointmentCalendarSync
from patients.models import Appointment


def send_appointment_confirmation(event, context):
    """
    Lambda handler for sending appointment confirmation emails
    
    Event format:
    {
        "appointment_id": <id>,
        "action": "confirmation"
    }
    """
    try:
        appointment_id = event.get('appointment_id')
        appointment = Appointment.objects.get(id=appointment_id)
        
        success = EmailNotificationService.send_appointment_confirmation(appointment)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Confirmation email sent successfully',
                'appointment_id': appointment_id,
                'success': success
            })
        }
    except Appointment.DoesNotExist:
        return {
            'statusCode': 404,
            'body': json.dumps({'error': 'Appointment not found'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def send_appointment_reminder(event, context):
    """
    Lambda handler for sending appointment reminders
    
    Event format:
    {
        "appointment_id": <id>,
        "action": "reminder",
        "hours_before": 24
    }
    """
    try:
        appointment_id = event.get('appointment_id')
        hours_before = event.get('hours_before', 24)
        appointment = Appointment.objects.get(id=appointment_id)
        
        success = EmailNotificationService.send_appointment_reminder(
            appointment,
            hours_before=hours_before
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Reminder email sent successfully',
                'appointment_id': appointment_id,
                'success': success
            })
        }
    except Appointment.DoesNotExist:
        return {
            'statusCode': 404,
            'body': json.dumps({'error': 'Appointment not found'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def sync_appointment_to_calendar(event, context):
    """
    Lambda handler for syncing appointments to Google Calendar
    
    Event format:
    {
        "appointment_id": <id>,
        "action": "sync"
    }
    """
    try:
        appointment_id = event.get('appointment_id')
        appointment = Appointment.objects.get(id=appointment_id)
        
        sync_service = AppointmentCalendarSync()
        success = sync_service.sync_appointment_to_calendar(appointment)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Appointment synced to calendar',
                'appointment_id': appointment_id,
                'success': success,
                'calendar_event_id': appointment.google_calendar_event_id
            })
        }
    except Appointment.DoesNotExist:
        return {
            'statusCode': 404,
            'body': json.dumps({'error': 'Appointment not found'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def cancel_appointment_notification(event, context):
    """
    Lambda handler for sending appointment cancellation notifications
    
    Event format:
    {
        "appointment_id": <id>,
        "action": "cancel",
        "reason": "Doctor unavailable"
    }
    """
    try:
        appointment_id = event.get('appointment_id')
        reason = event.get('reason', 'No reason provided')
        appointment = Appointment.objects.get(id=appointment_id)
        
        # Send cancellation email
        email_sent = EmailNotificationService.send_appointment_cancellation(
            appointment,
            reason=reason
        )
        
        # Delete from calendar if synced
        sync_service = AppointmentCalendarSync()
        calendar_deleted = sync_service.delete_appointment_from_calendar(appointment)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Appointment cancelled and notifications sent',
                'appointment_id': appointment_id,
                'email_sent': email_sent,
                'calendar_deleted': calendar_deleted
            })
        }
    except Appointment.DoesNotExist:
        return {
            'statusCode': 404,
            'body': json.dumps({'error': 'Appointment not found'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def batch_send_reminders(event, context):
    """
    Lambda handler for sending reminders to multiple appointments
    Triggered daily or on schedule via EventBridge
    
    Event format: {} (no specific format needed)
    """
    try:
        from datetime import datetime, timedelta
        
        # Get appointments scheduled for 24 hours from now
        tomorrow = datetime.now() + timedelta(hours=24)
        tomorrow_start = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_end = tomorrow_start + timedelta(days=1)
        
        appointments = Appointment.objects.filter(
            appointment_date__gte=tomorrow_start,
            appointment_date__lt=tomorrow_end,
            status='confirmed'
        )
        
        sent_count = 0
        for appointment in appointments:
            if EmailNotificationService.send_appointment_reminder(appointment, hours_before=24):
                sent_count += 1
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Reminders sent to {sent_count} appointments',
                'total_appointments': appointments.count(),
                'sent': sent_count
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def sync_all_appointments_to_calendar(event, context):
    """
    Lambda handler for syncing all pending appointments
    Can be triggered on-demand or on schedule
    
    Event format: {} (no specific format needed)
    """
    try:
        sync_service = AppointmentCalendarSync()
        synced_count = sync_service.sync_all_appointments()
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Synced {synced_count} appointments to Google Calendar',
                'synced_count': synced_count
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
