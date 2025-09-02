# FILE: ocular_diagnosis_system/services/diagnosis_service.py
# FILE: apps/diagnosis/ai_pipeline/service.py

import numpy as np
import tensorflow as tf
# تم إزالة ThreadPoolExecutor
import logging

from apps.diagnosis.ai_pipeline import config
from apps.diagnosis.ai_pipeline.production_feature_pipeline import ProductionFeaturePipeline
from apps.diagnosis.exceptions import ModelInferenceError, ModelLoadingError
from apps.diagnosis.ai_pipeline.feature_extractor import create_fused_feature_vector
from apps.diagnosis.ai_pipeline.models.classifier import Diagnoser, EyesModel
from apps.diagnosis.ai_pipeline.models.preprocessing import (
    CataractPreprocessing, DiabetesPreprocessing, GlaucomaPreprocessing,
    HypertensionPreprocessing, PathologicalMyopiaPreprocessing, AgeIssuesPreprocessing, MULTICLASSPreprocessing
)

logger = logging.getLogger(__name__)

class DiagnosisService:
    """
    ينسق خط أنابيب التشخيص الكامل.
    تم تعديل هذه النسخة لتشغيل جميع نماذج TensorFlow بشكل تسلسلي
    لضمان الاستقرار وتجنب مشاكل التزامن.
    """
    def __init__(self):
        try:
            logger.info("Initializing Diagnosis Service and loading models...")
            # 1. تحميل النموذج متعدد الفئات
            self.multi_class_model = EyesModel(
                model_path=config.MULTI_CLASS_MODEL_PATH,
                strategy=MULTICLASSPreprocessing()
            )
            
            # 2. إعداد مجمع النماذج المتخصصة
            self._setup_expert_diagnoser()
            
            # 3. تحميل النموذج الجدولي النهائي
            self.tabular_model = tf.keras.models.load_model(config.TABULAR_MODEL_PATH)
            
            # 4. إنشاء نسخة من خط أنابيب الميزات للإنتاج
            self.feature_pipeline = ProductionFeaturePipeline()

            logger.info("All models loaded and service is ready.")
        except Exception as e:
            logger.critical(f"Failed to initialize models or pipeline: {e}", exc_info=True)
            raise ModelLoadingError(f"Failed to initialize models or pipeline: {e}")
        
    def _setup_expert_diagnoser(self):
        """Initializes the Diagnoser singleton with all expert models."""
        self.diagnoser = Diagnoser()
        strategies = [
            CataractPreprocessing(), DiabetesPreprocessing(), GlaucomaPreprocessing(),
            HypertensionPreprocessing(), PathologicalMyopiaPreprocessing(), AgeIssuesPreprocessing()
        ]
        
        for i, expert_config in enumerate(config.EXPERT_MODELS_CONFIG):
            model = EyesModel(
                model_path=expert_config["path"],
                strategy=strategies[i]
            )
            self.diagnoser.add_model(model)

    def run_diagnosis(self, left_eye_img: np.ndarray, right_eye_img: np.ndarray, demographics: dict):
        """
        ينفذ خط أنابيب التشخيص الكامل من طرف إلى طرف بشكل تسلسلي.
        """
        try:
            logger.info("Starting full diagnosis pipeline (sequential execution)...")
            
            # --- الخطوة 1: استخلاص التنبؤات من النماذج الصورية (بشكل تسلسلي) ---
            logger.info("Running multi-class model for left eye...")
            multi_class_probs_left = self.multi_class_model.predict_single(left_eye_img)[0]
            
            logger.info("Running multi-class model for right eye...")
            multi_class_probs_right = self.multi_class_model.predict_single(right_eye_img)[0]
            
            logger.info("Running expert models...")
            expert_results = self.diagnoser.predict(left_eye_img, right_eye_img)

            expert_probs_left = np.array([res[0][0] for res in expert_results])
            expert_probs_right = np.array([res[1][0] for res in expert_results])
            
            # --- الخطوة 2: إنشاء متجه الميزات الأولي (18 ميزة) ---
            logger.info("Creating initial feature vector...")
            initial_feature_vector = create_fused_feature_vector(
                multi_class_probs_left, multi_class_probs_right,
                expert_probs_left, expert_probs_right,
                demographics['age'], demographics['gender']
            )

            # --- الخطوة 3: تحويل الميزات الأولية إلى الشكل النهائي (38 ميزة) ---
            logger.info("Transforming features with production pipeline...")
            final_feature_vector = self.feature_pipeline.transform(initial_feature_vector)

            # --- الخطوة 4: الحصول على التنبؤ النهائي من النموذج الجدولي ---
            logger.info("Getting final prediction from tabular model...")
            final_probabilities = self.tabular_model.predict(final_feature_vector)[0]
            
            # --- الخطوة 5: تنسيق المخرجات النهائية ---
            logger.info("Formatting final diagnosis report...")
            diagnosis_report = {
                "final_diagnosis": {},
                "evidence_vector": initial_feature_vector.tolist()
            }
            for i, prob in enumerate(final_probabilities):
                disease_name = config.MULTI_CLASS_OUTPUT_MAPPING.get(i, f"Unknown_Class_{i}")
                diagnosis_report["final_diagnosis"][disease_name] = f"{prob:.4f}"
            
            logger.info("Diagnosis pipeline completed successfully.")
            return diagnosis_report

        except Exception as e:
            logger.error(f"Full diagnosis pipeline failed: {e}", exc_info=True)
            raise ModelInferenceError(f"Full diagnosis pipeline failed: {e}")
        
