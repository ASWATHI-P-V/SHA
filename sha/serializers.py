# SHA_GROUP/sha/serializers.py
from rest_framework import serializers
import phonenumbers
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()


# Helper function for file size validation
def validate_file_size(value, max_size_mb=5):
    filesize = value.size
    if filesize > max_size_mb * 1024 * 1024: # Convert MB to bytes
        raise serializers.ValidationError(f"The maximum file size allowed is {max_size_mb}MB. Current size: {filesize / (1024 * 1024):.2f}MB")
    return value

# Helper function for file extension validation
def validate_file_extension(value, allowed_extensions):
    import os
    ext = os.path.splitext(value.name)[1].lower()
    if not ext in allowed_extensions:
        raise serializers.ValidationError(f"Unsupported file extension. Allowed are: {', '.join(allowed_extensions)}")
    return value

class UserSerializer(serializers.ModelSerializer):
    """
    Basic serializer for User model. 'name' is the unique identifier.
    """
    class Meta:
        model = User
        fields = ['id', 'name', 'mobile_number', 'email', 'is_active', 'is_staff']
        read_only_fields = ['id', 'is_active', 'is_staff']


class SendOTPRequestSerializer(serializers.Serializer):
    """
    Serializer for the 'send OTP' request.
    Validates the mobile number format.
    """
    mobile_number = serializers.CharField(max_length=20)
    country_code = serializers.CharField(max_length=5, required=False,
                                         help_text="Optional. Provide if mobile_number is not E.164 format (e.g., +12345678900).")

    def validate(self, attrs):
        mobile_number = attrs.get('mobile_number')
        country_code = attrs.get('country_code')

        if not mobile_number:
            raise serializers.ValidationError({"mobile_number": "This field is required."})

        # Validate and format the phone number to E.164
        if mobile_number.startswith('+'): # Assumed E.164 format
            try:
                parsed = phonenumbers.parse(mobile_number, None)
                if not phonenumbers.is_valid_number(parsed):
                    raise serializers.ValidationError("Provided mobile number is invalid.")
                attrs['mobile_number'] = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
                attrs['country_code'] = f"+{parsed.country_code}"
            except phonenumbers.NumberParseException as e:
                raise serializers.ValidationError(f"Mobile number format error: {e}")
        else: # Assumed local number, requires country_code
            if not country_code:
                raise serializers.ValidationError("Country code is required for non-E.164 mobile numbers.")
            full_phone = f"{country_code}{mobile_number}"
            try:
                parsed = phonenumbers.parse(full_phone, None)
            except phonenumbers.NumberParseException as e:
                raise serializers.ValidationError(f"Mobile number format error: {e}")

            if not phonenumbers.is_valid_number(parsed):
                raise serializers.ValidationError("Mobile number is invalid.")

            attrs['mobile_number'] = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
            attrs['country_code'] = f"+{parsed.country_code}"

        return attrs


class VerifyOTPRequestSerializer(serializers.Serializer):
    """
    Serializer for the 'verify OTP' request.
    Validates mobile number and OTP.
    """
    mobile_number = serializers.CharField(max_length=20)
    country_code = serializers.CharField(max_length=5, required=False)
    otp = serializers.CharField(max_length=6)

    def validate(self, attrs):
        # Reuse mobile number validation logic from SendOTPRequestSerializer
        mobile_number = attrs.get('mobile_number')
        country_code = attrs.get('country_code')

        if not mobile_number:
            raise serializers.ValidationError({"mobile_number": "This field is required."})

        if mobile_number.startswith('+'):
            try:
                parsed = phonenumbers.parse(mobile_number, None)
                if not phonenumbers.is_valid_number(parsed):
                    raise serializers.ValidationError("Provided mobile number is invalid.")
                attrs['mobile_number'] = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
                attrs['country_code'] = f"+{parsed.country_code}"
            except phonenumbers.NumberParseException as e:
                raise serializers.ValidationError(f"Mobile number format error: {e}")
        else:
            if not country_code:
                raise serializers.ValidationError("Country code is required for non-E.164 mobile numbers.")
            full_phone = f"{country_code}{mobile_number}"
            try:
                parsed = phonenumbers.parse(full_phone, None)
            except phonenumbers.NumberParseException as e:
                raise serializers.ValidationError(f"Mobile number format error: {e}")

            if not phonenumbers.is_valid_number(parsed):
                raise serializers.ValidationError("Mobile number is invalid.")

            attrs['mobile_number'] = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
            attrs['country_code'] = f"+{parsed.country_code}"

        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for creating (via POST) and updating (via PUT/PATCH) user profiles.
    Also used for retrieving user profile data.
    """
    profile_picture = serializers.ImageField(required=False, allow_null=True)
    proof_of_identity_document = serializers.FileField(required=False, allow_null=True)
    proof_of_address_document = serializers.FileField(required=False, allow_null=True)


    class Meta:
        model = User
        fields = [
            'id', 'name', 'email', 'mobile_number', 'profile_picture', 'date_of_birth',
            'guardian_name', 'address', 'city', 'pincode', 'father_husband_name',
            'proof_of_identity_type', 'proof_of_identity_document',
            'proof_of_address_type', 'proof_of_address_document',
            'gender', 'location', 'time_zone', 'terms_privacy_accepted',
        ]
        # 'mobile_number' is read-only here, as it's not meant to be updated via profile endpoint directly.
        # 'name' is the USERNAME_FIELD, must be unique. It's allowed for write as it's set on POST/PUT/PATCH.
        read_only_fields = ['id', 'mobile_number']

    def validate_profile_picture(self, value):
        if value:
            validate_file_size(value, max_size_mb=2)
            validate_file_extension(value, ['.jpg', '.jpeg', '.png'])
        return value

    def validate_proof_of_identity_document(self, value):
        if value:
            validate_file_size(value, max_size_mb=5)
            validate_file_extension(value, ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png'])
        return value

    def validate_proof_of_address_document(self, value):
        if value:
            validate_file_size(value, max_size_mb=5)
            validate_file_extension(value, ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png'])
        return value

    def validate_name(self, value):
        # When creating (POST) or updating (PUT/PATCH), ensure the name is unique.
        # For updates, allow the user to keep their current name.
        if self.instance and self.instance.name == value:
            return value
        if User.objects.filter(name=value).exists():
            raise serializers.ValidationError("This name is already taken. Please choose another.")
        return value

    def validate_terms_privacy_accepted(self, value):
        if not value:
            raise serializers.ValidationError("You must accept the terms of use and privacy policy.")
        return value

    def create(self, validated_data):
        # This create method will be called by the POST request to /api/profile/
        # The user object is already created (with a placeholder name) by RequestPhoneOTP.
        # So, we are effectively updating an existing user's profile based on the authenticated user.
        # We need to get the authenticated user from the context.
        # This 'create' is specifically for when the serializer is used in a CreateAPIView.
        # In our custom APIView, we'll manually update the user instance.
        raise NotImplementedError("This serializer's 'create' method is not directly used for new user creation in this flow.")


    def update(self, instance, validated_data):
        # This update method will be called for POST (initial profile completion)
        # and PUT/PATCH (subsequent updates).
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance