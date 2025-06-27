# permissions.py (if you create a custom one, otherwise use rest_framework.permissions.IsAdminUser)
from rest_framework import permissions

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow administrators to edit objects.
    Read-only access is allowed for everyone else.
    """
    def has_permission(self, request, view):
        # Allow GET, HEAD, OPTIONS requests for anyone
        if request.method in permissions.SAFE_METHODS:
            return True
        # Allow write access only to admin users
        return request.user and request.user.is_staff

class IsAdminUser(permissions.BasePermission):
    """
    Allows access only to admin users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_staff