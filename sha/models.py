# SHA_GROUP/sha/models.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin # Use AbstractBaseUser for full control
from django.utils import timezone
from django.contrib.auth.base_user import BaseUserManager
import pytz

TIMEZONE_CHOICES = [(tz, tz) for tz in pytz.common_timezones]

class UserManager(BaseUserManager):
    """
    Custom user manager where 'name' is the USERNAME_FIELD.
    This manager is adapted for AbstractBaseUser.
    """
    def create_user(self, name, mobile_number, password=None, **extra_fields):
        if not name:
            raise ValueError('The Name field must be set as it is the username.')
        if not mobile_number:
            raise ValueError('The Mobile Number field must be set.')

        user = self.model(name=name, mobile_number=mobile_number, **extra_fields)
        user.set_password(password or '') # Hash the password
        user.save(using=self._db)
        return user

    def create_superuser(self, name, mobile_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(name, mobile_number, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    # 'name' is now the unique identifier for login.
    # It must be unique, not null, not blank.
    name = models.CharField(max_length=100, unique=True,
                            help_text="User's unique name, used as the primary login identifier (username).")

    # Mobile number is for OTP, not the primary login field (username)
    mobile_number = models.CharField(max_length=20, unique=True, null=True, blank=True,
                                     help_text="Mobile number for OTP authentication.")
    email = models.EmailField(unique=True, null=True, blank=True,
                              help_text="Optional: User's email address.")


   
    otp = models.CharField(max_length=6, null=True, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)

    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    guardian_name = models.CharField(max_length=255, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    pincode = models.CharField(max_length=10, null=True, blank=True)
    father_husband_name = models.CharField(max_length=255, null=True, blank=True)

    PROOF_CHOICES = [
        ('passport', 'Passport'),
        ('emirates_id', 'Emirates ID'),
        ('other', 'Other Document')
    ]
    proof_of_identity_type = models.CharField(max_length=20, choices=PROOF_CHOICES, null=True, blank=True)
    proof_of_identity_document = models.FileField(upload_to='identity_proofs/', null=True, blank=True)
    proof_of_address_type = models.CharField(max_length=20, choices=PROOF_CHOICES, null=True, blank=True)
    proof_of_address_document = models.FileField(upload_to='address_proofs/', null=True, blank=True)

    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ]
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)

    location = models.CharField(max_length=255, null=True, blank=True) # Could be a specific location model later
    time_zone = models.CharField(max_length=100, choices=TIMEZONE_CHOICES, null=True, blank=True)

    terms_privacy_accepted = models.BooleanField(default=False,
                                                 help_text="Indicates if the user has accepted terms of use and privacy policy.")



    # Required fields for AbstractBaseUser and PermissionsMixin
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    # Fix for the SystemCheckError: Add related_name to avoid clashes
    # These are needed when inheriting from PermissionsMixin
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=('groups'),
        blank=True,
        help_text=(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name="sha_user_groups", # Unique related_name
        related_query_name="sha_user_group",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=('user permissions'),
        blank=True,
        help_text=('Specific permissions for this user.'),
        related_name="sha_user_permissions", # Unique related_name
        related_query_name="sha_user_permission",
    )

    # Set the custom manager
    objects = UserManager()

    # Define the field used for authentication (login)
    USERNAME_FIELD = 'name'
    # REQUIRED_FIELDS are prompted when creating a superuser via `createsuperuser`.
    # 'name' is already prompted as USERNAME_FIELD.
    # We require 'mobile_number' for superusers.
    REQUIRED_FIELDS = ['mobile_number']

    def is_otp_valid(self, otp_input, expiry_seconds=300):
        """
        Checks if the provided OTP matches the stored one and is within the expiry time.
        """
        if self.otp is None or self.otp != otp_input or not self.otp_created_at:
            return False
        return (timezone.now() - self.otp_created_at).total_seconds() <= expiry_seconds

    def __str__(self):
        """
        String representation of the user, prioritizing name (as it's the username).
        """
        if self.name:
            return self.name
        if self.mobile_number:
            return f"Mobile: {self.mobile_number}"
        return f"User ID: {self.id}" # Fallback
    
    # Required for PermissionsMixin
    def get_full_name(self):
        return self.name

    def get_short_name(self):
        return self.name

# name
# email
# profile_picture
# date_of_birth
# guardian's_name
# address
# city
# pincode
# father/husband_name
# proof_of_identity(passport,emirates id)
# proof_of_address(passport,emirates id)
# proof_of_address_document(file import ,accepts: pdf,doc ,docx,jpg,jpeg,png)
# gender(drop down:male.female,others)
# location
# TIME_ZONE(drop down)
# user_role(drop down: customer,agent)
# a terms of use and privacy policy checklist(bloolean field)

# pagination

# scheme details:
# Category Of The Applicant (drop down:individual,trust,nri,other)
# a text box under the category of the applicant which accept the other category
# Occupation:(drop down has:
# Service
# Business 
# Private sec
# Central/state government 
# Pensioner
# Senior citizen
# Minor
# Other)
# has a text box under the occupation which accepts the other occupation

# bank details:
# name
# bank_name
# Account Number:
# IFSC Code:
# Branch Name:
# mode of payment(radio button: account payee, cheque, bank transfer)

# Nominee Details:
# Nominee _Name
# Relationship with Investor
# Nominee Age
# Nominee Address
# Nominee City
# Nominee Pincode
# Nominee Mobile Number
# Nominee Email
# a declaration checkbox(ass BooleanField)