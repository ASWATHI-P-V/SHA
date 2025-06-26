# SHA_GROUP/sha/utils.py
import random
import phonenumbers
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework import status

def api_response(success, message, data=None, status_code=status.HTTP_200_OK):
    return Response({
        "success": success,
        "message": message,
        "data": data
    }, status=status_code)


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