# FILE: apps/diagnosis/ai_pipeline/service.py

# import numpy as np
# import tensorflow as tf
# from concurrent.futures import ThreadPoolExecutor
# import logging

# from apps.diagnosis.ai_pipeline import config
# from apps.diagnosis.ai_pipeline.production_feature_pipeline import ProductionFeaturePipeline
# from apps.diagnosis.exceptions import ModelInferenceError, ModelLoadingError
# from apps.diagnosis.ai_pipeline.feature_extractor import create_fused_feature_vector
# from apps.diagnosis.ai_pipeline.models.classifier import Diagnoser, EyesModel
# from apps.diagnosis.ai_pipeline.models.preprocessing import (
#     CataractPreprocessing, DiabetesPreprocessing, GlaucomaPreprocessing,
#     HypertensionPreprocessing, PathologicalMyopiaPreprocessing, AgeIssuesPreprocessing, MULTICLASSPreprocessing
# )

# # احصل على logger احترافي بدلاً من استخدام print
# logger = logging.getLogger(__name__)

# class DiagnosisService:
#     """
#     ينسق خط أنابيب التشخيص الكامل باستخدام جميع النماذج المتاحة.
#     هذه هي النسخة النهائية المدمجة مع أفضل الممارسات الهندسية.
#     """
#     def __init__(self):
#         try:
#             logger.info("Initializing Diagnosis Service and loading models...")
#             # 1. تحميل النموذج متعدد الفئات
#             self.multi_class_model = EyesModel(
#                 model_path=config.MULTI_CLASS_MODEL_PATH,
#                 strategy=MULTICLASSPreprocessing()
#             )
            
#             # 2. إعداد مجمع النماذج المتخصصة
#             self._setup_expert_diagnoser()
            
#             # 3. تحميل النموذج الجدولي النهائي
#             self.tabular_model = tf.keras.models.load_model(config.TABULAR_MODEL_PATH)
            
#             # 4. إنشاء نسخة من خط أنابيب الميزات للإنتاج
#             self.feature_pipeline = ProductionFeaturePipeline()

#             logger.info("All models loaded and service is ready.")
#         except Exception as e:
#             # سجل الخطأ الكامل قبل إثارة استثناء مخصص
#             logger.critical(f"Failed to initialize models or pipeline: {e}", exc_info=True)
#             raise ModelLoadingError(f"Failed to initialize models or pipeline: {e}")
        
#     def _setup_expert_diagnoser(self):
#         """Initializes the Diagnoser singleton with all expert models."""
#         self.diagnoser = Diagnoser()
#         strategies = [
#             CataractPreprocessing(), DiabetesPreprocessing(), GlaucomaPreprocessing(),
#             HypertensionPreprocessing(), PathologicalMyopiaPreprocessing(), AgeIssuesPreprocessing()
#         ]
        
#         for i, expert_config in enumerate(config.EXPERT_MODELS_CONFIG):
#             model = EyesModel(
#                 model_path=expert_config["path"],
#                 strategy=strategies[i]
#             )
#             self.diagnoser.add_model(model)

#     def run_diagnosis(self, left_eye_img: np.ndarray, right_eye_img: np.ndarray, demographics: dict):
#         """
#         ينفذ خط أنابيب التشخيص الكامل من طرف إلى طرف.
#         """
#         try:
#             logger.info("Starting full diagnosis pipeline...")
            
