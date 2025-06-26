# SHA_GROUP/sha/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated 
from django.contrib.auth import get_user_model
from django.utils import timezone
from .utils import generate_otp, get_tokens_for_user, api_response
from .serializers import SendOTPRequestSerializer, VerifyOTPRequestSerializer, UserSerializer, UserProfileSerializer
from rest_framework import generics

User = get_user_model()

class RequestPhoneOTP(APIView):
    """
    Handles sending an OTP to a mobile number for login/signup.
    Creates a new User account if one does not exist for the mobile number.
    The 'name' field (which is the username) will be set to mobile_number initially
    or can be updated later.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = SendOTPRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(False, "Validation error", data=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        mobile_number = serializer.validated_data.get("mobile_number")

        # Get or create the user based on mobile_number.
        # We need to provide a value for 'name' since it's now unique and required.
        # For implicit creation, we can use the mobile_number as a placeholder name,
        # or require the name in the request if it's part of the signup flow.
        # Here, we'll use a placeholder 'User_<mobile_number_suffix>' to ensure uniqueness.
        # In a real app, you'd likely have a separate registration endpoint for new users
        # where they explicitly provide a unique name.
        try:
            user = User.objects.get(mobile_number=mobile_number)
            created = False
        except User.DoesNotExist:
            # Generate a unique placeholder name.
            # In a full application, new users would register with a chosen name.
            placeholder_name = f"User_{mobile_number.replace('+', '')}_{timezone.now().timestamp()}".replace('.', '')
            user = User.objects.create(
                mobile_number=mobile_number,
                name=placeholder_name # Assigning a unique name here for creation
            )
            created = True


        otp = generate_otp()
        user.otp = otp
        user.otp_created_at = timezone.now()
        user.save()

        print(f"[DEBUG] OTP for {mobile_number}: {otp}")

        message = "OTP sent successfully. User account created." if created else "OTP sent successfully."
        return api_response(True, message, data={"otp_debug": otp}) # otp_debug for testing only


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

        user = User.objects.filter(mobile_number=mobile_number).first()

        if user and user.is_otp_valid(otp_input):
            user.otp = None
            user.otp_created_at = None
            user.save()

            tokens = get_tokens_for_user(user)
            user_data = UserSerializer(user).data
            return api_response(True, "Login successful", data={
                "access": tokens["access"],
                "refresh": tokens["refresh"],
                "user": user_data
            })
        else:
            return api_response(False, "Invalid or expired OTP", status_code=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView): # Custom APIView to handle POST for initial profile setup
    """
    API view for creating (first time POST) or retrieving/updating (GET/PUT/PATCH)
    the authenticated user's profile.
    """
    permission_classes = [IsAuthenticated] # User must be logged in

    def get(self, request, *args, **kwargs):
        """
        Retrieves the authenticated user's profile.
        """
        serializer = UserProfileSerializer(request.user)
        return api_response(True, "User profile retrieved successfully.", data=serializer.data)

    def post(self, request, *args, **kwargs):
        """
        Handles initial profile creation/completion for the authenticated user.
        This updates the existing user (created with placeholder name during OTP request).
        """
        # Pass instance=request.user to the serializer to perform an update operation
        # even though it's a POST request.
        serializer = UserProfileSerializer(instance=request.user, data=request.data, partial=False) # partial=False for full completion
        if serializer.is_valid():
            serializer.save() # This will call the update method of the serializer
            return api_response(True, "User profile created/completed successfully.", data=serializer.data, status_code=status.HTTP_200_OK)
        return api_response(False, "Validation error", data=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        """
        Handles full profile updates for the authenticated user.
        """
        serializer = UserProfileSerializer(instance=request.user, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            return api_response(True, "User profile updated successfully.", data=serializer.data, status_code=status.HTTP_200_OK)
        return api_response(False, "Validation error", data=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
        """
        Handles partial profile updates for the authenticated user.
        """
        serializer = UserProfileSerializer(instance=request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return api_response(True, "User profile updated successfully.", data=serializer.data, status_code=status.HTTP_200_OK)
        return api_response(False, "Validation error", data=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
