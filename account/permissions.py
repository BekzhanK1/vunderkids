from rest_framework.permissions import IsAuthenticated, BasePermission, SAFE_METHODS


class IsSuperUser(IsAuthenticated):
    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        return is_authenticated and request.user.is_superuser
    
class IsParent(IsAuthenticated):
    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        return is_authenticated and request.user.is_parent

class IsStudent(IsAuthenticated):
    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        return is_authenticated and request.user.is_student
    
class IsStaff(IsAuthenticated):
    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        return is_authenticated and request.user.is_staff
    
class IsSuperUserOrStaffOrReadOnly(IsAuthenticated):
    """
    Custom permission to only allow superusers or staff to edit it.
    Read permissions are allowed to any authenticated user.
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return request.user and (request.user.is_superuser or request.user.is_staff)
    
class IsSupervisor(IsAuthenticated):
    def has_permission(self, request, view):
        return request.user and request.user.is_supervisor