#             # --- الخطوة 1: استخلاص التنبؤات من النماذج الصورية بالتوازي ---
#             with ThreadPoolExecutor() as executor:
#                 mc_left_future = executor.submit(self.multi_class_model.predict_single, left_eye_img)
#                 mc_right_future = executor.submit(self.multi_class_model.predict_single, right_eye_img)
#                 expert_future = executor.submit(self.diagnoser.predict, left_eye_img, right_eye_img)

#                 multi_class_probs_left = mc_left_future.result()[0]
#                 multi_class_probs_right = mc_right_future.result()[0]
#                 expert_results = expert_future.result()

#             expert_probs_left = np.array([res[0][0] for res in expert_results])
#             expert_probs_right = np.array([res[1][0] for res in expert_results])
            
#             # --- الخطوة 2: إنشاء متجه الميزات الأولي (18 ميزة) ---
#             initial_feature_vector = create_fused_feature_vector(
#                 multi_class_probs_left, multi_class_probs_right,
#                 expert_probs_left, expert_probs_right,
#                 demographics['age'], demographics['gender']
#             )

#             # --- الخطوة 3: تحويل الميزات الأولية إلى الشكل النهائي (38 ميزة) ---
#             final_feature_vector = self.feature_pipeline.transform(initial_feature_vector)

#             # --- الخطوة 4: الحصول على التنبؤ النهائي من النموذج الجدولي ---
#             final_probabilities = self.tabular_model.predict(final_feature_vector)[0]
            
#             # --- الخطوة 5: تنسيق المخرجات النهائية ---
#             # هذا الجزء هو الذي يبني القاموس التفصيلي الذي تريده
#             diagnosis_report = {
#                 "final_diagnosis": {},
#                 # تحويل متجه numpy إلى قائمة بايثون ليكون متوافقًا مع JSON
#                 "evidence_vector": initial_feature_vector.tolist() 
#             }
#             for i, prob in enumerate(final_probabilities):
#                 disease_name = config.MULTI_CLASS_OUTPUT_MAPPING.get(i, f"Unknown_Class_{i}")
#                 # تنسيق الاحتمال كسلسلة نصية بأربع خانات عشرية
#                 diagnosis_report["final_diagnosis"][disease_name] = f"{prob:.4f}"
            
#             logger.info("Diagnosis pipeline completed successfully.")
#             return diagnosis_report

#         except Exception as e:
#             # سجل الخطأ الكامل مع التتبع للمساعدة في التصحيح
#             logger.error(f"Full diagnosis pipeline failed: {e}", exc_info=True)
#             raise ModelInferenceError(f"Full diagnosis pipeline failed: {e}")
        

# apps/diagnosis/ai_pipeline/service.py
# import os
# import numpy as np
# import logging
# from typing import Dict

# # from tensorflow.keras.models import load_model # <-- سيتم تفعيل هذا لاحقًا

# logger = logging.getLogger(__name__)

# # قاموس لتخزين النماذج المحملة لكل عملية عامل (worker process)
# # المفتاح هو معرّف العملية (PID)، والقيمة هي كائن النموذج
# _MODEL_CACHE: Dict[int, object] = {}

# def get_vision_model(model_path: str) -> object:
#     """
#     تحميل نموذج الرؤية بذكاء.
#     يتم تحميل النموذج مرة واحدة فقط لكل عملية عامل (worker process) بفضل التخزين المؤقت المستند إلى PID.
#     هذا يمنع تسرب الذاكرة ويقلل من وقت بدء تشغيل المهام.
#     """
#     pid = os.getpid()
#     if pid not in _MODEL_CACHE:
#         logger.info(f"Loading vision model from {model_path} for worker process PID: {pid}...")
#         # _MODEL_CACHE[pid] = load_model(model_path) # <-- سيتم تفعيل هذا لاحقًا
#         _MODEL_CACHE[pid] = "mock_vision_model" # محاكاة حالية
#         logger.info(f"Model loaded successfully for PID: {pid}.")
#     return _MODEL_CACHE[pid]

# class VisionModelService:
#     """خدمة مسؤولة عن نموذج الرؤية (الصور)."""
#     def __init__(self, model_path: str):
#         self._model = get_vision_model(model_path)

