from django.apps import AppConfig


class HospitalDashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hospital_dashboard'

    def ready(self):
        import hospital_dashboard.models  # This will register the signals
