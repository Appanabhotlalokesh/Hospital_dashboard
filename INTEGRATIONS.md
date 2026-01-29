# Integration Guide: Google Calendar & AWS Services

This document outlines the Google Calendar and AWS service integrations for the Hospital Dashboard application.

## Table of Contents

1. [Google Calendar Integration](#google-calendar-integration)
2. [AWS SES Email Service](#aws-ses-email-service)
3. [AWS Lambda Functions](#aws-lambda-functions)
4. [Configuration](#configuration)
5. [Usage Examples](#usage-examples)
6. [Deployment](#deployment)

---

## Google Calendar Integration

### Overview
The Hospital Dashboard automatically syncs appointment bookings and cancellations with Google Calendar. This allows patients and doctors to see appointments in their Google Calendar.

### Features
- ✅ Automatic sync of new appointments
- ✅ Update appointments when modified
- ✅ Delete appointments when cancelled
- ✅ Send calendar invitations to attendees
- ✅ Batch sync of existing appointments

### Setup Instructions

#### Option 1: Service Account (Recommended for Production)

1. **Create a Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable the Google Calendar API

2. **Create Service Account**
   - Go to "Credentials" → "Create Credentials" → "Service Account"
   - Download the JSON key file
   - Copy the entire JSON content

3. **Configure in .env**
   ```env
   GOOGLE_SERVICE_ACCOUNT_JSON={"type": "service_account", "project_id": "...", ...}
   ```

4. **Share Calendar with Service Account**
   - Share your Google Calendar with the service account email address (found in the JSON file)

#### Option 2: OAuth2 (For Testing/Development)

1. **Create OAuth2 Credentials**
   - In Google Cloud Console: Credentials → Create Credentials → OAuth 2.0 Client ID
   - Choose "Desktop application"
   - Download the JSON file as `credentials.json`

2. **Place credentials.json in project root**

3. **Configure in .env**
   ```env
   GOOGLE_CREDENTIALS_PATH=credentials.json
   GOOGLE_TOKEN_PATH=token.json
   ```

4. **First authentication**
   - Run the application; it will prompt you to authenticate
   - A browser window will open for authorization
   - The token will be saved to `token.json`

### Usage in Code

```python
from hospital_dashboard.integrations import GoogleCalendarService
from hospital_dashboard.integrations.calendar_sync import AppointmentCalendarSync

# Sync an appointment to calendar
sync_service = AppointmentCalendarSync()
sync_service.sync_appointment_to_calendar(appointment)

# Update an appointment in calendar
sync_service.update_appointment_in_calendar(appointment)

# Delete an appointment from calendar
sync_service.delete_appointment_from_calendar(appointment)

# Sync all pending appointments
synced_count = sync_service.sync_all_appointments()
```

---

## AWS SES Email Service

### Overview
AWS Simple Email Service (SES) is used to send appointment notifications including confirmations, cancellations, and reminders.

### Features
- ✅ Appointment confirmation emails
- ✅ Cancellation notifications
- ✅ Appointment reminders (24 hours before)
- ✅ HTML and plain text templates
- ✅ Scalable and reliable email delivery

### Setup Instructions

1. **Create AWS Account**
   - Go to [AWS Console](https://aws.amazon.com/)
   - Create a new account or sign in

2. **Set up SES**
   - Go to SES Console
   - Verify email addresses or domain (sandbox mode requires email verification)
   - For production: Request production access from AWS support

3. **Create IAM User with SES Permissions**
   - Go to IAM Console
   - Create new user with **AmazonSesSendingAccess** policy
   - Save Access Key ID and Secret Access Key

4. **Configure in .env**
   ```env
   EMAIL_BACKEND=hospital_dashboard.integrations.email_service.AWSSESBackend
   EMAIL_FROM_ADDRESS=noreply@hospital.com
   AWS_REGION=us-east-1
   AWS_ACCESS_KEY_ID=your_access_key_here
   AWS_SECRET_ACCESS_KEY=your_secret_key_here
   ```

### Usage in Code

```python
from hospital_dashboard.integrations import EmailNotificationService

# Send confirmation email
EmailNotificationService.send_appointment_confirmation(appointment)

# Send cancellation email
EmailNotificationService.send_appointment_cancellation(
    appointment, 
    reason="Doctor unavailable"
)

# Send reminder email
EmailNotificationService.send_appointment_reminder(appointment, hours_before=24)
```

### Email Templates

Templates are located in `templates/emails/`:
- `appointment_confirmation.html` / `.txt`
- `appointment_cancellation.html` / `.txt`
- `appointment_reminder.html` / `.txt`

Customize these templates as needed.

---

## AWS Lambda Functions

### Overview
Lambda functions enable serverless, asynchronous processing of appointment operations. Perfect for sending emails and syncing to calendar without blocking the main application.

### Available Handlers

All Lambda handlers are in `hospital_dashboard/integrations/lambda_handlers.py`

#### 1. send_appointment_confirmation
**Purpose**: Send confirmation email when appointment is booked
**Trigger**: API call or SQS message
**Event Format**:
```json
{
    "appointment_id": 123,
    "action": "confirmation"
}
```

#### 2. send_appointment_reminder
**Purpose**: Send reminder email 24 hours before appointment
**Trigger**: Scheduled event (EventBridge)
**Event Format**:
```json
{
    "appointment_id": 123,
    "action": "reminder",
    "hours_before": 24
}
```

#### 3. sync_appointment_to_calendar
**Purpose**: Sync appointment to Google Calendar
**Trigger**: API call or SNS message
**Event Format**:
```json
{
    "appointment_id": 123,
    "action": "sync"
}
```

#### 4. cancel_appointment_notification
**Purpose**: Handle appointment cancellation with email and calendar cleanup
**Trigger**: API call or SNS message
**Event Format**:
```json
{
    "appointment_id": 123,
    "action": "cancel",
    "reason": "Doctor unavailable"
}
```

#### 5. batch_send_reminders
**Purpose**: Send reminders to all appointments scheduled for 24 hours from now
**Trigger**: Scheduled event (EventBridge) - run daily
**Event Format**: `{}` (no specific format)

#### 6. sync_all_appointments_to_calendar
**Purpose**: Sync all pending appointments to Google Calendar
**Trigger**: Scheduled event or on-demand
**Event Format**: `{}` (no specific format)

### Deployment to AWS Lambda

1. **Create Lambda Function**
   ```bash
   # In AWS Console:
   # Lambda → Create function
   # Name: hospital-appointment-confirmation
   # Runtime: Python 3.11
   ```

2. **Package Code**
   ```bash
   # Create deployment package
   pip install -r requirements.txt -t lambda_package/
   cp hospital_dashboard/integrations/lambda_handlers.py lambda_package/
   cd lambda_package && zip -r ../deployment.zip . && cd ..
   ```

3. **Upload to Lambda**
   - In AWS Console: Upload ZIP file
   - Set handler to: `lambda_handlers.send_appointment_confirmation`

4. **Configure Environment Variables**
   - Add all .env variables to Lambda environment
   - Ensure permissions for SES, PostgreSQL access, etc.

5. **Set up Triggers**
   - For confirmation: API Gateway or SQS
   - For reminders: EventBridge scheduled rule (daily)
   - For calendar sync: SNS topic or EventBridge

### Example: Setting up Scheduled Reminder

1. **Create EventBridge Rule**
   ```bash
   aws events put-rule --name daily-appointment-reminders --schedule-expression "cron(0 8 * * ? *)"
   ```

2. **Add Lambda as Target**
   ```bash
   aws events put-targets --rule daily-appointment-reminders \
     --targets "Id"="1","Arn"="<lambda-arn>","RoleArn"="<role-arn>"
   ```

---

## Configuration

### Environment Variables

**Database**
```env
DB_ENGINE=django.db.backends.postgresql
DB_NAME=hospital_dashboard
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

**Django**
```env
SECRET_KEY=your-secret-key-here
DEBUG=False  # Set to False in production
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

**Email (AWS SES)**
```env
EMAIL_BACKEND=hospital_dashboard.integrations.email_service.AWSSESBackend
EMAIL_FROM_ADDRESS=noreply@hospital.com
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
```

**Google Calendar**
```env
# Service Account (Production)
GOOGLE_SERVICE_ACCOUNT_JSON={"type": "service_account", ...}

# OAuth2 (Development)
GOOGLE_CREDENTIALS_PATH=credentials.json
GOOGLE_TOKEN_PATH=token.json
```

---

## Usage Examples

### Example 1: Automatic Email on Appointment Booking

```python
# In views.py
from hospital_dashboard.integrations import EmailNotificationService

# When appointment is created:
appointment = Appointment.objects.create(...)
EmailNotificationService.send_appointment_confirmation(appointment)
```

### Example 2: Sync Appointment to Calendar

```python
from hospital_dashboard.integrations.calendar_sync import AppointmentCalendarSync

sync_service = AppointmentCalendarSync()
if sync_service.sync_appointment_to_calendar(appointment):
    print("Synced successfully")
else:
    print("Sync failed")
```

### Example 3: Handle Cancellation with All Notifications

```python
from hospital_dashboard.integrations import EmailNotificationService
from hospital_dashboard.integrations.calendar_sync import AppointmentCalendarSync

# Send cancellation email
EmailNotificationService.send_appointment_cancellation(
    appointment,
    reason="Doctor unavailable"
)

# Remove from calendar
sync_service = AppointmentCalendarSync()
sync_service.delete_appointment_from_calendar(appointment)

# Update appointment status
appointment.status = 'cancelled'
appointment.save()
```

### Example 4: Using Lambda via AWS SDK

```python
import boto3
import json

lambda_client = boto3.client('lambda', region_name='us-east-1')

# Trigger confirmation email
response = lambda_client.invoke(
    FunctionName='hospital-appointment-confirmation',
    InvocationType='Event',  # Asynchronous
    Payload=json.dumps({
        'appointment_id': 123,
        'action': 'confirmation'
    })
)
```

---

## Deployment

### Local Development

1. **No Google Calendar/AWS Integration**
   - Leave GOOGLE_SERVICE_ACCOUNT_JSON empty
   - EmailNotificationService will fail silently

2. **With Google Calendar (OAuth2)**
   - Download `credentials.json`
   - First run will prompt for authentication

3. **With AWS SES**
   - Configure AWS credentials in .env
   - Ensure SES is in production mode (not sandbox)

### AWS EC2/Production Deployment

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Environment Variables**
   - Use AWS Systems Manager Parameter Store
   - Or set in EC2 user data script

3. **Run Migrations**
   ```bash
   python manage.py migrate
   ```

4. **Collect Static Files**
   ```bash
   python manage.py collectstatic --noinput
   ```

5. **Run Gunicorn**
   ```bash
   gunicorn hospital_dashboard.wsgi:application --bind 0.0.0.0:8000
   ```

### Docker Deployment

```dockerfile
FROM python:3.11

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV DJANGO_SETTINGS_MODULE=hospital_dashboard.settings
RUN python manage.py collectstatic --noinput

CMD ["gunicorn", "hospital_dashboard.wsgi:application", "--bind", "0.0.0.0:8000"]
```

---

## Troubleshooting

### Google Calendar Integration Not Working

**Issue**: Events not syncing to calendar

**Solutions**:
1. Check if GOOGLE_SERVICE_ACCOUNT_JSON is properly set
2. Verify service account has access to calendar
3. Check Django logs for detailed error messages
4. Test with: `python manage.py shell`
   ```python
   from hospital_dashboard.integrations import GoogleCalendarService
   service = GoogleCalendarService()
   print(service.service)  # Should not be None
   ```

### AWS SES Emails Not Sending

**Issue**: Emails not being sent

**Solutions**:
1. Check if AWS credentials are correct
2. Verify SES is in production mode (not sandbox)
3. Ensure email addresses are verified in SES
4. Check AWS CloudWatch logs
5. Test with: `python manage.py shell`
   ```python
   from django.core.mail import send_mail
   send_mail('Test', 'Test message', 'from@example.com', ['to@example.com'])
   ```

### Lambda Function Errors

**Issue**: Lambda invocation fails

**Solutions**:
1. Check Lambda logs in CloudWatch
2. Ensure environment variables are set in Lambda
3. Verify IAM permissions for Lambda
4. Test locally before deploying to Lambda

---

## Support & Documentation

- [Google Calendar API Docs](https://developers.google.com/calendar)
- [AWS SES Docs](https://docs.aws.amazon.com/ses/)
- [AWS Lambda Docs](https://docs.aws.amazon.com/lambda/)
- [Django Email Documentation](https://docs.djangoproject.com/en/6.0/topics/email/)
