"""
Integration package for third-party services
Imports are wrapped in try-except to handle missing dependencies gracefully
"""

try:
    from .google_calendar import GoogleCalendarService
except ImportError:
    GoogleCalendarService = None

try:
    from .email_service import EmailNotificationService, AWSSESBackend
except ImportError:
    EmailNotificationService = None
    AWSSESBackend = None

__all__ = ['GoogleCalendarService', 'EmailNotificationService', 'AWSSESBackend']