#     def predict(self, image_data: np.ndarray) -> dict:
#         """يشغل التنبؤ على صورة واحدة."""
#         # predictions = self._model.predict(image_data)
#         logger.info("Vision model predicting...")
#         # محاكاة للإخراج
#         return {"disease_probability": 0.85, "features": [0.1, 0.2, 0.7]}

# class TabularModelService:
#     """خدمة مسؤولة عن النموذج الجدولي."""
#     def predict(self, vision_output: dict, demographic_data: dict) -> dict:
#         """يُرجع التشخيص النهائي."""
#         logger.info("Tabular model predicting...")
#         # محاكاة للإخراج
#         confidence = vision_output.get("disease_probability", 0) * 0.9
#         return {"final_diagnosis": "High-Risk Glaucoma", "confidence": confidence}


# class DiagnosisService:
#     """
#     المنسق (المايسترو) الذي يدير خط أنابيب التشخيص الكامل.
#     """
#     def __init__(self):
#         # في نظام حقيقي، سيتم حقن المسارات من الإعدادات
#         self.vision_service = VisionModelService(model_path="path/to/vision_model.h5")
#         self.tabular_service = TabularModelService()

#     def run_diagnosis(self, left_eye_img: np.ndarray, right_eye_img: np.ndarray, demographics: dict) -> dict:
#         """
#         ينسق عملية التشخيص الكاملة ويضمن أن المخرجات متوافقة مع JSON.
#         """
#         logger.info("Starting full diagnosis AI pipeline...")
#         # TODO: هنا سيتم دمج مخرجات العينين (مثلاً، أخذ المتوسط أو الأعلى)
#         vision_output = self.vision_service.predict(left_eye_img)
        
#         final_result = self.tabular_service.predict(vision_output, demographics)
        
#         # --- ضمان التوافق مع JSON ---
#         # تأكد من تحويل أي أنواع بيانات خاصة بالمكتبات (مثل numpy.float64) إلى أنواع بايثون الأصلية
#         final_result['confidence'] = float(final_result['confidence'])
        
#         logger.info("Diagnosis AI pipeline completed.")
#         return final_result
    
    
# import logging
# import numpy as np
# import tensorflow as tf
# from concurrent.futures import ThreadPoolExecutor

# from apps.diagnosis.ai_pipeline import config
# from apps.diagnosis.ai_pipeline.production_feature_pipeline import ProductionFeaturePipeline
# from apps.diagnosis.exceptions import ModelInferenceError, ModelLoadingError
# from apps.diagnosis.ai_pipeline.feature_extractor import create_fused_feature_vector
# from apps.diagnosis.ai_pipeline.models.classifier import Diagnoser, EyesModel
# from apps.diagnosis.ai_pipeline.models.preprocessing import (
#     CataractPreprocessing, DiabetesPreprocessing, GlaucomaPreprocessing,
#     HypertensionPreprocessing, PathologicalMyopiaPreprocessing, AgeIssuesPreprocessing, MULTICLASSPreprocessing
# )

# class DiagnosisService:
#     """
#     ينسق خط أنابيب التشخيص الكامل باستخدام جميع النماذج المتاحة.
#     الإصدار النهائي (Hotfix v2.0).
#     """
#     def __init__(self):
#         try:
#             print("INFO: Initializing Diagnosis Service and loading models...")
#             # 1. تحميل النموذج متعدد الفئات
#             self.multi_class_model = EyesModel(
#                 model_path=config.MULTI_CLASS_MODEL_PATH,
#                 strategy=MULTICLASSPreprocessing()
#             )
            
#             # 2. إعداد مجمع النماذج المتخصصة
#             self._setup_expert_diagnoser()
            
#             # 3. تحميل النموذج الجدولي النهائي
#             self.tabular_model = tf.keras.models.load_model(config.TABULAR_MODEL_PATH)
            
#             # 4. إنشاء نسخة من خط أنابيب الميزات للإنتاج
#             self.feature_pipeline = ProductionFeaturePipeline()

#             print("INFO: All models loaded and service is ready.")
#         except Exception as e:
#             raise ModelLoadingError(f"Failed to initialize models or pipeline: {e}")
        
#     def _setup_expert_diagnoser(self):
#         """Initializes the Diagnoser singleton with all expert models."""
#         self.diagnoser = Diagnoser()
#         strategies = [
#             CataractPreprocessing(), DiabetesPreprocessing(), GlaucomaPreprocessing(),
#             HypertensionPreprocessing(), PathologicalMyopiaPreprocessing(), AgeIssuesPreprocessing()
#         ]
        
