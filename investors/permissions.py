# permissions.py

from rest_framework import permissions

class IsAdminUser(permissions.BasePermission):
    """
    Custom permission to only allow administrators to access.
    """
    def has_permission(self, request, view):
        # Allow access only to staff (admin) users
        return request.user and request.user.is_staff

    def has_object_permission(self, request, view, obj):
        # Admins have full object access
        return request.user and request.user.is_staff

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit/delete it,
    or allow admin users full access.
    Assumes the model instance has a 'user' attribute which is a ForeignKey to User.
    """
    def has_object_permission(self, request, view, obj):
        # Admins always have permission
        if request.user and request.user.is_staff:
            return True

        # Read permissions are allowed to any request, so we'll always allow GET, HEAD, or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the object.
        # Check if the object's 'user' field matches the requesting user.
        return obj.user == request.user