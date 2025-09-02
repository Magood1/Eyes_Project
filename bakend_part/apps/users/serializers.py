# apps/users/serializers.py
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, Patient, Clinic, Appointment, TreatmentPlan, Bill
from apps.diagnosis.models import Diagnosis
from datetime import date



class UserRegisterSerializer(serializers.ModelSerializer):
    """Serializer لتسجيل مستخدم جديد."""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'password2', 'email', 'first_name', 'last_name', 'role', 'spicialzaton', 'phone')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        # استخدم `create_user` لضمان تجزئة كلمة المرور بشكل صحيح
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data.get('email', ''),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            role=validated_data.get('role', User.Roles.DOCTOR),
            spicialzaton=validated_data.get('spicialzaton', ''),
            phone=validated_data.get('phone', '')
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    """Serializer لعرض بيانات المستخدم (بدون معلومات حساسة)."""
    class Meta:
        model = User
        fields =  ('id', 'username','first_name', 'last_name',  'email', 'spicialzaton', 'phone' )


class ClinicSerializer(serializers.ModelSerializer):
    """Serializer للعيادات."""
    class Meta:
        model = Clinic
        fields = ('id', 'name', 'location', 'created_at')
        read_only_fields = ('id', 'created_at')



class PatientSerializer(serializers.ModelSerializer):
    """Serializer للمرضى، مع تضمين بيانات العيادة."""
    clinic = ClinicSerializer(read_only=True)
    clinic_id = serializers.UUIDField(write_only=True)
    age = serializers.IntegerField(read_only=True)

    class Meta:
        model = Patient
        fields = ('id', 'personal_photo','full_name', 'date_of_birth', 'gender', 'age', 'clinic', 'clinic_id',
                   'address','phone', 'insurance_info', 'contact_info', 'doctors')
        read_only_fields = ('id', 'clinic', 'doctors')
    
    def create(self, validated_data):
        # ربط الطبيب الذي أنشأ المريض تلقائيًا
        doctor = self.context['request'].user
        patient = super().create(validated_data)
        patient.doctors.add(doctor)
        return patient
    


class AppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    clinic_name = serializers.CharField(source='clinic.name', read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id', 'patient', 'clinic', 'scheduled_time', 'status',
            'notes', 'created_at', 'updated_at',
            'patient_name', 'clinic_name'
        ]
        read_only_fields = ['created_at', 'updated_at']


class TreatmentPlanSerializer(serializers.ModelSerializer):
    diagnosis_summary = serializers.CharField(source='diagnosis.summary', read_only=True)

    class Meta:
        model = TreatmentPlan
        fields = [
            'id', 'diagnosis', 'plan_details', 'medications', 'follow_up_required',
            'created_at', 'updated_at',
            'diagnosis_summary',
        ]
        read_only_fields = ['created_at', 'updated_at']


class BillSerializer(serializers.ModelSerializer):
    appointment_time = serializers.DateTimeField(source='appointment.scheduled_time', read_only=True)
    patient_name = serializers.CharField(source='appointment.patient.full_name', read_only=True)

    class Meta:
        model = Bill
        fields = [
            'id', 'appointment', 'amount', 'status', 'issued_at', 'paid_at',
            'appointment_time', 'patient_name'
        ]
        read_only_fields = ['issued_at', 'paid_at']

class DiagnosisMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Diagnosis
        fields = ['id', 'disease', 'summary', 'created_at']

class AppointmentMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ['id', 'clinic', 'scheduled_time', 'status']

class PatientFullProfileSerializer(serializers.ModelSerializer):
    appointments = AppointmentMiniSerializer(many=True, read_only=True, source='appointment_set')
    diagnoses = DiagnosisMiniSerializer(many=True, read_only=True, source='diagnosis_set')

    class Meta:
        model = Patient
        fields = [
            'id', 'full_name', 'date_of_birth', 'gender', 'phone_number', 'email',
            'medical_history', 'created_at', 'updated_at',
            'appointments', 'diagnoses'
        ]
        read_only_fields = ['created_at', 'updated_at']


