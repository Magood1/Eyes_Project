# # # apps/diagnosis/services.py
# FILE: apps/diagnosis/services.py

import os
import numpy as np
from PIL import Image
import logging
from typing import Dict

from apps.diagnosis.ai_pipeline.service import DiagnosisService as AIPipelineService
from .repositories import DiagnosisRepository
from .exceptions import ModelInferenceError, ModelLoadingError

logger = logging.getLogger(__name__)

# --- Singleton Pattern Implementation ---
# قاموس لتخزين نسخة واحدة من المنسق لكل عملية عامل (worker process)
# هذا يضمن أن نماذج الذكاء الاصطناعي الثقيلة يتم تحميلها مرة واحدة فقط لكل عامل.
_ORCHESTRATOR_CACHE: Dict[int, 'DjangoDiagnosisOrchestrator'] = {}

def get_orchestrator() -> 'DjangoDiagnosisOrchestrator':
    """
    دالة مساعدة للحصول على نسخة Singleton من المنسق.
    """
    pid = os.getpid()
    if pid not in _ORCHESTRATOR_CACHE:
        logger.info(f"Initializing DjangoDiagnosisOrchestrator for worker process PID: {pid}...")
        _ORCHESTRATOR_CACHE[pid] = DjangoDiagnosisOrchestrator()
        logger.info(f"Orchestrator for PID: {pid} is ready.")
    return _ORCHESTRATOR_CACHE[pid]
# -----------------------------------------

class DjangoDiagnosisOrchestrator:
    """
    غلاف (Wrapper) حول خدمة الذكاء الاصطناعي لدمجها مع Django.
    مسؤول عن جلب البيانات من نماذج Django، وتمريرها إلى خط الأنابيب، وإرجاع النتائج.
    
    ملاحظة: لا تقم بإنشاء نسخ من هذه الفئة مباشرة، استخدم دالة get_orchestrator()
    للاستفادة من نمط Singleton.
    """
    def __init__(self):
        # تهيئة خدمة الذكاء الاصطناعي الأساسية. سيتم استدعاء هذا مرة واحدة فقط لكل عامل.
        self.ai_service = AIPipelineService()
        self.repo = DiagnosisRepository()

    def _preprocess_image_for_pipeline(self, image_field) -> np.ndarray:
        """يقرأ ImageField من Django ويحوله إلى مصفوفة NumPy."""
        try:
            image = Image.open(image_field)
            # قد تحتاج إلى تحويلات إضافية هنا إذا لم تكن جزءًا من خط الأنابيب
            # مثال: image = image.convert('RGB')
            return np.array(image)
        except Exception as e:
            logger.error(f"Failed to preprocess image {image_field.name}: {e}", exc_info=True)
            raise IOError(f"Could not read or process image file: {image_field.name}")

    def run_diagnosis_from_django_model(self, diagnosis_id: str) -> dict:
        """
        ينفذ التشخيص الكامل باستخدام سجل Diagnosis من قاعدة البيانات.
        يعيد قاموس النتائج عند النجاح، أو يثير استثناءً عند الفشل.
        """
        try:
            diagnosis_record = self.repo.get_by_id(diagnosis_id)
            if not diagnosis_record:
                # هذا خطأ فادح غير قابل للاسترداد يجب أن يوقف المهمة
                raise ValueError(f"Diagnosis record with ID {diagnosis_id} not found.")

            logger.info(f"Preparing inputs for diagnosis_id={diagnosis_id}")
            left_eye_img = self._preprocess_image_for_pipeline(diagnosis_record.left_fundus_image)
            right_eye_img = self._preprocess_image_for_pipeline(diagnosis_record.right_fundus_image)
            
            patient = diagnosis_record.patient
            demographics = {
                "age": patient.age,
                "gender": 1 if patient.gender == 'FEMALE' else 0
            }

            logger.info(f"Running AI pipeline for diagnosis_id={diagnosis_id}")
            result_dict = self.ai_service.run_diagnosis(
                left_eye_img=left_eye_img,
                right_eye_img=right_eye_img,
                demographics=demographics
            )
            
            logger.info(f"AI pipeline completed successfully for diagnosis_id={diagnosis_id}")
            return result_dict

        except (ModelInferenceError, ModelLoadingError, ValueError, IOError) as e:
            # التقط الأخطاء المتوقعة وسجلها وأثرها مجددًا
            logger.error(f"A predictable error occurred during diagnosis for {diagnosis_id}: {e}", exc_info=True)
            raise
        except Exception as e:
            # التقط أي أخطاء أخرى غير متوقعة
            logger.error(f"An unexpected system error occurred during diagnosis for {diagnosis_id}: {e}", exc_info=True)
            # أثر الخطأ مجددًا ليتم التعامل معه كخطأ قابل لإعادة المحاولة في طبقة المهام
            raise

        
