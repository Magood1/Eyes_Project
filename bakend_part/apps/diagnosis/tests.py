# apps/diagnosis/tests.py
from datetime import date
from django.test import TestCase
from unittest.mock import patch, MagicMock
from apps.diagnosis.services import DjangoDiagnosisOrchestrator, AIPipelineService
from apps.diagnosis.exceptions import ModelInferenceError, ModelLoadingError
from apps.diagnosis.models import Diagnosis, Patient
from django.core.files.uploadedfile import SimpleUploadedFile
import numpy as np
import uuid

class DiagnosisOrchestratorTests(TestCase):

    @patch.object(AIPipelineService, 'run_diagnosis')
    @patch('apps.diagnosis.services.Image.open')
    @patch('apps.diagnosis.repositories.DiagnosisRepository.get_by_id')
    @patch('apps.diagnosis.repositories.DiagnosisRepository.update_with_success')
    def test_successful_diagnosis(self, mock_update_success, mock_get_by_id, mock_image_open, mock_run_diagnosis):
        """
        اختبار مسار النجاح الكامل لخدمة DjangoDiagnosisOrchestrator
        """
        # إعداد النتائج الوهمية
        fake_result = {'final_diagnosis': 'Test Disease', 'confidence': 0.95}
        mock_run_diagnosis.return_value = fake_result
        mock_image_open.return_value = MagicMock()
        #mock_image_open.return_value.__array__ = lambda s: np.zeros((224, 224, 3))
        mock_image_open.return_value.__array__ = lambda *args: np.zeros((224, 224, 3))

        # إعداد كائن المريض والتشخيص
        diagnosis_id = uuid.uuid4()
        patient_id = uuid.uuid4()
        patient = Patient(id=patient_id, date_of_birth=date(1994, 7, 22), gender='MALE')
        
        diagnosis = Diagnosis(id=diagnosis_id, patient=patient)
        diagnosis.left_fundus_image = SimpleUploadedFile("left.jpg", b"fakeleftdata")
        diagnosis.right_fundus_image = SimpleUploadedFile("right.jpg", b"fakerightdata")
        mock_get_by_id.return_value = diagnosis

        # تنفيذ
        orchestrator = DjangoDiagnosisOrchestrator()
        orchestrator.run_diagnosis_from_django_model(diagnosis_id)

        # التحقق
        mock_run_diagnosis.assert_called_once()
        mock_update_success.assert_called_once_with(diagnosis_id, fake_result)

    @patch('apps.diagnosis.services.Image.open')
    @patch('apps.diagnosis.repositories.DiagnosisRepository.get_by_id')
    @patch('apps.diagnosis.repositories.DiagnosisRepository.update_with_failure')
    @patch.object(AIPipelineService, 'run_diagnosis', side_effect=ModelInferenceError("OOM"))
    def test_ai_failure_handled(self, mock_run_diagnosis, mock_update_failure, mock_get_by_id, mock_image_open):
        """
        التأكد من التعامل مع أخطاء نموذج الذكاء الاصطناعي
        """
        mock_image_open.return_value = MagicMock()
        #mock_image_open.return_value.__array__ = lambda s: np.zeros((224, 224, 3))
        mock_image_open.return_value.__array__ = lambda *args: np.zeros((224, 224, 3))
        
        diagnosis_id_2 = uuid.uuid4()
        patient_id_2 = uuid.uuid4()

        patient = Patient(id=patient_id_2, date_of_birth=date(1994, 7, 22), gender='FEMALE')
        diagnosis = Diagnosis(id=diagnosis_id_2, patient=patient)
        diagnosis.left_fundus_image = SimpleUploadedFile("left.jpg", b"xxx")
        diagnosis.right_fundus_image = SimpleUploadedFile("right.jpg", b"yyy")
        mock_get_by_id.return_value = diagnosis

        orchestrator = DjangoDiagnosisOrchestrator()
        orchestrator.run_diagnosis_from_django_model(diagnosis_id_2)

        mock_run_diagnosis.assert_called_once()
        mock_update_failure.assert_called_once_with(diagnosis_id_2, 'OOM')

    @patch('apps.diagnosis.repositories.DiagnosisRepository.get_by_id', return_value=None)
    @patch('apps.diagnosis.repositories.DiagnosisRepository.update_with_failure')
    def test_diagnosis_not_found(self, mock_update_failure, mock_get_by_id):
        """
        اختبار التعامل مع حالة عدم وجود سجل تشخيص
        """
        orchestrator = DjangoDiagnosisOrchestrator()
        orchestrator.run_diagnosis_from_django_model('invalid_id')

        mock_update_failure.assert_called_once()
        args = mock_update_failure.call_args[0]
        assert 'not found' in args[1]



"""
from django.test import TestCase
from unittest.mock import patch
from apps.diagnosis.services import DiagnosisOrchestrationService, VisionModelService, TabularModelService
from apps.diagnosis.exceptions import ModelInferenceError

class DiagnosisServiceTests(TestCase):

    @patch.object(TabularModelService, 'predict')
    @patch.object(VisionModelService, 'predict')
    def test_orchestration_service_success_path(self, mock_vision_predict, mock_tabular_predict):
        #اختبار مسار النجاح لمنسق التشخيص.
        mock_vision_predict.return_value = {"disease_probability": 0.8}
        mock_tabular_predict.return_value = {"final_diagnosis": "Test Disease", "confidence": 0.9}

        service = DiagnosisOrchestrationService()
        result = service.run_full_diagnosis(image_data=b'fake_image_bytes', demographics={})

        mock_vision_predict.assert_called_once()
        mock_tabular_predict.assert_called_once()
        self.assertEqual(result['final_diagnosis'], "Test Disease")

    @patch.object(VisionModelService, 'predict', side_effect=ModelInferenceError("GPU Out of Memory"))
    def test_orchestration_service_handles_inference_error(self, mock_vision_predict):
        #اختبار أن الخدمة تعالج الأخطاء القادمة من نماذج الذكاء الاصطناعي برشاقة.
        service = DiagnosisOrchestrationService()

        with self.assertRaises(ModelInferenceError):
            service.run_full_diagnosis(image_data=b'', demographics={})

        mock_vision_predict.assert_called_once()

"""
