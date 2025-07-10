# SHA_GROUP/sha/permissions.py
from rest_framework import permissions
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

#MARK: isadmin or readonly
class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow administrators to edit objects.
    Read-only access is allowed for everyone else.
    """
    def has_permission(self, request, view):
        logger.debug(f"IsAdminOrReadOnly - Method: {request.method}, Path: {request.path}")
        # Allow GET, HEAD, OPTIONS requests for anyone
        if request.method in permissions.SAFE_METHODS:
            logger.debug("IsAdminOrReadOnly - SAFE_METHODS, allowing.")
            return True
        # Allow write access only to admin users
        result = request.user and request.user.is_staff
        logger.debug(f"IsAdminOrReadOnly - Write method, User: {request.user}, Is Staff: {request.user.is_staff if request.user else 'N/A'}, Result: {result}")
        return result

#MARK: isadmin user
class IsAdminUser(permissions.BasePermission):
    """
    Allows access only to admin users.
    """
    def has_permission(self, request, view):
        logger.info(f"IsAdminUser - Checking permission for request.user: {request.user}")

        if request.user.is_authenticated:
            logger.info(f"IsAdminUser - User is authenticated. ID: {request.user.id}, Username: {request.user.get_username()}")
            logger.info(f"IsAdminUser - User is_staff: {request.user.is_staff}")
            logger.info(f"IsAdminUser - User is_superuser: {request.user.is_superuser}")
            logger.info(f"IsAdminUser - User is_active: {request.user.is_active}")
        else:
            logger.info("IsAdminUser - User is NOT authenticated.")

        # This is the actual permission logic
        permission_granted = request.user and request.user.is_staff
        logger.info(f"IsAdminUser - Final permission decision: {permission_granted}")
        return permission_granted

 