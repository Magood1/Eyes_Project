# apps/users/urls_frontend.py
from django.urls import path
from .views import PatientListView, PatientDetailView, PatientCreateView

urlpatterns = [
    path('patients/', PatientListView.as_view(), name='patient-list'),
    path('patients/add/', PatientCreateView.as_view(), name='patient-add'),
    path('patients/<uuid:pk>/', PatientDetailView.as_view(), name='patient-detail'),
]