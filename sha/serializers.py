# SHA_GROUP/sha/serializers.py
from rest_framework import serializers
import phonenumbers
from django.contrib.auth import get_user_model
from django.conf import settings
from .models import UserProfileSettings

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
    Basic serializer for User model. 'mobile_number' is the unique identifier.
    """
    class Meta:
        model = User
        fields = ['id', 'name', 'mobile_number', 'email', 'is_active', 'is_staff']
        read_only_fields = ['id', 'is_active', 'is_staff', 'mobile_number'] # mobile_number is read-only here for basic display/return

class SendOTPRequestSerializer(serializers.Serializer):
    """
    Serializerr for the 'send OTP' request.
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
    Dynamically limits editable fields for non-admin users based on UserProfileSettings.
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
            'gender', 'location', 'time_zone', 'occupation', 'terms_privacy_accepted',
            'bank_name', 'account_number', 'ifsc', 'branch',
            'nominee_name', 'nominee_relationship', 'nominee_age', 'nominee_address',
            'nominee_city', 'nominee_pincode', 'nominee_mobile_number', 'nominee_email',
            'nominee_declaration_accepted',
        ]
        # mobile_number is the USERNAME_FIELD, so it's controlled by the authentication flow.
        # It's read-only in the profile update, as it's the primary key for the user.
        read_only_fields = ['id', 'mobile_number']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get('request')

        # Apply dynamic field filtering ONLY for non-staff users on write operations
        if request and not request.user.is_staff and request.method in ['POST', 'PUT', 'PATCH']:
            try:
                settings = UserProfileSettings.objects.first()
                if settings:
                    # Get editable fields from settings and combine with always read-only fields
                    allowed_fields_for_user = set(settings.editable_fields)
                    allowed_fields_for_user.update(self.Meta.read_only_fields)
                else:
                    # If no settings exist, default to only read-only fields for user updates
                    allowed_fields_for_user = set(self.Meta.read_only_fields)

            except UserProfileSettings.DoesNotExist:
                # If UserProfileSettings model doesn't exist or no instance, assume no fields are editable by user
                allowed_fields_for_user = set(self.Meta.read_only_fields)
            
            # Remove fields that are not in the allowed list for non-admin users
            # when they are attempting to update their profile.
            for field_name in list(self.fields.keys()):
                if field_name not in allowed_fields_for_user:
                    self.fields.pop(field_name)

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

    def validate_terms_privacy_accepted(self, value):
        if not value:
            raise serializers.ValidationError("You must accept the terms of use and privacy policy.")
        return value

    def validate_nominee_declaration_accepted(self, value):
        if not value:
            raise serializers.ValidationError("You must accept the nominee declaration.")
        return value

    def create(self, validated_data):
        # As per your comment, this serializer's 'create' is not for new user creation.
        # This will only be called if a POST request is made to the UserProfileView
        # and it attempts to create a new instance, which is handled by your view's post method
        # for initial profile completion.
        # Ensure that if 'name' is the placeholder being updated, it's included in validated_data.
        # The instance here is expected to be request.user.
        instance = self.instance # Get the user instance from self.instance (passed via instance=request.user)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        # This is for PUT/PATCH operations
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

