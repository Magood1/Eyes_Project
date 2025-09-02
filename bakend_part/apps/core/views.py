from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny


# apps/core/views.py
from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.diagnosis.models import Diagnosis
from apps.users.models import Patient



class HealthCheckView(APIView):
    """
    نقطة نهاية بسيطة للتحقق من أن الخدمة تعمل.
    """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        return Response({"status": "ok"})
    


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    يعرض لوحة التحكم الرئيسية للطبيب المسجل دخوله.
    """
    template_name = "dashboard/main.html"    


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # جلب الإحصائيات الخاصة بالطبيب الحالي فقط
        patient_count = Patient.objects.filter(doctors=user).count()
        diagnosis_count = Diagnosis.objects.filter(physician=user).count()

        # جلب أحدث 5 تشخيصات للطبيب الحالي
        recent_diagnoses = Diagnosis.objects.filter(physician=user).select_related('patient').order_by('-created_at')[:5]

        context['counts'] = {
            "patients": patient_count,
            "diagnoses": diagnosis_count,
        }
        context['recent_diagnoses'] = recent_diagnoses
        return context
