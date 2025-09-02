# ocular_diagnosis_system/models/preprocessing.py
import cv2
import numpy as np
from typing import Protocol
from apps.diagnosis.ai_pipeline.models.singleton import Singleton



class PreprocessingStrategy(Protocol):
    """
    Protocol defining the interface for all preprocessing strategies.
    Ensures that any strategy class will have an 'apply' method.
    """
    def apply(self, image: np.ndarray) -> np.ndarray:
        """Applies a specific preprocessing pipeline to an image."""
        ...

# Using Singleton ensures that we only create one instance of each strategy, saving memory.
class CataractPreprocessing(metaclass=Singleton):
    """Preprocessing strategy tailored for Cataract detection."""
    def apply(self, image: np.ndarray) -> np.ndarray:
        image = cv2.resize(image, (224, 224))
        # Increase brightness to better visualize lens opacity
        return cv2.convertScaleAbs(image, alpha=1.0, beta=50)

class DiabetesPreprocessing(metaclass=Singleton):
    """Preprocessing strategy for Diabetic Retinopathy, enhancing microaneurysms."""
    def apply(self, image: np.ndarray) -> np.ndarray:
        image = cv2.resize(image, (224, 224))
        # Isolate green channel for better contrast of red lesions
        green_channel = image[:, :, 1]
        red_free_image = cv2.merge([green_channel, green_channel, green_channel])
        return cv2.convertScaleAbs(red_free_image, alpha=1.5, beta=50)

class GlaucomaPreprocessing(metaclass=Singleton):
    """Basic preprocessing for Glaucoma, focusing on normalization."""
    def apply(self, image: np.ndarray) -> np.ndarray:
        image = cv2.resize(image, (224, 224))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        # Normalize pixels to the [0, 1] range
        image = image / 255.0
        return image.astype(np.float32)

class HypertensionPreprocessing(metaclass=Singleton):
    """Advanced feature engineering for Hypertensive Retinopathy to see vessel changes."""
    def apply(self, image: np.ndarray) -> np.ndarray:
        image = cv2.resize(image, (224, 224))
        green_channel = image[:, :, 1]
        # Enhance contrast and find edges to highlight vascular structure
        red_free_image = cv2.equalizeHist(green_channel)
        edges = cv2.Canny(red_free_image, 50, 150)
        blurred = cv2.GaussianBlur(red_free_image, (5, 5), 0)
        # Stack channels to create a feature-rich image
        return np.stack([red_free_image, edges, blurred], axis=-1)

class PathologicalMyopiaPreprocessing(metaclass=Singleton):
    """Simple resizing for Pathological Myopia."""
    def apply(self, image: np.ndarray) -> np.ndarray:
        return cv2.resize(image, (224, 224))

class AgeIssuesPreprocessing(metaclass=Singleton):
    """Preprocessing for age-related issues like AMD, enhancing local contrast."""
    def apply(self, image: np.ndarray) -> np.ndarray:
        image = cv2.resize(image, (224, 224))
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # CLAHE is excellent for enhancing features in fundus images
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced_image = clahe.apply(gray_image)
        # Re-merge to 3 channels if needed by the model, or combine with other features
        image_faf = cv2.cvtColor(enhanced_image, cv2.COLOR_GRAY2BGR)
        edges = cv2.Canny(image, 100, 200)
        return cv2.addWeighted(image, 0.8, cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR), 0.2, 0)
    


class MULTICLASSPreprocessing(metaclass=Singleton):
    """
    استراتيجية معالجة مسبقة شاملة (للإنتاج):
    - إعادة التحجيم إلى 224x224
    - تحويل إلى RGB
    - التطبيع إلى [0,1] float32
    - زيادة بيانات أساسية (انعكاس أفقي عشوائي، دوران، تعديل تباين)
    
    ملاحظة: هذه الاستراتيجية تعكس منطق خط الأنابيب (data_handler.py) 
    بحيث تكون جاهزة للإنتاج ضمن نظام الاستراتيجيات.
    """
    def __init__(self, image_size: int = 224):
        self.image_size = image_size

    def apply(self, image: np.ndarray) -> np.ndarray:
        """
        تنفيذ جميع خطوات المعالجة المسبقة:
        1. التأكد من أن الصورة ملونة (3 قنوات).
        2. إعادة التحجيم إلى حجم ثابت.
        3. التحويل إلى RGB.
        4. التطبيع إلى [0,1] float32.
        """
        if image is None:
            raise ValueError("الصورة المدخلة None")

        # 1) التأكد من عدد القنوات (تحويل رمادية إلى 3 قنوات)
        if image.ndim == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

        # 2) إعادة التحجيم
        image = cv2.resize(image, (self.image_size, self.image_size), interpolation=cv2.INTER_AREA)

        # 3) التحويل إلى RGB (معظم النماذج تتوقع RGB)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # 4) التطبيع إلى [0,1] float32
        image = image.astype(np.float32) / 255.0

        return image.astype(np.float32)
    


class TABULARPreprocessing(metaclass=Singleton):
    """
    استراتيجية معالجة مسبقة للمتجه الجدولي.
    في هذه الحالة، لا تقوم بأي تحويل، فقط تتحقق من الشكل.
    يمكن توسيعها في المستقبل لتشمل (Scaling, Imputation).
    """
    def __init__(self, expected_features: int = 18):
        self.expected_features = expected_features
    
         
    def apply(self, feature_vector: np.ndarray) -> np.ndarray:
        """
        تتحقق من أن متجه الميزات له الشكل الصحيح.
        """
        if feature_vector.ndim != 1 or feature_vector.shape[0] != self.expected_features:
            raise ValueError(f"متجه الميزات المدخل يجب أن يكون متجهًا أحاديًا بطول {self.expected_features}, "
                             f"ولكن تم استقبال شكل {feature_vector.shape}")
        
        # حاليًا، لا توجد معالجة إضافية. يمكن إضافة Scaling هنا إذا تم تدريب النموذج عليه.
        return feature_vector.astype(np.float32)
    