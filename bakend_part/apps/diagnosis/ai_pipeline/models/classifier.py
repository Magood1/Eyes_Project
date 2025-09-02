# ocular_diagnosis_system/models/classifier.py
# FILE: apps/diagnosis/ai_pipeline/models/classifier.py

import tensorflow as tf
import numpy as np
import threading
import logging
from typing import List, Tuple, Dict, Callable

# Local imports from other parts of the project
from apps.diagnosis.ai_pipeline.models.singleton import Singleton
from apps.diagnosis.ai_pipeline.models.preprocessing import PreprocessingStrategy

logger = logging.getLogger(__name__)

class ModelLoaderFactory:
    """A factory for loading ML models based on their file extension."""
    
    _loaders: Dict[str, Callable[[str], object]] = {
        "h5": lambda path: tf.keras.models.load_model(path),
        "keras": lambda path: tf.keras.models.load_model(path),
        "pb": lambda path: tf.saved_model.load(path),
    }

    @staticmethod
    def get_loader(extension: str) -> Callable[[str], object]:
        loader = ModelLoaderFactory._loaders.get(extension.lower())
        if loader is None:
            raise ValueError(f"Unsupported model format: {extension}")
        return loader


class EyesModel:
    """
    Represents a single, specialized expert model for diagnosing a specific disease.
    It encapsulates the model loading, caching, and prediction logic.
    """
    _model_cache: Dict[str, object] = {}
    _cache_lock = threading.Lock()

    def __init__(self, model_path: str, strategy: PreprocessingStrategy):
        self.model_path = model_path
        self.strategy = strategy
        self.model = self._load_model()

    def _load_model(self) -> object:
        """Loads a model from the given path, utilizing a thread-safe cache."""
        with EyesModel._cache_lock:
            if self.model_path not in EyesModel._model_cache:
                logger.info(f"Cache miss. Loading expert model from {self.model_path}...")
                extension = str(self.model_path).split('.')[-1]
                loader = ModelLoaderFactory.get_loader(extension)
                EyesModel._model_cache[self.model_path] = loader(self.model_path)
            else:
                logger.info(f"Cache hit. Reusing expert model from {self.model_path}.")
            return EyesModel._model_cache[self.model_path]
        
    def _prepare_input_tensor(self, image: np.ndarray) -> tf.Tensor:
        """Applies preprocessing, normalization, and shaping for a single image."""
        # 1. Apply preprocessing
        processed_image = self.strategy.apply(image)

        # 2. Ensure correct input shape and data type
        input_tensor = np.expand_dims(processed_image, axis=0).astype(np.float32)

        # 3. Normalize if needed (safety check)
        if np.max(input_tensor) > 1.0:
            input_tensor /= 255.0
        
        return tf.convert_to_tensor(input_tensor)

    def predict_single(self, image: np.ndarray) -> np.ndarray:
        """
        Prepares and runs prediction for a single image.
        """
        input_tensor = self._prepare_input_tensor(image)
        # The result of .predict() is a numpy array
        result = self.model.predict(input_tensor)
        return result
    
    def diagnose(self, left_image: np.ndarray, right_image: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepares and runs prediction for both eyes.
        """
        left_tensor = self._prepare_input_tensor(left_image)
        right_tensor = self._prepare_input_tensor(right_image)

        # Run prediction
        left_result = self.model.predict(left_tensor)[0]
        right_result = self.model.predict(right_tensor)[0]
        
        return left_result, right_result


class Diagnoser(metaclass=Singleton):
    """
    A Singleton service that manages and runs all specialized EyesModel instances.
    """
    def __init__(self):
        self.models: List[EyesModel] = []

    def add_model(self, model: EyesModel):
        """Adds a configured expert model to the diagnoser."""
        self.models.append(model)

    def predict(self, left_image: np.ndarray, right_image: np.ndarray) -> List[Tuple[np.ndarray, np.ndarray]]:
        """
        Runs the 'diagnose' method for all registered models sequentially to avoid
        TensorFlow threading issues with model.predict().
        """
        if not self.models:
            logger.warning("Diagnoser.predict called with no models registered.")
            return []
        
        logger.info(f"Running {len(self.models)} expert models sequentially...")
        results = []
        for model in self.models:
            # Call diagnose for each model one by one
            result_tuple = model.diagnose(left_image, right_image)
            results.append(result_tuple)
        
        logger.info("All expert models have completed prediction.")
        return results
    
# import tensorflow as tf
# import numpy as np
# import threading
# from typing import List, Tuple, Dict, Callable
# from concurrent.futures import ThreadPoolExecutor

# # Local imports from other parts of the project
# from apps.diagnosis.ai_pipeline.models.singleton import Singleton
# from apps.diagnosis.ai_pipeline.models.preprocessing import PreprocessingStrategy


# class ModelLoaderFactory:
#     """A factory for loading ML models based on their file extension."""
    
#     _loaders: Dict[str, Callable[[str], object]] = {
#         "h5": lambda path: tf.keras.models.load_model(path),
#         "keras": lambda path: tf.keras.models.load_model(path),
#         "pb": lambda path: tf.saved_model.load(path),
#     }

#     @staticmethod
#     def get_loader(extension: str) -> Callable[[str], object]:
#         loader = ModelLoaderFactory._loaders.get(extension.lower())
#         if loader is None:
#             raise ValueError(f"Unsupported model format: {extension}")
#         return loader


# class EyesModel:
#     """
#     Represents a single, specialized expert model for diagnosing a specific disease.
#     It encapsulates the model loading, caching, and prediction logic.
#     """
#     _model_cache: Dict[str, object] = {}
#     _cache_lock = threading.Lock()

#     def __init__(self, model_path: str, strategy: PreprocessingStrategy):
#         self.model_path = model_path
#         self.strategy = strategy
#         self.model = self._load_model()

#     def _load_model(self) -> object:
#         """Loads a model from the given path, utilizing a thread-safe cache."""
#         with EyesModel._cache_lock:
#             if self.model_path not in EyesModel._model_cache:
#                 print(f"INFO: Cache miss. Loading expert model from {self.model_path}...")
#                 extension = str(self.model_path).split('.')[-1]
#                 loader = ModelLoaderFactory.get_loader(extension)
#                 EyesModel._model_cache[self.model_path] = loader(self.model_path)
#             else:
#                 print(f"INFO: Cache hit. Reusing expert model from {self.model_path}.")
#             return EyesModel._model_cache[self.model_path]
        
#     def predict_single(self, image: np.ndarray) -> np.ndarray:
#         """
#         Applies preprocessing and runs prediction for a single image.
#         """
#         # 1. Apply preprocessing
#         processed_image = self.strategy.apply(image)

#         # 2. Ensure correct input shape and data type
#         input_tensor = np.expand_dims(processed_image, axis=0).astype(np.float32)

#         # 3. Normalize if needed
#         if np.max(input_tensor) > 1.0:
#             input_tensor /= 255.0

#         # 4. Run prediction
#         # لاحظ أننا لا نأخذ [0] هنا لأننا قد نحتاج للدفعة الكاملة
#         result = self.model.predict(input_tensor)
        
#         return result
    

#     def diagnose(self, left_image: np.ndarray, right_image: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
#         """
#         Applies preprocessing and runs prediction for both eyes.
#         This is the final, robust version of the method.
#         """
#         # 1. Apply the specific preprocessing strategy for this model
#         left_processed = self.strategy.apply(left_image)
#         right_processed = self.strategy.apply(right_image)

#         # 2. Ensure correct input shape and data type for the model
#         left_input = np.expand_dims(left_processed, axis=0).astype(np.float32)
#         right_input = np.expand_dims(right_processed, axis=0).astype(np.float32)

#         # 3. Normalize pixels to [0, 1] if they are not already.
#         #    This is a critical safety check for model compatibility.
#         if np.max(left_input) > 1.0:
#             left_input /= 255.0
#         if np.max(right_input) > 1.0:
#             right_input /= 255.0

#         # 4. Run prediction
#         left_result = self.model.predict(left_input)[0]
#         right_result = self.model.predict(right_input)[0]
        
#         return left_result, right_result


# class Diagnoser(metaclass=Singleton):
#     """
#     A Singleton service that manages and runs all specialized EyesModel instances in parallel.
#     """
#     def __init__(self):
#         self.models: List[EyesModel] = []

#     def add_model(self, model: EyesModel):
#         """Adds a configured expert model to the diagnoser."""
#         self.models.append(model)

#     def predict(self, left_image: np.ndarray, right_image: np.ndarray) -> List[Tuple[np.ndarray, np.ndarray]]:
#         """
#         Runs the 'diagnose' method for all registered models concurrently.
#         """
#         if not self.models:
#             return []
            
#         with ThreadPoolExecutor(max_workers=len(self.models)) as executor:
#             # Map each model to its diagnose function with the provided images
#             results = list(executor.map(
#                 lambda model: model.diagnose(left_image, right_image), 
#                 self.models
#             ))
#         return results