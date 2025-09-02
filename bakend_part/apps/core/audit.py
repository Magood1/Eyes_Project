# apps/core/audit.py
import logging

# احصل على logger مخصص للتدقيق
audit_logger = logging.getLogger('audit')

def log_patient_access(user, patient, action):
    """يسجل حدث وصول إلى بيانات المريض."""
    audit_logger.info(f"User '{user.username}' (ID: {user.id}) {action} patient '{patient.full_name}' (ID: {patient.id}).")