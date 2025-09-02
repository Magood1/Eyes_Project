# apps/diagnosis/exceptions.py
class DiagnosisError(Exception):
    """
    استثناء أساسي لتطبيق التشخيص.
    يُستخدم للأخطاء المتوقعة في منطق العمل والتي لا ينبغي إعادة محاولتها.
    """
    pass

class ModelInferenceError(DiagnosisError):
    """يحدث عند فشل استدلال النموذج (خطأ غير قابل للاسترداد)."""
    pass

class ModelLoadingError(DiagnosisError):
    """يحدث عند فشل تحميل النموذج (خطأ غير قابل للاسترداد)."""
    pass
