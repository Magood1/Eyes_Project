# ocular_diagnosis_system/services/diagnosis_service.py
import numpy as np
from concurrent.futures import ThreadPoolExecutor

import tensorflow as tf

from apps.diagnosis.ai_pipeline import config
from apps.diagnosis.exceptions import ModelInferenceError, ModelLoadingError
from apps.diagnosis.ai_pipeline.feature_extractor import _calculate_f1_score, create_fused_feature_vector
from apps.diagnosis.ai_pipeline.models.classifier import Diagnoser, EyesModel
from apps.diagnosis.ai_pipeline.models.preprocessing import (
    CataractPreprocessing, DiabetesPreprocessing, GlaucomaPreprocessing,
    HypertensionPreprocessing, PathologicalMyopiaPreprocessing, AgeIssuesPreprocessing, MULTICLASSPreprocessing, TABULARPreprocessing
)


# --- Mock Models for runnable demonstration ---
# # In a real system, these would be loaded model objects.
# def mock_tf_model(input_shape):
#     class MockModel:
#         def predict(self, data):
#             batch_size = data.shape[0]
#             if len(input_shape) == 2: # Expert model (binary)
#                 return np.random.rand(batch_size, 1).astype(np.float32)
#             # Multi-class model (8 classes)
#             probs = np.random.rand(batch_size, 8)
#             return (probs / probs.sum(axis=1, keepdims=True)).astype(np.float32)
#     return MockModel()

# def mock_tabular_model():
#     class MockTabular:
#         def predict_proba(self, data):
#             batch_size = data.shape[0]
#             probs = np.random.rand(batch_size, 8)
#             return probs / probs.sum(axis=1, keepdims=True)
#     return MockTabular()
# # --- End Mock Models ---


class DiagnosisService:
    """Orchestrates the full diagnosis pipeline using all available models."""

    def __init__(self):
        try:
            print("INFO: Initializing Diagnosis Service and loading models...")
            # Load the multi-class model
            self.multi_class_model = EyesModel(
                model_path=config.MULTI_CLASS_MODEL_PATH,
                strategy= MULTICLASSPreprocessing()
            )
            self._setup_expert_diagnoser() # Call this method to initialize the expert diagnoser
            
            # Load the tabular model
            # --- تفعيل النموذج الجدولي الحقيقي ---
            self.tabular_model = tf.keras.models.load_model(config.TABULAR_MODEL_PATH)
            self.tabular_preprocessor = TABULARPreprocessing()
            # تحديد استراتيجية الدمج المستخدمة في الإنتاج
            self.fusion_strategy = create_fused_feature_vector

            print("INFO: All models loaded and service is ready.")
        except Exception as e:
            raise ModelLoadingError(f"Failed to initialize models: {e}")
        

            print("INFO: All models loaded and service is ready.")
        except Exception as e:
            raise ModelLoadingError(f"Failed to initialize models: {e}")
        
        
    def _setup_expert_diagnoser(self):
        """Initializes the Diagnoser singleton with all expert models."""
        self.diagnoser = Diagnoser()
        strategies = [
            CataractPreprocessing(), DiabetesPreprocessing(), GlaucomaPreprocessing(),
            HypertensionPreprocessing(), PathologicalMyopiaPreprocessing(), AgeIssuesPreprocessing()
        ]
        
        for i, expert_config in enumerate(config.EXPERT_MODELS_CONFIG):
            print("Majd I am Here :) ... ", expert_config["path"])
            model = EyesModel(
                model_path=expert_config["path"],
                strategy=strategies[i]
            )
            # Override the loaded model with a mock for demonstration
            #model.model = mock_tf_model((224, 224, 1)) # Use appropriate shape
            self.diagnoser.add_model(model)

    def run_diagnosis(self, left_eye_img: np.ndarray, right_eye_img: np.ndarray, demographics: dict):
        """
        Runs the full end-to-end diagnosis pipeline.
        """
        try:
            print("INFO: Starting full diagnosis pipeline...")
            
            # Step 1: Run multi-class and expert models in parallel
            with ThreadPoolExecutor() as executor:
                # Submit multi-class predictions using the new correct method
                multi_class_left_future = executor.submit(self.multi_class_model.predict_single, left_eye_img)
                multi_class_right_future = executor.submit(self.multi_class_model.predict_single, right_eye_img)
                
                # Submit expert predictions
                expert_future = executor.submit(self.diagnoser.predict, left_eye_img, right_eye_img)

                # Retrieve results
                multi_class_probs_left = multi_class_left_future.result()[0]
                multi_class_probs_right = multi_class_right_future.result()[0]
                expert_results = expert_future.result()

            # The diagnoser returns a list of tuples [(left_res, right_res), ...], needs unpacking
            expert_probs_left = np.array([res[0][0] for res in expert_results])
            expert_probs_right = np.array([res[1][0] for res in expert_results])
            
            # Step 2: Create the fused feature vector
            feature_vector = self.fusion_strategy (
                multi_class_probs_left, multi_class_probs_right,
                expert_probs_left, expert_probs_right,
                demographics['age'], demographics['gender'],
            )

            processed_vector = self.tabular_preprocessor.apply(feature_vector)
            
            # Step 3: Get final prediction from the tabular model
            #final_probabilities = self.tabular_model.predict_proba(np.expand_dims(feature_vector, axis=0))[0]
            final_probabilities = self.tabular_model.predict(np.expand_dims(processed_vector, axis=0))[0]
            
            # Step 4: Format the final output
            diagnosis_report = {
                "final_diagnosis": {},
                "evidence_vector": feature_vector.tolist() # For research and interpretability
            }
            for i, prob in enumerate(final_probabilities):
                disease_name = config.MULTI_CLASS_OUTPUT_MAPPING.get(i, f"Unknown_Class_{i}")
                diagnosis_report["final_diagnosis"][disease_name] = f"{prob:.4f}"
            
            print("INFO: Diagnosis pipeline completed successfully.")
            return diagnosis_report

        except Exception as e:
            raise ModelInferenceError(f"Full diagnosis pipeline failed: {e}")