#         for i, expert_config in enumerate(config.EXPERT_MODELS_CONFIG):
#             model = EyesModel(
#                 model_path=expert_config["path"],
#                 strategy=strategies[i]
#             )
#             self.diagnoser.add_model(model)

#     def run_diagnosis(self, left_eye_img: np.ndarray, right_eye_img: np.ndarray, demographics: dict):
#         """
#         ينفذ خط أنابيب التشخيص الكامل من طرف إلى طرف.
#         """
#         try:
#             print("INFO: Starting full diagnosis pipeline...")
            
#             # --- الخطوة 1: استخلاص التنبؤات من النماذج الصورية بالتوازي ---
#             with ThreadPoolExecutor() as executor:
#                 mc_left_future = executor.submit(self.multi_class_model.predict_single, left_eye_img)
#                 mc_right_future = executor.submit(self.multi_class_model.predict_single, right_eye_img)
#                 expert_future = executor.submit(self.diagnoser.predict, left_eye_img, right_eye_img)

#                 multi_class_probs_left = mc_left_future.result()[0]
#                 multi_class_probs_right = mc_right_future.result()[0]
#                 expert_results = expert_future.result()

#             expert_probs_left = np.array([res[0][0] for res in expert_results])
#             expert_probs_right = np.array([res[1][0] for res in expert_results])
            
#             # --- الخطوة 2: إنشاء متجه الميزات الأولي (18 ميزة) ---
#             initial_feature_vector = create_fused_feature_vector(
#                 multi_class_probs_left, multi_class_probs_right,
#                 expert_probs_left, expert_probs_right,
#                 demographics['age'], demographics['gender']
#             )

#             # --- الخطوة 3: تحويل الميزات الأولية إلى الشكل النهائي (38 ميزة) ---
#             final_feature_vector = self.feature_pipeline.transform(initial_feature_vector)

#             # --- الخطوة 4: الحصول على التنبؤ النهائي من النموذج الجدولي ---
#             final_probabilities = self.tabular_model.predict(final_feature_vector)[0]
            
#             # --- الخطوة 5: تنسيق المخرجات النهائية ---
#             diagnosis_report = {
#                 "final_diagnosis": {},
#                 "evidence_vector": initial_feature_vector.tolist() # نعرض المتجه الأولي للمستخدم
#             }
#             for i, prob in enumerate(final_probabilities):
#                 disease_name = config.MULTI_CLASS_OUTPUT_MAPPING.get(i, f"Unknown_Class_{i}")
#                 diagnosis_report["final_diagnosis"][disease_name] = f"{prob:.4f}"
            
#             print("INFO: Diagnosis pipeline completed successfully.")
#             return diagnosis_report

#         except Exception as e:
#             # إضافة تفاصيل إضافية للخطأ للمساعدة في التصحيح
#             logging.error(f"Full diagnosis pipeline failed: {e}", exc_info=True)
#             raise ModelInferenceError(f"Full diagnosis pipeline failed: {e}")
        
        
# # ocular_diagnosis_system/services/diagnosis_service.py
# import numpy as np
# from concurrent.futures import ThreadPoolExecutor

# import tensorflow as tf

# from apps.diagnosis.ai_pipeline import config
# from apps.diagnosis.ai_pipeline.production_feature_pipeline import ProductionFeaturePipeline
# from apps.diagnosis.exceptions import ModelInferenceError, ModelLoadingError
# from apps.diagnosis.ai_pipeline.feature_extractor import _calculate_f1_score, create_fused_feature_vector
# from apps.diagnosis.ai_pipeline.models.classifier import Diagnoser, EyesModel
# from apps.diagnosis.ai_pipeline.models.preprocessing import (
#     CataractPreprocessing, DiabetesPreprocessing, GlaucomaPreprocessing,
#     HypertensionPreprocessing, PathologicalMyopiaPreprocessing, AgeIssuesPreprocessing, MULTICLASSPreprocessing, TABULARPreprocessing
# )

# class DiagnosisService:
#     """Orchestrates the full diagnosis pipeline using all available models."""

#     def __init__(self):
#         try:
#             print("INFO: Initializing Diagnosis Service and loading models...")
#             # Load the multi-class model
#             self.multi_class_model = EyesModel(
#                 model_path=config.MULTI_CLASS_MODEL_PATH,
#                 strategy= MULTICLASSPreprocessing()
#             )
#             self._setup_expert_diagnoser() # Call this method to initialize the expert diagnoser
            
