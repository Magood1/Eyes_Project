# apps/diagnosis/urls_api.py

from rest_framework.routers import DefaultRouter
from.views import DiagnosisViewSet

router = DefaultRouter()
router.register(r'diagnoses', DiagnosisViewSet, basename='diagnosis')

urlpatterns = router.urls
