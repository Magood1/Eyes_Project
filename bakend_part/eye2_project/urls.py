"""
URL configuration for eye2_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))

# eye2_project/urls.py


from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.diagnosis.views import DiagnosisViewSet
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from django.conf import settings
from django.conf.urls.static import static
from apps.diagnosis.views import dashboard_view



from apps.core.views import DashboardView



router = DefaultRouter()
router.register(r'diagnoses', DiagnosisViewSet, basename='diagnosis')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('apps.users.urls')), # api/ but we will let it like as this now
    path('', include(router.urls)),  # api/ but we will let it like as this now

    
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    path('api/', include('apps.core.urls')),

    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),


    path('dashm', dashboard_view, name='dashboard'),
    
    # مسارات الواجهة الأمامية (DTL)
    path('', DashboardView.as_view(), name='dashboard'),
    path('users/', include('apps.users.urls_frontend')),
    path('diagnoses/', include('apps.diagnosis.urls_frontend')),

    # مسارات المصادقة المدمجة في Django
    path('accounts/', include('django.contrib.auth.urls')),



] 

# خدمة ملفات الوسائط أثناء التطوير
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


"""

# eye2_project/urls.py
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from apps.core.views import DashboardView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


# --- المسارات الأساسية للتطبيق ---
# هذه هي المسارات التي يتصفحها المستخدم (DTL)
urlpatterns = [
    # مسارات الإدارة
    path('admin/', admin.site.urls),

    # مسارات المصادقة المدمجة (login, logout, password_reset, etc.)
    path('accounts/', include('django.contrib.auth.urls')),

    # الصفحات الرئيسية للتطبيق
    path('', DashboardView.as_view(), name='dashboard'),
    path('frontend/users/', include('apps.users.urls_frontend')),
    path('frontend/diagnoses/', include('apps.diagnosis.urls_frontend')),
]

# --- مسارات واجهات برمجة التطبيقات (API) ---
# يتم تجميع جميع نقاط نهاية API تحت /api/ لتسهيل إدارتها وأمانها
api_urlpatterns = [
    # نقاط نهاية المستخدمين والمصادقة (JWT)
    path('users/', include('apps.users.urls_api')),
    
    # نقاط نهاية التشخيص
    path('', include('apps.diagnosis.urls_api')),

    # نقطة نهاية فحص الحالة
    path('', include('apps.core.urls')),
]

urlpatterns += [
    path('api/', include(api_urlpatterns)),
]

# --- مسارات توثيق API (Swagger / OpenAPI) ---
urlpatterns += [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

# --- خدمة ملفات الوسائط أثناء التطوير ---
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


