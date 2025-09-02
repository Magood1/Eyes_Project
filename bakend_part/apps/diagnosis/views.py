# # apps/diagnosis/views.py
# apps/diagnosis/views.py
from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from django.db import transaction
from django.views.generic import CreateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect, render
from rest_framework.permissions import IsAuthenticated

from .models import Diagnosis
from .serializers import DiagnosisCreateSerializer, DiagnosisDetailSerializer
from .tasks import process_diagnosis
from apps.users.models import Patient
from apps.diagnosis import serializers
from apps.users.permissions import IsOwnerOrAdmin
from .forms import DiagnosisUploadForm


def dashboard_view(request):
    return render(request, 'dashboard/dashboard.html')


class DiagnosisViewSet(mixins.CreateModelMixin,
                       mixins.RetrieveModelMixin,
                       viewsets.GenericViewSet):
    """
    ViewSet لإنشاء واسترجاع التشخيصات.
    يستخدم transaction.on_commit لضمان جدولة المهام بشكل آمن.
    """
    queryset = Diagnosis.objects.select_related('patient', 'physician').all()
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_serializer_class(self):
        if self.action == 'create':
            return DiagnosisCreateSerializer
        return DiagnosisDetailSerializer

    def perform_create(self, serializer):
        """
        يحفظ السجل المبدئي ويطلق مهمة Celery بشكل آمن بعد إتمام المعاملة.
        """
        patient_id = serializer.validated_data.pop('patient_id')
        try:
            patient = self.request.user.patients.get(id=patient_id)
        except Patient.DoesNotExist:
            raise serializers.ValidationError("You do not have permission for this patient.")

        # نضمن أن الحفظ وجدولة المهمة يحدثان بشكل ذري
        with transaction.atomic():
            diagnosis = serializer.save(
                patient=patient,
                physician=self.request.user
            )
            # جدولة المهمة لتنفذ فقط بعد نجاح COMMIT في قاعدة البيانات
            transaction.on_commit(
                lambda: process_diagnosis.delay(diagnosis_id=str(diagnosis.id))
            )

class DiagnosisCreateView(LoginRequiredMixin, CreateView):
    """
    يعالج طلب إنشاء تشخيص جديد من نموذج ويب، مع جدولة آمنة للمهام.
    """
    model = Diagnosis
    form_class = DiagnosisUploadForm
    
    def get_success_url(self):
        return reverse_lazy('diagnosis-detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        form.instance.physician = self.request.user
        
        # استخدام transaction.atomic لضمان سلامة العملية
        with transaction.atomic():
            self.object = form.save()
            # جدولة المهمة بشكل آمن
            transaction.on_commit(
                lambda: process_diagnosis.delay(diagnosis_id=str(self.object.id))
            )
        
        return redirect(self.get_success_url())

class DiagnosisDetailView(LoginRequiredMixin, DetailView):
    """يعرض تفاصيل تشخيص واحد."""
    model = Diagnosis
    template_name = 'diagnosis/diagnosis_detail.html'
    context_object_name = 'diagnosis'

    def get_queryset(self):
        return Diagnosis.objects.filter(physician=self.request.user)
    
# from rest_framework import viewsets, mixins, status
# from rest_framework.response import Response
# from .models import Diagnosis
# from .serializers import DiagnosisCreateSerializer, DiagnosisDetailSerializer
# from .tasks import process_diagnosis
# from apps.users.models import Patient
# from apps.diagnosis import serializers
# from apps.users.permissions import IsOwnerOrAdmin
# from rest_framework.permissions import IsAuthenticated
# from django.db import transaction
# from django.shortcuts import render

# # apps/diagnosis/views.py
# from django.shortcuts import redirect
# from django.views.generic import CreateView, DetailView
# from django.contrib.auth.mixins import LoginRequiredMixin
# from django.urls import reverse_lazy
# from .models import Diagnosis
# from .forms import DiagnosisUploadForm
# from .tasks import process_diagnosis



# def dashboard_view(request):
#     return render(request, 'dashboard/dashboard.html')


# class DiagnosisViewSet(mixins.CreateModelMixin,
#                        mixins.RetrieveModelMixin,
#                        viewsets.GenericViewSet):
#     """
#     ViewSet لإنشاء واسترجاع التشخيصات.
#     - POST: ينشئ طلب تشخيص ويطلق مهمة في الخلفية.
#     - GET: يسترجع حالة ونتيجة طلب معين.
#     """
#     queryset = Diagnosis.objects.select_related('patient', 'physician').all()
#     permission_classes = [IsAuthenticated, IsOwnerOrAdmin]


#     def get_serializer_class(self):
#         if self.action == 'create':
#             return DiagnosisCreateSerializer
#         return DiagnosisDetailSerializer

#     def perform_create(self, serializer):
#         """
#         يحفظ السجل المبدئي ويطلق مهمة Celery بشكل آمن بعد إتمام المعاملة.
#         """
#         patient_id = serializer.validated_data.pop('patient_id')
#         try:
#             patient = self.request.user.patients.get(id=patient_id)
#         except Patient.DoesNotExist:
#             raise serializers.ValidationError("You do not have permission for this patient.")

#         # نضمن أن الحفظ وجدولة المهمة يحدثان بشكل ذري
#         with transaction.atomic():
#             diagnosis = serializer.save(
#                 patient=patient,
#                 physician=self.request.user
#             )
#             # جدولة المهمة لتنفذ فقط بعد نجاح COMMIT في قاعدة البيانات
#             transaction.on_commit(
#                 lambda: process_diagnosis.delay(diagnosis_id=str(diagnosis.id))
#             )


# class DiagnosisCreateView(LoginRequiredMixin, CreateView):
#     """
#     يعالج طلب إنشاء تشخيص جديد من نموذج ويب.
#     """
#     model = Diagnosis
#     form_class = DiagnosisUploadForm
    
#     def get_success_url(self):
#         # إعادة التوجيه إلى صفحة تفاصيل التشخيص بعد الإنشاء
#         return reverse_lazy('diagnosis-detail', kwargs={'pk': self.object.pk})

#     def form_valid(self, form):
#         form.instance.physician = self.request.user
        
#         # استخدام transaction.atomic لضمان سلامة العملية
#         with transaction.atomic():
#             self.object = form.save()
#             # جدولة المهمة بشكل آمن
#             transaction.on_commit(
#                 lambda: process_diagnosis.delay(diagnosis_id=str(self.object.id))
#             )

#         return redirect(self.get_success_url())


# class DiagnosisDetailView(LoginRequiredMixin, DetailView):
#     """يعرض تفاصيل تشخيص واحد."""
#     model = Diagnosis
#     template_name = 'diagnosis/diagnosis_detail.html'
#     context_object_name = 'diagnosis'

#     def get_queryset(self):
#         # ضمان أن الطبيب يمكنه فقط عرض تشخيصاته
#         return Diagnosis.objects.filter(physician=self.request.user)