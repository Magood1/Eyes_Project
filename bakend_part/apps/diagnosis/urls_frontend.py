# apps/diagnosis/urls_frontend.py
from django.urls import path
from .views import DiagnosisCreateView, DiagnosisDetailView

urlpatterns = [
    path('create/', DiagnosisCreateView.as_view(), name='diagnosis-create'),
    path('<uuid:pk>/', DiagnosisDetailView.as_view(), name='diagnosis-detail'),
]