# # apps/diagnosis/services.py
# from apps.diagnosis.exceptions import ModelInferenceError, ModelLoadingError
# from apps.diagnosis.ai_pipeline.service import DiagnosisService as AIPipelineService
# from apps.diagnosis.repositories import DiagnosisRepository
# import numpy as np
# from PIL import Image
# import logging

# logger = logging.getLogger(__name__)

# # ... (VisionModelService and TabularModelService remain the same) ...
        
# from apps.diagnosis.exceptions import ModelInferenceError, ModelLoadingError
# from apps.diagnosis.ai_pipeline.service import DiagnosisService as AIPipelineService
# from apps.diagnosis.repositories import DiagnosisRepository
# import numpy as np
# from PIL import Image

# # سنقوم بمحاكاة تحميل النموذج حاليًا
# # from tensorflow.keras.models import load_model 

# class VisionModelService:
#     """خدمة مسؤولة عن نموذج الرؤية (الصور)."""
#     _model = None

#     def __init__(self, model_path: str):
#         self.model_path = model_path
#         # التحميل المتأخر (Lazy Loading) للمساعدة في سرعة بدء التشغيل
#         if VisionModelService._model is None:
#             print(f"INFO: Loading vision model from {self.model_path}...")
#             # VisionModelService._model = load_model(self.model_path) # <-- سيتم تفعيل هذا لاحقًا
#             VisionModelService._model = "mock_vision_model" # محاكاة حالية

#     def predict(self, image_data) -> dict:
#         """يشغل التنبؤ على صورة واحدة."""
#         try:
#             # predictions = self._model.predict(image_data)
#             print("INFO: Vision model predicting...")
#             # محاكاة للإخراج
#             return {"disease_probability": 0.85, "features": [0.1, 0.2, 0.7]}
#         except Exception as e:
#             raise ModelInferenceError(f"Vision model prediction failed: {e}")

# class TabularModelService:
#     """خدمة مسؤولة عن النموذج الجدولي."""
#     def predict(self, vision_output: dict, demographic_data: dict) -> dict:
#         """يُرجع التشخيص النهائي بناءً على مخرجات الرؤية والبيانات الديموغرافية."""
#         try:
#             print("INFO: Tabular model predicting...")
#             # هنا، سيتم دمج المدخلات وتمريرها إلى نموذج جدولي (مثل scikit-learn)
#             # محاكاة للإخراج
#             confidence = vision_output.get("disease_probability", 0) * 0.9  # مثال
#             return {"final_diagnosis": "High-Risk Glaucoma", "confidence": confidence}
#         except Exception as e:
#             raise ModelInferenceError(f"Tabular model prediction failed: {e}")


# class DjangoDiagnosisOrchestrator:
#     """
#     غلاف (Wrapper) حول خدمة الذكاء الاصطناعي لدمجها مع Django.
#     مسؤول عن تنسيق خط أنابيب الذكاء الاصطناعي، وإرجاع النتائج أو إثارة الاستثناءات.
#     """
#     def __init__(self):
#         self.ai_service = AIPipelineService()
#         self.repo = DiagnosisRepository()

#     def _preprocess_image_for_pipeline(self, image_field) -> np.ndarray:
#         image = Image.open(image_field)
#         return np.array(image)

#     def run_diagnosis_from_django_model(self, diagnosis_id: str) -> dict:
#         """
#         ينفذ التشخيص الكامل ويعيد قاموس النتائج عند النجاح،
#         أو يثير استثناءً عند الفشل.
#         """
#         try:
#             diagnosis_record = self.repo.get_by_id(diagnosis_id)
#             if not diagnosis_record:
#                 # هذا خطأ فادح يجب أن يوقف المهمة
#                 raise ValueError(f"Diagnosis record with ID {diagnosis_id} not found.")

#             logger.info(f"Preparing AI pipeline inputs for diagnosis_id={diagnosis_id}")
#             left_eye_img = self._preprocess_image_for_pipeline(diagnosis_record.left_fundus_image)
#             right_eye_img = self._preprocess_image_for_pipeline(diagnosis_record.right_fundus_image)
            
#             patient = diagnosis_record.patient
#             demographics = {
#                 "age": patient.age,
#                 "gender": 1 if patient.gender == 'FEMALE' else 0
#             }

#             logger.info(f"Running AI pipeline for diagnosis_id={diagnosis_id}")
#             result_dict = self.ai_service.run_diagnosis(
#                 left_eye_img=left_eye_img,
#                 right_eye_img=right_eye_img,
#                 demographics=demographics
#             )
            
