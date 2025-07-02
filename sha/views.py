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
        # 1. Get the target user instance.
        #    If PK is provided, get_object attempts to fetch that user.
        #    If no PK, get_object returns request.user.
        user_to_delete = self.get_object(request, pk)

        # 2. Handle cases where the user_to_delete was not found
        #    (e.g., non-existent PK or get_object returned None due to some internal logic).
        if not user_to_delete:
            # If a PK was supplied but the user doesn't exist, it's a 404.
            # If get_object returned None because a non-staff user tried to access another PK,
            # this would fall into the 404/403 below.
            if pk and not request.user.is_staff: # Explicitly deny non-admin accessing others
                return api_response(False, "You do not have permission to delete other users' profiles.", status_code=status.HTTP_403_FORBIDDEN)
            return api_response(False, "User not found.", status_code=status.HTTP_404_NOT_FOUND)

        # 3. Permission Checks for Deletion:

        # Scenario A: Admin deleting any user (including themselves if pk is explicitly provided)
        if request.user.is_staff:
            # Admin can delete any user if PK is provided.
            # Admin can delete their own profile IF a PK is provided (to prevent accidental self-deletion)
            if pk and user_to_delete.pk == request.user.pk:
                # Admin deleting their own profile via PK
                pass # Allow
            elif not pk and user_to_delete.pk == request.user.pk:
                # Admin trying to delete their own profile without a PK (e.g., /profile/DELETE)
                return api_response(False, "Admins must specify the user ID (pk) to delete their own profile.", status_code=status.HTTP_400_BAD_REQUEST)
            # If admin is deleting another user (pk is present and not their own pk), that's allowed by default
            # because we're inside the request.user.is_staff block.
        # Scenario B: Regular user deleting their own profile (no PK or PK matches their own)
        else: # Not an admin
            if pk and user_to_delete.pk != request.user.pk:
                # Regular user trying to delete another user's profile via PK
                return api_response(False, "You do not have permission to delete other users' profiles.", status_code=status.HTTP_403_FORBIDDEN)
            elif pk is None and user_to_delete.pk != request.user.pk:
                 # This case shouldn't happen if get_object returns request.user when pk is None
                 # but it's a defensive check.
                 return api_response(False, "Permission denied.", status_code=status.HTTP_403_FORBIDDEN)


        # 4. Perform the deletion if all checks pass
        mobile_number_deleted = user_to_delete.mobile_number # Store for response message
        user_to_delete.delete() # Perform the deletion

        return api_response(True, f"User '{mobile_number_deleted}' and associated profile deleted successfully.", status_code=status.HTTP_204_NO_CONTENT)



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

    