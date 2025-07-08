# SHA_GROUP/sha/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser # Import IsAdminUser
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import generics # For ListAPIView

from .utils import generate_otp, get_tokens_for_user, api_response
from .serializers import (
    SendOTPRequestSerializer, VerifyOTPRequestSerializer,
    UserSerializer, UserProfileSerializer
)


User = get_user_model()

class RequestPhoneOTP(APIView):
    """
    Handles sending an OTP to a mobile number for login/signup.
    Creates a new User account if one does not exist for the mobile number.
    Mobile number is now the unique identifier (USERNAME_FIELD).
    """
    permission_classes = [AllowAny]
    authentication_classes = [] # Explicitly disable authentication

    def post(self, request):
        serializer = SendOTPRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(False, "Validation error", data=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        mobile_number = serializer.validated_data.get("mobile_number")

        try:
            # Try to get the user by mobile_number (which is now USERNAME_FIELD)
            user = User.objects.get(mobile_number=mobile_number)
            created = False
        except User.DoesNotExist:
            # Create a new user with mobile_number as username.
            # 'name' can be an empty string or None initially, as it's no longer unique.
            user = User.objects.create_user(
                mobile_number=mobile_number, # This is the USERNAME_FIELD
                name="", # Placeholder for name, will be filled via profile update
                is_active=True
            )
            user.set_unusable_password() # No password set during OTP flow
            user.save()
            created = True

        otp = generate_otp()
        user.otp = otp
        user.otp_created_at = timezone.now()
        user.save()

        print(f"[DEBUG] OTP for {mobile_number}: {otp}")

        message = "OTP sent successfully. Please proceed to verify OTP and complete your profile." if created else "OTP sent successfully. Please verify to login."
        return api_response(True, message, data={"otp_debug": otp})


class VerifyOTP(APIView):
    """
    Verifies the provided OTP for a mobile number.
    If successful, returns JWT tokens for the user.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = VerifyOTPRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(False, "Validation error", data=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        mobile_number = serializer.validated_data.get("mobile_number")
        otp_input = serializer.validated_data.get("otp")

        # User.objects.filter(mobile_number=mobile_number).first() is fine, as mobile_number is unique
        user = User.objects.filter(mobile_number=mobile_number).first()

        if not user:
            return api_response(False, "User with this mobile number does not exist.", status_code=status.HTTP_404_NOT_FOUND)

        if user.is_otp_valid(otp_input):
            user.otp = None
            user.otp_created_at = None
            user.save()

            tokens = get_tokens_for_user(user)
            user_data = UserSerializer(user).data
            return api_response(True, "Login successful", data={
                "access": tokens["access"],
                # "refresh": tokens["refresh"],
                "user": user_data
            })
        else:
            return api_response(False, "Invalid or expired OTP", status_code=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    """
    API view for creating (first time POST) or retrieving/updating (GET/PUT/PATCH)
    the authenticated user's profile, or for administrators to manage any user's profile.
    """
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk=None):
        if pk: # Admin is trying to access a specific user
            if request.user.is_staff: # Check if the request is from an admin
                try:
                    return User.objects.get(pk=pk)
                except User.DoesNotExist:
                    return None
            else:
                # Non-admin trying to access another user's profile - forbidden
                return None
        else: # Regular user accessing their own profile
            return request.user

    def get(self, request, pk=None, *args, **kwargs):
        user_instance = self.get_object(request, pk)
        if not user_instance:
            if pk and not request.user.is_staff:
                return api_response(False, "You do not have permission to access other users' profiles.", status_code=status.HTTP_403_FORBIDDEN)
            return api_response(False, "User not found.", status_code=status.HTTP_404_NOT_FOUND)

        serializer = UserProfileSerializer(user_instance)
        return api_response(True, "User profile retrieved successfully.", data=serializer.data)

    def post(self, request, pk=None, *args, **kwargs):
        # POST usually for initial creation/completion of *own* profile.
        # Admin creating a profile should probably go through a different endpoint
        # or a different serializer/logic if they are creating a new user + profile.
        if pk and not request.user.is_staff:
            return api_response(False, "You do not have permission to create profiles for other users.", status_code=status.HTTP_403_FORBIDDEN)

        user_instance = self.get_object(request, pk) if pk else request.user
        if not user_instance:
            return api_response(False, "User not found or forbidden.", status_code=status.HTTP_404_NOT_FOUND)

        serializer = UserProfileSerializer(instance=user_instance, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            message = "User profile created successfully." if not pk else f"User profile for {user_instance.username} created/completed by admin."
            return api_response(True, message, data=serializer.data, status_code=status.HTTP_200_OK)
        return api_response(False, "Validation error", data=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk=None, *args, **kwargs):
        user_instance = self.get_object(request, pk)
        if not user_instance:
            if pk and not request.user.is_staff:
                return api_response(False, "You do not have permission to update other users' profiles.", status_code=status.HTTP_403_FORBIDDEN)
            return api_response(False, "User not found.", status_code=status.HTTP_404_NOT_FOUND)

        serializer = UserProfileSerializer(instance=user_instance, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            message = "User profile updated successfully." if not pk else f"User profile for {user_instance.username} updated by admin."
            return api_response(True, message, data=serializer.data, status_code=status.HTTP_200_OK)
        return api_response(False, "Validation error", data=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk=None, *args, **kwargs):
        user_instance = self.get_object(request, pk)
        if not user_instance:
            if pk and not request.user.is_staff:
                return api_response(False, "You do not have permission to update other users' profiles.", status_code=status.HTTP_403_FORBIDDEN)
            return api_response(False, "User not found.", status_code=status.HTTP_404_NOT_FOUND)

        serializer = UserProfileSerializer(instance=user_instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            message = "User profile updated successfully." if not pk else f"User profile for {user_instance.username} partially updated by admin."
            return api_response(True, message, data=serializer.data, status_code=status.HTTP_200_OK)
        return api_response(False, "Validation error", data=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None, *args, **kwargs):
        # Determine the user to be deleted based on PK or the authenticated user
        user_to_delete = self.get_object(request, pk)

        if not user_to_delete:
            # This handles cases where the PK was invalid or a non-admin tried to access another user's PK.
            # Your get_object already handles returning None for forbidden access.
            if pk and not request.user.is_staff:
                return api_response(False, "You do not have permission to delete other users' profiles.", status_code=status.HTTP_403_FORBIDDEN)
            return api_response(False, "User not found.", status_code=status.HTTP_404_NOT_FOUND)

        # Permission check for deletion
        if request.user.is_staff:
            # Admins can delete any user's profile, specified by PK.
            # If an admin tries to delete their own without PK (e.g., /profile/delete),
            # user_to_delete will be request.user. We can enforce PK for admin self-deletion
            # to prevent accidental account deletion.
            if not pk and user_to_delete.pk == request.user.pk:
                return api_response(False, "Admins must specify the user ID (pk) to delete their own profile to prevent accidental full account deletion.", status_code=status.HTTP_400_BAD_REQUEST)
            # Otherwise, admin can proceed.
            pass
        else: # Not an admin
            # A non-admin can ONLY delete their OWN profile.
            if user_to_delete.pk != request.user.pk:
                return api_response(False, "You do not have permission to delete other users' profiles.", status_code=status.HTTP_403_FORBIDDEN)
            # If user_to_delete.pk == request.user.pk, it means they are deleting their own, so pass.

        # If we reach here, permission is granted.
        try:
            mobile_number_deleted = user_to_delete.mobile_number # Assuming 'mobile_number' exists on your User model
            user_to_delete.delete()
            return api_response(True, f"User '{mobile_number_deleted}' and associated profile deleted successfully.", status_code=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            # Log the exception for debugging on the server side
            # import logging
            # logger = logging.getLogger(__name__)
            # logger.error(f"Error deleting user {user_to_delete.pk}: {e}", exc_info=True)
            return api_response(False, "An error occurred during deletion.", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
class AdminUserProfileView(APIView):
    """
    API view for administrators to retrieve or update any user's profile.
    """
    permission_classes = [IsAuthenticated, IsAdminUser] # Only authenticated admins can access

    def get_object(self, pk):
        try:
            # Assuming profile information is directly on the User model
            # If UserProfile is a separate model linked by OneToOneField, you'd fetch that
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            return None

    def get(self, request, pk, *args, **kwargs):
        user_instance = self.get_object(pk)
        if not user_instance:
            return api_response(False, "User not found.", status_code=status.HTTP_404_NOT_FOUND)

        serializer = UserProfileSerializer(user_instance)
        return api_response(True, f"User profile for {user_instance.username} retrieved successfully.", data=serializer.data)

    def put(self, request, pk, *args, **kwargs):
        user_instance = self.get_object(pk)
        if not user_instance:
            return api_response(False, "User not found.", status_code=status.HTTP_404_NOT_FOUND)

        serializer = UserProfileSerializer(instance=user_instance, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            return api_response(True, f"User profile for {user_instance.username} updated successfully.", data=serializer.data, status_code=status.HTTP_200_OK)
        return api_response(False, "Validation error", data=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk, *args, **kwargs):
        user_instance = self.get_object(pk)
        if not user_instance:
            return api_response(False, "User not found.", status_code=status.HTTP_404_NOT_FOUND)

        serializer = UserProfileSerializer(instance=user_instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return api_response(True, f"User profile for {user_instance.username} partially updated successfully.", data=serializer.data, status_code=status.HTTP_200_OK)
        return api_response(False, "Validation error", data=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

    # You might not need POST for admin updates, as profiles should already exist.
    # If an admin needs to *create* a user and their initial profile, that would typically be a separate
    # user creation endpoint.

    