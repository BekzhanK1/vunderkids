from rest_framework.permissions import IsAuthenticated


class IsSuperUser(IsAuthenticated):
    """
    Allows access only to superusers.
    """
    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        return is_authenticated and request.user.is_superuser
    
class IsPrincipal(IsAuthenticated):
    """
    Allows access only to principal users.
    """
    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        return is_authenticated and request.user.is_principal()
    
class IsParent(IsAuthenticated):
    """
    Allows access only to parent users.
    """
    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        return is_authenticated and request.user.is_parent()
    
class IsTeacher(IsAuthenticated):
    """
    Allows access only to teacher users.
    """
    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        return is_authenticated and (request.user.is_teacher() or request.user.is_principal())