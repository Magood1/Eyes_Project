# apps/diagnosis/ai_pipeline/config.py
from django.conf import settings
import os

# الآن، بدلاً من المسارات الثابتة، سنقرأها من إعدادات Django
# هذا يسمح لنا بتغيير مسارات النماذج لكل بيئة (تطوير، إنتاج)
MULTI_CLASS_MODEL_PATH = getattr(settings, 'AI_MULTI_CLASS_MODEL_PATH')
TABULAR_MODEL_PATH = getattr(settings, 'AI_TABULAR_MODEL_PATH')


# قائمة بنماذج الخبراء وأسماء الأمراض المقابلة لها
# (الترتيب هنا مهم ويجب أن يتطابق مع مخرجات النماf'sذح متعدد الفئات)
DISEASE_CLASSES = [
    ("Cataract", "AI_EXPERT_CATARACT_MODEL_PATH"),
    ("Diabetes", "AI_EXPERT_DIABETES_MODEL_PATH"),
    ("Glaucoma", "AI_EXPERT_GLAUCOMA_MODEL_PATH"),
    ("Hypertension", "AI_EXPERT_HYPERTENSION_MODEL_PATH"),
    ("Pathological Myopia", "AI_EXPERT_MYOPIA_MODEL_PATH"),
    ("Age Issues", "AI_EXPERT_AGE_MODEL_PATH"),
]


EXPERT_MODELS_CONFIG = [
    {
        "disease": disease,
        "path": getattr(settings, path_var, None)
    }
    for disease, path_var in DISEASE_CLASSES
]

















# ترتيب الفئات في مخرجات النموذج متعدد الفئات (8 فئات)
# هذا الترتيب حاسم لدالة دمج السمات
MULTI_CLASS_OUTPUT_MAPPING = {
    0: "Normal",
    1: "Cataract",
    2: "Diabetes",
    3: "Glaucoma",
    4: "Hypertension",
    5: "Pathological Myopia",
    6: "Age Issues",
    7: "Other Disorders"
}