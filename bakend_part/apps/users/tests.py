# apps/users/tests.py
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

# احصل على نموذج المستخدم مرة واحدة في بداية الملف
User = get_user_model()

class UserAuthAPITests(APITestCase):
    """
    مجموعة اختبارات مخصصة لواجهات برمجة التطبيقات (API) الخاصة بالمصادقة والتسجيل.
    """
    def setUp(self):
        self.register_data = {
            "username": "testdoctor",
            "password": "strong-password-123",
            "password2": "strong-password-123",
            "email": "doctor@example.com",
            "first_name": "Test",
            "last_name": "Doctor",
            "role": User.Roles.DOCTOR
        }
        self.login_data = {
            "username": "testdoctor",
            "password": "strong-password-123"
        }

    def test_user_registration_successful(self):
        """تأكد من أنه يمكن للمستخدم التسجيل بنجاح."""
        url = reverse('user_register')
        response = self.client.post(url, self.register_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().username, 'testdoctor')

    def test_user_login_and_token_generation(self):
        """تأكد من أنه يمكن للمستخدم المسجل الحصول على توكن JWT."""
        User.objects.create_user(
            username=self.login_data['username'],
            password=self.login_data['password']
        )
        url = reverse('token_obtain_pair')
        response = self.client.post(url, self.login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_access_protected_api_endpoint_with_valid_token(self):
        """تأكد من إمكانية الوصول إلى مسار API محمي باستخدام توكن صالح."""
        user = User.objects.create_user(
            username=self.login_data['username'],
            password=self.login_data['password']
        )
        token_response = self.client.post(reverse('token_obtain_pair'), self.login_data, format='json')
        access_token = token_response.data['access']

        url = reverse('user_profile')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], user.username)
    
    def test_access_protected_api_endpoint_without_token(self):
        """تأكد من رفض الوصول إلى مسار API محمي بدون توكن."""
        url = reverse('user_profile')
        response = self.client.get(url)
        # بالنسبة لـ DRF، الاستجابة الصحيحة هي 401 Unauthorized عندما لا يتم توفير بيانات اعتماد
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) #status.HTTP_401_UNAUTHORIZED HTTP_403_FORBIDDEN


class FrontendTemplateTests(APITestCase):
    """
    مجموعة اختبارات مخصصة للصفحات والقوالب المُقدمة من الخادم (Server-Rendered).
    """
    def setUp(self):
        self.doctor = User.objects.create_user(
            username='frontend_doctor',
            password='password123',
            first_name='Test',
            last_name='Doctor',
            role=User.Roles.DOCTOR
        )
        # استخدم force_login للمصادقة في اختبارات الواجهة الأمامية (DTL)
        self.client.force_login(self.doctor)

    def test_dashboard_renders_for_logged_in_user(self):
        """تأكد من أن لوحة التحكم يتم عرضها بنجاح للمستخدم المسجل دخوله."""
        url = reverse('dashboard')
        response = self.client.get(url)
        
        # تحقق من أن الاستجابة ناجحة وأن القوالب الصحيحة تم استخدامها
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/main.html')
        self.assertTemplateUsed(response, 'layouts/app_base.html') # تحقق من الوراثة
        
        # تحقق من وجود بيانات السياق الأساسية
        self.assertIn('counts', response.context)
        self.assertIn('recent_diagnoses', response.context)