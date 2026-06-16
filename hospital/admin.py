from django.contrib import admin
from .models import (
    patient_info,
    doctor_infos,
    scheduled_appointments,
    DoctorSchedule
)

# =========================
# PATIENT ADMIN
# =========================
@admin.register(patient_info)
class PatientInfoAdmin(admin.ModelAdmin):
    list_display = (
        'user_name',
        'first_name',
        'last_name',
        'mobile_number',
        'city',
        'doctor',
        'status'
    )
    search_fields = ('user_name', 'first_name', 'last_name')


# =========================
# DOCTOR ADMIN
# =========================
@admin.register(doctor_infos)
class DoctorInfoAdmin(admin.ModelAdmin):
    list_display = (
        'first_name',
        'last_name',
        'specialist_in',
        'mobile_number',
        'city'
    )
    search_fields = ('first_name', 'last_name', 'specialist_in')


# =========================
# APPOINTMENT ADMIN
# =========================
@admin.register(scheduled_appointments)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        'patient',
        'doctor',
        'date',
        'time'
    )
    list_filter = ('date', 'doctor')
    search_fields = ('patient',)


# =========================
# DOCTOR SCHEDULE ADMIN (NEW)
# =========================
@admin.register(DoctorSchedule)
class DoctorScheduleAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'date', 'start_time', 'end_time')
    list_filter = ('doctor', 'date')
    search_fields = ('doctor__username',)