#             # Load the tabular model
#             # --- تفعيل النموذج الجدولي الحقيقي ---
#             self.tabular_model = tf.keras.models.load_model(config.TABULAR_MODEL_PATH)
#             # تحديد استراتيجية الدمج المستخدمة في الإنتاج
#             self.fusion_strategy = create_fused_feature_vector

#             self.feature_pipeline = ProductionFeaturePipeline()

#             self.preporcesseing = TABULARPreprocessing

#             print("INFO: All models loaded and service is ready.")
#         except Exception as e:
#             raise ModelLoadingError(f"Failed to initialize models: {e}")
        

#             print("INFO: All models loaded and service is ready.")
#         except Exception as e:
#             raise ModelLoadingError(f"Failed to initialize models: {e}")
        
        
#     def _setup_expert_diagnoser(self):
#         """Initializes the Diagnoser singleton with all expert models."""
#         self.diagnoser = Diagnoser()
#         strategies = [
#             CataractPreprocessing(), DiabetesPreprocessing(), GlaucomaPreprocessing(),
#             HypertensionPreprocessing(), PathologicalMyopiaPreprocessing(), AgeIssuesPreprocessing()
#         ]
        
#         for i, expert_config in enumerate(config.EXPERT_MODELS_CONFIG):
#             print("Majd I am Here :) ... ", expert_config["path"])
#             model = EyesModel(
#                 model_path=expert_config["path"],
#                 strategy=strategies[i]
#             )
#             # Override the loaded model with a mock for demonstration
#             #model.model = mock_tf_model((224, 224, 1)) # Use appropriate shape
#             self.diagnoser.add_model(model)

#     def run_diagnosis(self, left_eye_img: np.ndarray, right_eye_img: np.ndarray, demographics: dict):
#         """
#         Runs the full end-to-end diagnosis pipeline.
#         """
#         try:
#             print("INFO: Starting full diagnosis pipeline...")
            
#             # Step 1: Run multi-class and expert models in parallel
#             with ThreadPoolExecutor() as executor:
#                 # Submit multi-class predictions using the new correct method
#                 multi_class_left_future = executor.submit(self.multi_class_model.predict_single, left_eye_img)
#                 multi_class_right_future = executor.submit(self.multi_class_model.predict_single, right_eye_img)
                
#                 # Submit expert predictions
#                 expert_future = executor.submit(self.diagnoser.predict, left_eye_img, right_eye_img)

#                 # Retrieve results
#                 multi_class_probs_left = multi_class_left_future.result()[0]
#                 multi_class_probs_right = multi_class_right_future.result()[0]
#                 expert_results = expert_future.result()

#             # The diagnoser returns a list of tuples [(left_res, right_res), ...], needs unpacking
#             expert_probs_left = np.array([res[0][0] for res in expert_results])
#             expert_probs_right = np.array([res[1][0] for res in expert_results])
            
#             # Step 2: Create the fused feature vector
#             # Fused Vector 18 Features
#             feature_vector = self.fusion_strategy (
#                 multi_class_probs_left, multi_class_probs_right,
#                 expert_probs_left, expert_probs_right,
#                 demographics['age'], demographics['gender'],
#             )

#             #Final Vector 38 Features
#             processed_vector = self.feature_pipeline.transform(feature_vector)


#             # Step 3: Get final prediction from the tabular model
#             final_probabilities = self.tabular_model.predict(np.expand_dims(processed_vector, axis=0))[0]

#             #final_probabilities = self.tabular_model.predict_proba(np.expand_dims(feature_vector, axis=0))[0]
            
            
#             # Step 4: Format the final output
#             diagnosis_report = {
#                 "final_diagnosis": {},
#                 "evidence_vector": feature_vector.tolist() # For research and interpretability
#             }
#             for i, prob in enumerate(final_probabilities):
#                 disease_name = config.MULTI_CLASS_OUTPUT_MAPPING.get(i, f"Unknown_Class_{i}")
#                 diagnosis_report["final_diagnosis"][disease_name] = f"{prob:.4f}"
            
#             print("INFO: Diagnosis pipeline completed successfully.")
#             return diagnosis_report

#         except Exception as e:
#             raise ModelInferenceError(f"Full diagnosis pipeline failed: {e}")