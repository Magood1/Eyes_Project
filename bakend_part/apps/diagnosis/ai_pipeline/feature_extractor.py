# FILE: backend_logic/ai_pipeline/feature_extractor.py

import numpy as np

def _calculate_f1_score(p_multi: float, p_expert: float, epsilon: float = 1e-8) -> float:
    """
    يحسب المتوسط التوافقي (شبيه بـ F1-score) بين احتمالتين.
    هذا هو المنطق الأساسي للدمج.
    """
    return (2 * p_multi * p_expert) / (p_multi + p_expert + epsilon)

def create_fused_feature_vector(
    multi_class_probs_left: np.ndarray,
    multi_class_probs_right: np.ndarray,
    expert_probs_left: np.ndarray,
    expert_probs_right: np.ndarray,
    age: float,
    gender: int
) -> np.ndarray:
    """
    ينشئ متجه ميزات نهائي مكون من 18 بُعدًا ليدخل إلى النموذج الجدولي.
    هذا المنطق يجب أن يكون متطابقًا تمامًا بين بيئة التدريب والإنتاج.
    
    Args:
        multi_class_probs_left (np.ndarray): مصفوفة احتمالات (8,) للعين اليسرى من النموذج العام.
        multi_class_probs_right (np.ndarray): مصفوفة احتمالات (8,) للعين اليمنى من النموذج العام.
        expert_probs_left (np.ndarray): مصفوفة احتمالات (6,) للعين اليسرى من النماذج المتخصصة.
        expert_probs_right (np.ndarray): مصفوفة احتمالات (6,) للعين اليمنى من النماذج المتخصصة.
        age (float): عمر المريض.
        gender (int): جنس المريض (e.g., 1 for Male, 0 for Female).

    Returns:
        np.ndarray: متجه ميزات نهائي بطول 18.
    """
    # التحقق من الأبعاد المدخلة
    if multi_class_probs_left.shape != (8,) or expert_probs_left.shape != (6,):
        raise ValueError("أبعاد مدخلات مصفوفات الاحتمالات غير صحيحة.")

    # --- دمج ميزات العين اليسرى ---
    # الفئة الأولى هي 'Normal'
    fused_features_left = [multi_class_probs_left[0]]
    # دمج الـ 6 أمراض المتخصصة
    for i in range(6):
        p_multi = multi_class_probs_left[i + 1]
        p_expert = expert_probs_left[i]
        fused_features_left.append(_calculate_f1_score(p_multi, p_expert))
    # الفئة الأخيرة هي 'Other'
    fused_features_left.append(multi_class_probs_left[7])

    # --- دمج ميزات العين اليمنى ---
    fused_features_right = [multi_class_probs_right[0]]
    for i in range(6):
        p_multi = multi_class_probs_right[i + 1]
        p_expert = expert_probs_right[i]
        fused_features_right.append(_calculate_f1_score(p_multi, p_expert))
    fused_features_right.append(multi_class_probs_right[7])
    
    # --- تجميع المتجه النهائي ---
    # 8 ميزات للعين اليسرى + 8 ميزات للعين اليمنى + 2 ديموغرافية = 18 ميزة
    final_vector = np.concatenate([
        fused_features_left,
        fused_features_right,
        [age, gender]
    ])

    return final_vector.astype(np.float32)