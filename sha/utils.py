# SHA_GROUP/sha/utils.py
import random
import phonenumbers
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework import status

def _extract_single_error_message(errors_dict):
    """
    Extracts a single, human-readable error message from a DRF serializer errors dictionary.
    Prioritizes non_field_errors, then the first field's error.
    """
    if not isinstance(errors_dict, dict):
        return str(errors_dict) # In case of a simple string/list error

    # Prioritize non_field_errors if they exist
    if 'non_field_errors' in errors_dict and isinstance(errors_dict['non_field_errors'], list) and errors_dict['non_field_errors']:
        return str(errors_dict['non_field_errors'][0])

    # Iterate through fields to find the first error
    for field, errors in errors_dict.items():
        if isinstance(errors, list) and errors:
            # Format field name for clarity (e.g., 'mobile_number' -> 'Mobile number')
            # Removed the field_name_pretty prefix. Now it just returns the error message itself.
            return str(errors[0])
        elif isinstance(errors, dict):
            # Recursively try to find an error in nested dictionaries (though for simple cases, direct fields are often enough)
            nested_error = _extract_single_error_message(errors)
            if nested_error:
                return nested_error
    return "An unknown validation error occurred." # Fallback


def api_response(success, message=None, data=None, status_code=status.HTTP_200_OK):
    """
    Generates a consistent API response.
    If it's a 400 Bad Request due to validation errors, it sets the 'message'
    to the specific error and sets 'data' to null.
    """
    response_data = {}
    response_data["success"] = success

    # Handle validation errors specifically for 400 status codes
    if not success and status_code == status.HTTP_400_BAD_REQUEST and isinstance(data, dict):
        # Extract a single, specific message for validation errors
        response_data["message"] = _extract_single_error_message(data)
        response_data["data"] = None # Set data to null for validation errors
    else:
        # For other errors or success responses, use provided message/data
        response_data["message"] = message if message is not None else ("Operation successful." if success else "An error occurred.")
        response_data["data"] = data

    return Response(response_data, status=status_code)


def generate_otp():
    return str(random.randint(1000, 9999))


def validate_phone_number(phone):
    if not phone.startswith('+'):
        raise ValidationError("Phone number must start with '+' and country code, e.g. +919876543210")
    try:
        phone_obj = phonenumbers.parse(phone, None)
    except phonenumbers.NumberParseException:
        raise ValidationError("Invalid phone number format")

    if not phonenumbers.is_valid_number(phone_obj):
        raise ValidationError("Invalid phone number")

    return phonenumbers.format_number(phone_obj, phonenumbers.PhoneNumberFormat.E164)


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token)
    }

