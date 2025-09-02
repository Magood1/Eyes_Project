# apps/users/models.py
import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone


class User(AbstractUser):
    """
    نموذج المستخدم المخصص الذي يوسع النموذج الافتراضي في Django.
    ملاحظة: حقول first_name, last_name, email موجودة بالفعل في AbstractUser.
    """
    class Roles(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        DOCTOR = "DOCTOR", "Doctor"

    # الحقول الإضافية
    role = models.CharField(
        max_length=10,
        choices=Roles.choices,
        default=Roles.DOCTOR
    )
    spicialzaton = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=10, blank=True)

class Clinic(models.Model):
    """يمثل عيادة أو مستشفى."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Patient(models.Model):
    """يمثل سجل المريض."""
    class Gender(models.TextChoices):
        MALE = "MALE", "Male"
        FEMALE = "FEMALE", "Female"
        OTHER = "OTHER", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=50)
    date_of_birth = models.DateField(default=timezone.now)
    phone = models.CharField(max_length=10, blank=True)
    address = models.CharField(max_length=255, blank=True)
    gender = models.CharField(max_length=10, choices=Gender.choices)
    insurance_info = models.CharField(max_length=255, blank=True)
    contact_info = models.CharField(max_length=255, blank=True)
    personal_photo = models.ImageField(upload_to='patient_images', blank=True)
    clinic = models.ForeignKey(Clinic, on_delete=models.SET_NULL, null=True, related_name="patients")
    
    # علاقة المريض بالأطباء (متعدد إلى متعدد)
    doctors = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="patients",
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def age(self):
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))

    def __str__(self):
        return self.full_name

class Appointment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="appointments")
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="appointments")
    appointment_datetime = models.DateTimeField()
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ('patient', 'doctor', 'appointment_datetime')

class TreatmentPlan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    diagnosis = models.OneToOneField('diagnosis.Diagnosis', on_delete=models.CASCADE, related_name="treatment_plan")
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="treatment_plans")
    medication = models.TextField()
    instructions = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class Bill(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name="bills")
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="bills")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)