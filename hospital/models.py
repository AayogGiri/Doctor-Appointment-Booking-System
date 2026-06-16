from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# ===============================
# DOCTOR PROFILE MODEL
# ===============================
class doctor_infos(models.Model):

    doctor = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    email = models.CharField(max_length=320)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)

    province = models.CharField(max_length=20)
    city = models.CharField(max_length=20)
    address = models.CharField(max_length=100)

    sex = models.CharField(max_length=10)
    mobile_number = models.CharField(max_length=10)

    specialist_in = models.CharField(max_length=50)
    profile_description = models.TextField(blank=True, null=True, help_text="Short description of the doctor")

    profile_pic = models.ImageField(
        upload_to='doctors/',
        blank=True,
        null=True
    )

    def __str__(self):
        return (
            self.first_name +
            " " +
            self.last_name +
            " - " +
            self.specialist_in
        )


# ===============================
# DOCTOR AVAILABLE SCHEDULE MODEL
# ===============================
class DoctorSchedule(models.Model):

    doctor = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    is_booked = models.BooleanField(
        default=False
    )

    def __str__(self):
        return (
            f"{self.doctor.username} | "
            f"{self.date} | "
            f"{self.start_time}"
        )
    
class SystemSetting(models.Model):
    slot_duration = models.IntegerField(default=20)  # minutes

    def __str__(self):
        return f"{self.slot_duration} min"    


# ===============================
# FINAL BOOKED APPOINTMENTS
# ===============================
class scheduled_appointments(models.Model):

    doctor = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    patient = models.CharField(
        max_length=50,
        default=""
    )

    date = models.DateField()
    time = models.TimeField()

    reason = models.CharField(
        max_length=60,
        default=""
    )

    symptoms = models.CharField(
        max_length=100,
        default=""
    )

    email_id = models.CharField(
        max_length=320,
        default=""
    )

    mobile_number = models.CharField(
        max_length=10
    )

    booked_at = models.DateTimeField(
        auto_now_add=True
    )

    # ── Priority Scheduling Fields ──────────────────────────
    EMERGENCY_CHOICES = [
        (1, 'Normal'),
        (2, 'Urgent'),
        (3, 'Critical'),
    ]

    emergency_level = models.IntegerField(
        choices=EMERGENCY_CHOICES,
        default=1
    )

    age = models.IntegerField(default=30)

    priority_score = models.IntegerField(default=0)
    # ────────────────────────────────────────────────────────

    class Meta:
        verbose_name_plural = "Scheduled Appointments"

    def calculate_priority(self):
        """
        Priority formula:
          - Emergency Level  : level * 5
          - Age factor       : (age / 10) * 2
          - Waiting time     : minutes since booking, capped at 120 min / 10
          - Critical override: +50 if emergency_level == 3
        """
        from django.utils import timezone

        # Emergency factor
        emergency_score = self.emergency_level * 5

        # Age factor
        age_score = (self.age / 10) * 2

        # Waiting time factor (capped so it never overrides emergency status)
        if self.booked_at:
            waiting_minutes = (timezone.now() - self.booked_at).total_seconds() / 60
        else:
            waiting_minutes = 0
        waiting_minutes = min(waiting_minutes, 120)   # cap at 2 hours
        waiting_score = waiting_minutes / 10

        score = emergency_score + age_score + waiting_score

        # Critical override bonus
        if self.emergency_level == 3:
            score += 50

        return round(score, 2)

    def save(self, *args, **kwargs):
        # For new records booked_at is not set yet — save first, then update score
        is_new = self.pk is None
        if is_new:
            super().save(*args, **kwargs)
            self.priority_score = self.calculate_priority()
            # Only update the score field to avoid recursion
            type(self).objects.filter(pk=self.pk).update(
                priority_score=self.priority_score
            )
        else:
            self.priority_score = self.calculate_priority()
            super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.patient} booked "
            f"{self.doctor.username} "
            f"on {self.date}"
        )


# ===============================
# PATIENT PROFILE MODEL
# ===============================
class patient_info(models.Model):

    user_name = models.CharField(
        primary_key=True,
        max_length=150
    )

    email_id = models.CharField(
        max_length=320,
        default=""
    )

    first_name = models.CharField(
        max_length=20
    )

    last_name = models.CharField(
        max_length=20
    )

    mobile_number = models.CharField(
        max_length=10
    )

    province = models.CharField(
        max_length=20
    )

    city = models.CharField(
        max_length=20,
        default=""
    )

    address = models.CharField(
        max_length=100,
        default=""
    )

    sex = models.CharField(
        max_length=10,
        blank=True,
        null=True
    )

    dob = models.DateField(
        blank=True,
        null=True
    )

    reason = models.CharField(
        max_length=60,
        default=""
    )

    symptoms = models.CharField(
        max_length=100,
        default=""
    )

    current_medication_list = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        default=""
    )

    emergency_first_name = models.CharField(
        max_length=30,
        default=""
    )

    emergency_last_name = models.CharField(
        max_length=30,
        default=""
    )

    emergency_relationship = models.CharField(
        max_length=20,
        default=""
    )

    emergency_mobile_number = models.CharField(
        max_length=10,
        blank=True,
        null=True
    )

    doctor = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    status = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.first_name + " " + self.last_name