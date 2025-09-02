# FILE: src/preprocessing_strategies.py

import cv2
import numpy as np
import logging
from typing import Protocol, Dict, Type

class Singleton(type):
    """Metaclass to ensure only one instance of a strategy is created."""
    _instances: Dict[Type, object] = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class PreprocessingStrategy(Protocol):
    """Protocol defining the interface for all preprocessing strategies."""
    def apply(self, image: np.ndarray) -> np.ndarray: ...

# --- استراتيجيات المعالجة المسبقة ---

class CataractPreprocessing(metaclass=Singleton):
    def apply(self, image: np.ndarray) -> np.ndarray:
        image = cv2.resize(image, (224, 224))
        return cv2.convertScaleAbs(image, alpha=1.0, beta=50)

class DiabetesPreprocessing(metaclass=Singleton):
    def apply(self, image: np.ndarray) -> np.ndarray:
        image = cv2.resize(image, (224, 224))
        green_channel = image[:, :, 1]
        red_free_image = cv2.merge([green_channel, green_channel, green_channel])
        return cv2.convertScaleAbs(red_free_image, alpha=1.5, beta=50)

class GlaucomaPreprocessing(metaclass=Singleton):
    def apply(self, image: np.ndarray) -> np.ndarray:
        image = cv2.resize(image, (224, 224))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return (image / 255.0).astype(np.float32)

class HypertensionPreprocessing(metaclass=Singleton):
    def apply(self, image: np.ndarray) -> np.ndarray:
        image = cv2.resize(image, (224, 224))
        green_channel = image[:, :, 1]
        red_free_image = cv2.equalizeHist(green_channel)
        edges = cv2.Canny(red_free_image, 50, 150)
        blurred = cv2.GaussianBlur(red_free_image, (5, 5), 0)
        return np.stack([red_free_image, edges, blurred], axis=-1)

class PathologicalMyopiaPreprocessing(metaclass=Singleton):
    def apply(self, image: np.ndarray) -> np.ndarray:
        return cv2.resize(image, (224, 224))

class AgeIssuesPreprocessing(metaclass=Singleton):
    def apply(self, image: np.ndarray) -> np.ndarray:
        image = cv2.resize(image, (224, 224))
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced_image = clahe.apply(gray_image)
        image_faf = cv2.cvtColor(enhanced_image, cv2.COLOR_GRAY2BGR)
        edges = cv2.Canny(image, 100, 200)
        return cv2.addWeighted(image, 0.8, cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR), 0.2, 0)

class MULTICLASSPreprocessing(metaclass=Singleton):
    def apply(self, image: np.ndarray) -> np.ndarray:
        if image.ndim == 2: image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        image = cv2.resize(image, (224, 224), interpolation=cv2.INTER_AREA)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return (image / 255.0).astype(np.float32)

# --- مصنع الاستراتيجيات ---

STRATEGY_REGISTRY: Dict[str, Type[PreprocessingStrategy]] = {
    "CataractPreprocessing": CataractPreprocessing,
    "DiabetesPreprocessing": DiabetesPreprocessing,
    "GlaucomaPreprocessing": GlaucomaPreprocessing,
    "HypertensionPreprocessing": HypertensionPreprocessing,
    "PathologicalMyopiaPreprocessing": PathologicalMyopiaPreprocessing,
    "AgeIssuesPreprocessing": AgeIssuesPreprocessing,
    "MULTICLASSPreprocessing": MULTICLASSPreprocessing,
}

def get_strategy(name: str) -> PreprocessingStrategy:
    """Factory function to get an instance of a preprocessing strategy by name."""
    strategy_class = STRATEGY_REGISTRY.get(name)
    if not strategy_class:
        raise ValueError(f"استراتيجية المعالجة المسبقة '{name}' غير معروفة.")
    logging.info(f"استخدام استراتيجية المعالجة المسبقة: {name}")
    return strategy_class()
