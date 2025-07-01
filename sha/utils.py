# SHA_GROUP/sha/utils.py
import random
import phonenumbers
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError, NotAuthenticated, PermissionDenied, NotFound

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


def api_response(success, message=None, data=None, status_code=status.HTTP_200_OK, headers=None):
    """
    Generates a consistent API response.
    If it's a 400 Bad Request due to validation errors, it sets the 'message'
    to the specific error and sets 'data' to null.
    The headers argument will be passed directly to rest_framework.response.Response.
    """
    response_data = {}
    response_data["success"] = success

    # Handle validation errors specifically for 400 status codes
    if not success and status_code == status.HTTP_400_BAD_REQUEST and isinstance(data, dict):
        response_data["message"] = _extract_single_error_message(data)
        response_data["data"] = None
    else:
        response_data["message"] = message if message is not None else ("Operation successful." if success else "An error occurred.")
        response_data["data"] = data

    # ----------------------------------------------------------------------------------
    # CHANGE THIS LINE: Pass headers to the Response constructor
    # ----------------------------------------------------------------------------------
    return Response(response_data, status=status_code, headers=headers)


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

def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    # Use your existing api_response for consistent formatting
    if response is not None:
        # Check for specific DRF exception types and customize messages
        if isinstance(exc, NotFound):
            error_message = "The requested resource could not be found."
            if "No InvestmentServiceGroup matches" in exc.detail:
                error_message = "Investment Service Group not found."
            elif "No InterestRateSetting matches" in exc.detail:
                error_message = "Interest Rate Setting not found."
            elif "No Investor matches" in exc.detail:
                error_message = "Investor profile not found."
            # Explicitly pass data=None for 404s
            return api_response(False, error_message, data=None, status_code=status.HTTP_404_NOT_FOUND)

        elif isinstance(exc, NotAuthenticated):
            # Explicitly pass data=None for 401s
            return api_response(False, "Authentication required. Please log in to access this resource.", data=None, status_code=status.HTTP_401_UNAUTHORIZED)

        elif isinstance(exc, PermissionDenied):
            # Explicitly pass data=None for 403s
            return api_response(False, "You do not have permission to perform this action.", data=None, status_code=status.HTTP_403_FORBIDDEN)

        elif isinstance(exc, ValidationError):
            # For validation errors (400), your api_response function
            # already handles setting 'data' to null if it's a dict and success is false.
            # So, we pass exc.detail as data, and api_response will process it.
            return api_response(False, None, data=exc.detail, status_code=status.HTTP_400_BAD_REQUEST)

        # For any other DRF exception not explicitly handled above,
        # we want data to be null as well, unless it's a specific case.
        # The 'detail' message from DRF's default response is typically sufficient for the message.
        default_message = response.data.get('detail', 'An unexpected error occurred.')
        return api_response(False, default_message, data=None, status_code=response.status_code)

    # If the default DRF exception handler returns None, it means it's not a DRF exception
    # (e.g., a raw Django Http404, or a custom exception not registered with DRF).
    # You could log it, re-raise, or return a generic 500 error here.
    # For now, we'll just return None, letting Django handle it.
    return None

