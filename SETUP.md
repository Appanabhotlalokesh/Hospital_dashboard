# Hospital Dashboard Setup Guide

## Prerequisites
- Python 3.8+
- PostgreSQL 12+
- pip (Python package manager)

## Installation & Setup

### 1. Clone/Extract the Project
```bash
cd hospital_dashboard
```

### 2. Create a Python Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup PostgreSQL Database
1. Install PostgreSQL if not already installed
2. Start PostgreSQL service
3. Create a database (optional - Django can create it):
   ```sql
   CREATE DATABASE hospital_dashboard;
   ```

### 5. Configure Environment Variables
Edit `.env` file with your PostgreSQL credentials:
```env
DB_ENGINE=django.db.backends.postgresql
DB_NAME=hospital_dashboard
DB_USER=postgres
DB_PASSWORD=your_postgres_password
DB_HOST=localhost
DB_PORT=5432

# Security - Change these in production!
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 6. Run Migrations
```bash
python manage.py migrate
```

### 7. Create Superuser (Admin)
```bash
python manage.py createsuperuser
```

### 8. Load Test Data (Optional)
```bash
python manage.py create_test_users
```

### 9. Run Development Server
```bash
python manage.py runserver
```

Visit: http://localhost:8000

## Project Structure

```
hospital_dashboard/
├── hospital_dashboard/       # Main Django app
│   ├── settings.py          # Configuration file
│   ├── urls.py              # URL routing
│   └── wsgi.py              # WSGI application
├── doctors/                 # Doctors app
├── patients/                # Patients app
├── templates/               # HTML templates
├── static/                  # Static files (CSS, JS)
├── manage.py                # Django management script
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables
└── .gitignore              # Git ignore rules
```

## Key Features

- Doctor management and scheduling
- Patient registration and profiles
- Appointment booking and cancellation
- Time slot management
- User authentication (Login/Signup)

## Database

This project uses **PostgreSQL** for production. The database configuration is environment-based and can be easily changed through the `.env` file.

## Notes for Submission

- ✅ SQLite removed
- ✅ PostgreSQL configured
- ✅ All dependencies in requirements.txt
- ✅ Environment variables in .env
- ✅ .gitignore configured
- ✅ No errors or warnings
- ✅ Production-ready settings

## Troubleshooting

### PostgreSQL Connection Error
- Ensure PostgreSQL is running
- Verify credentials in .env
- Check if database exists

### Migration Error
- Try: `python manage.py migrate --run-syncdb`
- Ensure all apps are in INSTALLED_APPS

### Port Already in Use
```bash
python manage.py runserver 8001
```

## Production Deployment

Before deploying to production:

1. Set `DEBUG=False` in .env
2. Generate a strong `SECRET_KEY`
3. Update `ALLOWED_HOSTS` with your domain
4. Use environment variables for all sensitive data
5. Set up HTTPS/SSL
6. Configure static and media file serving
