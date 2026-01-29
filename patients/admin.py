from django.contrib import admin
from .models import PatientProfile, Appointment

@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'phone', 'age', 'gender', 'created_at')
    list_filter = ('gender', 'created_at')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'phone')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Personal Information', {
            'fields': ('phone', 'age', 'gender', 'address')
        }),
        ('Medical Information', {
            'fields': ('medical_history',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    get_full_name.short_description = 'Name'


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('get_patient_name', 'get_doctor_name', 'get_appointment_date', 'get_appointment_time', 'status', 'booking_date')
    list_filter = ('status', 'booking_date', 'time_slot__date')
    search_fields = ('patient__user__first_name', 'patient__user__last_name', 'doctor__user__first_name', 'doctor__user__last_name')
    readonly_fields = ('created_at', 'updated_at', 'booking_date')
    fieldsets = (
        ('Appointment Details', {
            'fields': ('patient', 'doctor', 'time_slot', 'status')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('booking_date', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_patient_name(self, obj):
        return f"{obj.patient.user.first_name} {obj.patient.user.last_name}"
    get_patient_name.short_description = 'Patient'

    def get_doctor_name(self, obj):
        return f"Dr. {obj.doctor.user.first_name} {obj.doctor.user.last_name}"
    get_doctor_name.short_description = 'Doctor'

    def get_appointment_date(self, obj):
        return obj.time_slot.date
    get_appointment_date.short_description = 'Date'

    def get_appointment_time(self, obj):
        return f"{obj.time_slot.start_time} - {obj.time_slot.end_time}"
    get_appointment_time.short_description = 'Time'
