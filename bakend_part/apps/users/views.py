# apps/users/views.py
from rest_framework import generics, viewsets, filters
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser

from apps.diagnosis.models import Diagnosis
from .serializers import (UserRegisterSerializer, UserSerializer,
                           ClinicSerializer,PatientSerializer, AppointmentSerializer,
                             TreatmentPlanSerializer, BillSerializer, PatientFullProfileSerializer)

from rest_framework.exceptions import PermissionDenied
from .models import User,  Clinic, Patient, Appointment, TreatmentPlan, Bill
from .permissions import IsAdmin, IsAssignedDoctorOrReadOnly, IsDoctor, IsOwnerOrAdmin
from apps.core.audit import log_patient_access
from drf_spectacular.utils import extend_schema

@extend_schema(
    summary="Register a new user (Doctor or Admin)",
    description="Creates a new user account. Any user can register."
)
class UserRegisterView(generics.CreateAPIView):
    """عرض API لتسجيل مستخدم جديد."""
    queryset = User.objects.all()
    permission_classes = (AllowAny,) # أي شخص يمكنه التسجيل
    serializer_class = UserRegisterSerializer


class UserProfileView(generics.RetrieveAPIView):
    """
    عرض API محمي لجلب ملف تعريف المستخدم المسجل دخوله.
    هذا endpoint مثالي لاختبار صلاحيات JWT.
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user
    

class ClinicViewSet(viewsets.ModelViewSet):
    """ViewSet لإدارة العيادات. الوصول مقيد للمسؤولين."""
    queryset = Clinic.objects.all()
    serializer_class = ClinicSerializer
    #permission_classes = [IsAdmin, IsDoctor] # فقط المسؤول يمكنه إدارة العيادات


class PatientViewSet(viewsets.ModelViewSet):
    """ViewSet لإدارة المرضى."""
    queryset = Patient.objects.all()    # ← هذه السطر ضروري

    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['full_name'] 

    def get_queryset(self):
        """
        - المسؤولون يرون جميع المرضى.
        - الأطباء يرون فقط المرضى المرتبطين بهم.
        """
        user = self.request.user
        if user.role == User.Roles.ADMIN:
            return Patient.objects.all()
        return user.patients.all() # استرجاع المرضى المرتبطين بالطبيب


    def perform_create(self, serializer):
        patient = serializer.save()
        patient.doctors.add(self.request.user) # ربط الطبيب الحالي بالمريض
    

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        log_patient_access(request.user, instance, "retrieved")
        return super().retrieve(request, *args, **kwargs)
    

class AppointmentViewSet(viewsets.ModelViewSet):
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Appointment.objects.select_related('patient', 'doctor').all()
        return user.appointments.select_related('patient', 'doctor').all()

    def perform_create(self, serializer):
        serializer.save(doctor=self.request.user)


class TreatmentPlanViewSet(viewsets.ModelViewSet):
    serializer_class = TreatmentPlanSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return TreatmentPlan.objects.all()
        return TreatmentPlan.objects.filter(diagnosis__patient__doctor=user)

    def perform_create(self, serializer):
        # نضمن أن التشخيص ينتمي للطبيب الحالي
        diagnosis = serializer.validated_data['diagnosis']
        if diagnosis.patient.doctor != self.request.user:
            raise PermissionDenied("You do not have permission to create a treatment plan for this diagnosis.")
        serializer.save()


class BillViewSet(viewsets.ModelViewSet):
    serializer_class = BillSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Bill.objects.all()
        return Bill.objects.filter(appointment__patient__doctor=user)

    def perform_create(self, serializer):
        appointment = serializer.validated_data['appointment']
        if appointment.patient.doctor != self.request.user:
            raise PermissionDenied("You do not have permission to create a bill for this appointment.")
        serializer.save()


class PatientFullProfileViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PatientFullProfileSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        user = self.request.user
        base_qs = user.patients if not user.is_staff else Patient.objects.all()
        
        # استخدام prefetch_related لتحميل كل البيانات المرتبطة في استعلامين فقط!
        return base_qs.prefetch_related(
            'appointments__bills', 
            'diagnoses__treatment_plan'
        )
    

# apps/users/views.py
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Patient
from .forms import PatientForm
from apps.diagnosis.forms import DiagnosisUploadForm

class PatientListView(LoginRequiredMixin, ListView):
    """يعرض قائمة المرضى المرتبطين بالطبيب الحالي."""
    model = Patient
    template_name = 'patients/patient_list.html'
    context_object_name = 'patients'
    paginate_by = 10  # ترقيم الصفحات

    def get_queryset(self):
        # تصفية المرضى لعرض مرضى الطبيب الحالي فقط
        return Patient.objects.filter(doctors=self.request.user).order_by('full_name')

class PatientDetailView(LoginRequiredMixin, DetailView):
    """يعرض التفاصيل الكاملة لمريض واحد."""
    model = Patient
    template_name = 'patients/patient_detail.html'
    context_object_name = 'patient'

    def get_queryset(self):
        # ضمان أن الطبيب يمكنه فقط عرض مرضاه
        return Patient.objects.filter(doctors=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        patient = self.get_object()
        # إضافة قائمة التشخيصات الخاصة بالمريض إلى السياق
        context['diagnoses'] = Diagnosis.objects.filter(patient=patient).order_by('-created_at')
        # إضافة نموذج رفع التشخيص إلى السياق
        context['upload_form'] = DiagnosisUploadForm(initial={'patient': patient})
        return context



class PatientCreateView(LoginRequiredMixin, CreateView):
    """عرض لإنشاء مريض جديد."""
    model = Patient
    form_class = PatientForm
    template_name = 'patients/patient_form.html'
    success_url = reverse_lazy('patient-list') # إعادة التوجيه إلى قائمة المرضى بعد النجاح

    def form_valid(self, form):
        # ربط المريض بالطبيب الحالي تلقائيًا
        patient = form.save()
        patient.doctors.add(self.request.user)
        return super().form_valid(form)
    
