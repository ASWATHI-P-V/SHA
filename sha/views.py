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
from django.core.exceptions import ValidationError as DjangoValidationError

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
        if pk: # PK is provided in the URL
            if request.user.is_staff: # Admin trying to access a specific user by PK
                try:
                    return User.objects.get(pk=pk)
                except User.DoesNotExist:
                    return None # User with PK not found
            else:
                # Non-admin trying to access *any* user's profile by PK - forbidden
                return None
        else: # No PK provided in the URL, implies current authenticated user
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
        if pk and not request.user.is_staff:
            return api_response(False, "You do not have permission to create profiles for other users.", status_code=status.HTTP_403_FORBIDDEN)

        user_instance = self.get_object(request, pk) if pk else request.user
        if not user_instance:
            return api_response(False, "Target user for profile creation not found or forbidden.", status_code=status.HTTP_404_NOT_FOUND)

        serializer = UserProfileSerializer(instance=user_instance, data=request.data, partial=False)
        if serializer.is_valid():
            try:
                serializer.save()
                message = "User profile created successfully." if not pk else f"User profile for {user_instance.username} created/completed by admin."
                return api_response(True, message, data=serializer.data, status_code=status.HTTP_200_OK)
            except DjangoValidationError as e:
                return api_response(False, f"Model validation error: {e.message}", data=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return api_response(False, f"An unexpected error occurred during profile creation: {str(e)}", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            first_error_key = next(iter(serializer.errors))
            first_error_message = serializer.errors[first_error_key][0]
            return api_response(False, f" {first_error_key}: {first_error_message}", data=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk=None, *args, **kwargs):
        user_instance = self.get_object(request, pk)
        if not user_instance:
            if pk and not request.user.is_staff:
                return api_response(False, "You do not have permission to update other users' profiles.", status_code=status.HTTP_403_FORBIDDEN)
            return api_response(False, "User not found for update.", status_code=status.HTTP_404_NOT_FOUND)

        # Explicit permission check for update: Admin can update any, non-admin only their own.
        if not request.user.is_staff and user_instance.pk != request.user.pk:
             return api_response(False, "You do not have permission to update other users' profiles.", status_code=status.HTTP_403_FORBIDDEN)

        serializer = UserProfileSerializer(instance=user_instance, data=request.data, partial=False)
        if serializer.is_valid():
            try:
                serializer.save()
                message = "User profile updated successfully." if not pk else f"User profile for {user_instance.username} updated by admin."
                return api_response(True, message, data=serializer.data, status_code=status.HTTP_200_OK)
            except DjangoValidationError as e:
                return api_response(False, f"Model validation error during update: {e.message}", data=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return api_response(False, f"An unexpected error occurred during profile update: {str(e)}", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            first_error_key = next(iter(serializer.errors))
            first_error_message = serializer.errors[first_error_key][0]
            return api_response(False, f"Validation failed for {first_error_key}: {first_error_message}", data=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk=None, *args, **kwargs):
        user_instance = self.get_object(request, pk)
        if not user_instance:
            if pk and not request.user.is_staff:
                return api_response(False, "You do not have permission to update other users' profiles.", status_code=status.HTTP_403_FORBIDDEN)
            return api_response(False, "User not found for partial update.", status_code=status.HTTP_404_NOT_FOUND)

        # Explicit permission check for update: Admin can update any, non-admin only their own.
        if not request.user.is_staff and user_instance.pk != request.user.pk:
             return api_response(False, "You do not have permission to update other users' profiles.", status_code=status.HTTP_403_FORBIDDEN)

        serializer = UserProfileSerializer(instance=user_instance, data=request.data, partial=True)
        if serializer.is_valid():
            try:
                serializer.save()
                message = "User profile updated successfully." if not pk else f"User profile for {user_instance.username} partially updated by admin."
                return api_response(True, message, data=serializer.data, status_code=status.HTTP_200_OK)
            except DjangoValidationError as e:
                return api_response(False, f"Model validation error during partial update: {e.message}", data=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return api_response(False, f"An unexpected error occurred during profile partial update: {str(e)}", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            first_error_key = next(iter(serializer.errors))
            first_error_message = serializer.errors[first_error_key][0]
            return api_response(False, f"Validation failed for {first_error_key}: {first_error_message}", data=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None, *args, **kwargs):
        user_to_delete = self.get_object(request, pk)

        # Handle cases where the target user was not found or not accessible
        if not user_to_delete:
            if pk and not request.user.is_staff:
                # This means a non-admin tried to specify a PK for another user
                return api_response(False, "You do not have permission to delete other users' profiles.", status_code=status.HTTP_403_FORBIDDEN)
            # This covers cases where PK was valid but user_to_delete was None from get_object
            return api_response(False, "User to delete not found.", status_code=status.HTTP_404_NOT_FOUND)

        # Permission check:
        if request.user.is_staff:
            # Admins can delete any user's profile.
            # For self-deletion as admin, requiring PK is a good safety measure.
            if not pk and user_to_delete.pk == request.user.pk:
                return api_response(False, "As an admin, you must specify your user ID (pk) to delete your own profile to prevent accidental full account deletion.", status_code=status.HTTP_400_BAD_REQUEST)
            # If PK is provided or it's another user, admin can proceed.
        else: # Not an admin
            # Non-admins can ONLY delete their own profile.
            if user_to_delete.pk != request.user.pk:
                return api_response(False, "You do not have permission to delete other users' profiles.", status_code=status.HTTP_403_FORBIDDEN)
            # If user_to_delete.pk == request.user.pk, it's their own profile, so proceed.

        # If all checks pass, perform the deletion
        try:
            mobile_number_deleted = getattr(user_to_delete, 'mobile_number', 'N/A')
            user_to_delete.delete()
            return api_response(True, f"User '{mobile_number_deleted}' and associated profile deleted successfully.", status_code=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            # Catch any unexpected errors during the deletion process
            # It's highly recommended to log these errors for debugging.
            return api_response(False, f"An internal server error occurred while deleting the user: {str(e)}", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
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

    