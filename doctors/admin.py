from django.contrib import admin
from .models import DoctorProfile, TimeSlot

# Register your models here.

@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ('get_doctor_name', 'specialization', 'is_available', 'created_at')
    list_filter = ('is_available', 'created_at')
    search_fields = ('user__first_name', 'user__last_name', 'specialization')
    readonly_fields = ('created_at', 'updated_at')

    def get_doctor_name(self, obj):
        return f"Dr. {obj.user.first_name} {obj.user.last_name}"
    get_doctor_name.short_description = "Doctor Name"


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'date', 'start_time', 'end_time', 'is_available')
    list_filter = ('is_available', 'date')
    search_fields = ('doctor__user__first_name', 'doctor__user__last_name')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'date'
