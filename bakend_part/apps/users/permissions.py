# apps/users/permissions.py
from rest_framework.permissions import BasePermission,  SAFE_METHODS
from .models import User


class IsAdmin(BasePermission):
    """صلاحية تسمح بالوصول للمسؤولين فقط."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == User.Roles.ADMIN)

class IsDoctor(BasePermission):
    """صلاحية تسمح بالوصول للأطباء فقط."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == User.Roles.DOCTOR)
    

class IsAssignedDoctorOrReadOnly(BasePermission):
    """
    يسمح بالوصول الكامل إذا كان الطبيب مرتبطًا بالمريض.
    يسمح بالوصول للقراءة فقط للآخرين (يمكن تعديل هذا لاحقًا).
    """
    def has_object_permission(self, request, view, obj):
        # obj هنا هو instance من Patient
        if request.method in SAFE_METHODS:
            return True
        # يسمح بالكتابة فقط إذا كان المستخدم طبيبًا مرتبطًا بهذا المريض
        return request.user in obj.doctors.all()
    

class IsOwnerOrAdmin(BasePermission):
    """
    يسمح بالوصول للمالك أو المسؤول فقط.
    يفترض أن الكائن (obj) لديه حقل 'doctor' أو 'physician' أو 'user'.
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff: # المسؤولون يرون كل شيء
            return True
        
        # تحقق من وجود حقل يربط الكائن بالمستخدم
        owner_field = None
        if hasattr(obj, 'doctor'):
            owner_field = obj.doctor
        elif hasattr(obj, 'physician'):
            owner_field = obj.physician
        elif hasattr(obj, 'user'):
            owner_field = obj.user

        return owner_field == request.user
    