#             logger.info(f"AI pipeline completed successfully for diagnosis_id={diagnosis_id}")
#             return result_dict

#         except (ModelInferenceError, ModelLoadingError) as e:
#             logger.error(f"AI_ERROR during diagnosis for {diagnosis_id}: {e}")
#             # إعادة إثارة الاستثناء ليتم التقاطه بواسطة مهمة Celery
#             raise
#         except Exception as e:
#             logger.error(f"SYSTEM_ERROR during diagnosis for {diagnosis_id}: {e}")
#             # إعادة إثارة الاستثناء كخطأ عام ليتم التقاطه بواسطة مهمة Celery
#             raise


# class DiagnosisOrchestrationService:
#     #المنسق (المايسترو) الذي يدير خط أنابيب التشخيص الكامل.
    
#     def __init__(self):
#         # في نظام حقيقي، سيتم حقن المسارات من الإعدادات
#         self.vision_service = VisionModelService(model_path="path/to/vision_model.h5")
#         self.tabular_service = TabularModelService()

#     def run_full_diagnosis(self, image_data, demographics: dict) -> dict:
        
#         #ينسق عملية التشخيص الكاملة.
        
#         print("INFO: Starting full diagnosis pipeline...")
#         # 1. الحصول على تنبؤات من نموذج الرؤية
#         vision_output = self.vision_service.predict(image_data)
        
#         # 2. الحصول على التشخيص النهائي من النموذج الجدولي
#         final_result = self.tabular_service.predict(vision_output, demographics)
        
#         print("INFO: Diagnosis pipeline completed.")
#         return final_result
# """


# class DjangoDiagnosisOrchestrator:
    
#     #غلاف (Wrapper) حول خدمة الذكاء الاصطناعي لدمجها مع Django.
#     #يتعامل مع جلب البيانات من نماذج Django وتمريرها إلى الـ pipeline.
    
#     def __init__(self):
#         # تهيئة خدمة الذكاء الاصطناعي الأساسية
#         # سيتم تحميل النماذج مرة واحدة فقط بفضل نمط Singleton
#         self.ai_service = AIPipelineService()
#         self.repo = DiagnosisRepository()

#     def _preprocess_image_for_pipeline(self, image_field) -> np.ndarray:
#         #يقرأ ImageField من Django ويحوله إلى مصفوفة NumPy.
#         image = Image.open(image_field)
#         # قد تحتاج إلى تحويل الصورة إلى RGB وتغيير حجمها هنا إذا لم يكن ذلك جزءًا من الـ pipeline
#         # مثال: image = image.convert('RGB').resize((224, 224))
#         return np.array(image)

#     def run_diagnosis_from_django_model(self, diagnosis_id: str):
#         #ينفذ التشخيص الكامل باستخدام سجل Diagnosis من قاعدة البيانات.
#         try:
#             diagnosis_record = self.repo.get_by_id(diagnosis_id)
#             if not diagnosis_record:
#                 raise ValueError(f"Diagnosis record with ID {diagnosis_id} not found.")

#             # 1. تحضير المدخلات للـ pipeline
#             left_eye_img = self._preprocess_image_for_pipeline(diagnosis_record.left_fundus_image)
#             right_eye_img = self._preprocess_image_for_pipeline(diagnosis_record.right_fundus_image)
            
#             patient = diagnosis_record.patient
#             demographics = {
#                 "age": patient.age,
#                 "gender": 1 if patient.gender == 'FEMALE' else 0 # تحويل الجنس إلى رقمي
#             }

#             # 2. تشغيل pipeline الذكاء الاصطناعي
#             result_dict = self.ai_service.run_diagnosis(
#                 left_eye_img=left_eye_img,
#                 right_eye_img=right_eye_img,
#                 demographics=demographics
#             )

#             # 3. تحديث سجل التشخيص بالنتائج
#             self.repo.update_with_success(diagnosis_id, result_dict)
#             print(f"SUCCESS: Updated diagnosis record {diagnosis_id} with AI results.")

#         except (ModelInferenceError, ModelLoadingError) as e:
#             # التعامل مع أخطاء الذكاء الاصطناعي
#             print(f"AI_ERROR: {e}")
#             self.repo.update_with_failure(diagnosis_id, str(e))
#         except Exception as e:
#             # التعامل مع أخطاء Django أو أخطاء أخرى
#             print(f"SYSTEM_ERROR: {e}")
#             self.repo.update_with_failure(diagnosis_id, f"A system error occurred: {e}")

        
