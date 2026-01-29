from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from hospital_dashboard.models import UserProfile


class Command(BaseCommand):
    help = 'Create test users for development'

    def handle(self, *args, **options):
        # Create test doctor
        doctor_user, created = User.objects.get_or_create(
            username='testdoctor',
            defaults={
                'email': 'doctor@test.com',
                'first_name': 'Test',
                'last_name': 'Doctor'
            }
        )
        
        if created:
            doctor_user.set_password('TestDoctor123')
            doctor_user.save()
        
        # Ensure profile exists with doctor role
        profile, _ = UserProfile.objects.get_or_create(user=doctor_user)
        profile.role = 'doctor'
        profile.save()
        
        self.stdout.write(
            self.style.SUCCESS(f'Doctor user created: testdoctor / TestDoctor123')
        )

        # Create test patient
        patient_user, created = User.objects.get_or_create(
            username='testpatient',
            defaults={
                'email': 'patient@test.com',
                'first_name': 'Test',
                'last_name': 'Patient'
            }
        )
        
        if created:
            patient_user.set_password('TestPatient123')
            patient_user.save()
        
        # Ensure profile exists with patient role
        profile, _ = UserProfile.objects.get_or_create(user=patient_user)
        profile.role = 'patient'
        profile.save()
        
        self.stdout.write(
            self.style.SUCCESS(f'Patient user created: testpatient / TestPatient123')
        )
