# SHA_GROUP/sha/models.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from django.contrib.auth.base_user import BaseUserManager
import pytz
from django.db.models import JSONField # Import JSONField for MySQL compatibility

TIMEZONE_CHOICES = [(tz, tz) for tz in pytz.common_timezones]



class UserProfileSettings(models.Model):
    """
    Stores settings related to user profile editing.
    There should ideally be only one instance of this model.
    """
    # Use JSONField for storing a list of strings in MySQL
    editable_fields = JSONField(
        default=list, # Store as an empty list by default
        blank=True,
        help_text="A JSON list of profile field names that users can update. Example: [\"bio\", \"website\"]"
    )
    # You could add other settings here in the future

    class Meta:
        verbose_name_plural = "User Profile Settings"

    def __str__(self):
        return "User Profile Editable Fields Settings"

    # Ensure only one instance exists
    def save(self, *args, **kwargs):
        if not self.pk and UserProfileSettings.objects.exists():
            # If you want to strictly enforce one instance:
            # raise ValidationError('There can be only one UserProfileSettings instance.')
            # Or, just update the existing one if trying to create a second:
            existing_settings = UserProfileSettings.objects.first()
            if existing_settings:
                self.pk = existing_settings.pk
        super().save(*args, **kwargs)


class UserManager(BaseUserManager):
    """
    Custom user manager where 'mobile_number' is the USERNAME_FIELD.
    This manager is adapted for AbstractBaseUser.
    """
    def create_user(self, mobile_number, name=None, password=None, **extra_fields):
        if not mobile_number:
            raise ValueError('The Mobile Number field must be set as it is the username.')

        # Ensure name is not None if it's required for createsuperuser later
        # For regular users, name can be set to an empty string initially if not provided.
        if name is None:
            name = "" # Set default to empty string if not provided for regular user creation

        user = self.model(mobile_number=mobile_number, name=name, **extra_fields)
        user.set_password(password or '') # Hash the password
        user.save(using=self._db)
        return user

    def create_superuser(self, mobile_number, name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        # Call create_user with mobile_number as the primary argument
        return self.create_user(mobile_number, name, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    # 'mobile_number' is now the unique identifier for login.
    mobile_number = models.CharField(
        max_length=20, unique=True,
        help_text="Mobile number for OTP authentication and primary login identifier (username).",
        null=True, blank=True
    )

    # 'name' is now a display name, no longer unique.
    # It can be blank initially and filled later.
    name = models.CharField(max_length=100, unique=False, null=True, blank=True,
                            help_text="User's display name.")

    email = models.EmailField(unique=True, null=True, blank=True,
                              help_text="Optional: User's email address.")

    otp = models.CharField(max_length=6, null=True, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)

    # PROFILE FIELDS
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

    location = models.CharField(max_length=255, null=True, blank=True)
    time_zone = models.CharField(max_length=100, choices=TIMEZONE_CHOICES, null=True, blank=True)

    # Occupation Choices
    OCCUPATION_CHOICES = [
        ('service', 'Service'),
        ('business', 'Business'),
        ('private_sector', 'Private Sector'),
        ('govt_central_state', 'Central/State Government'),
        ('pensioner', 'Pensioner'),
        ('senior_citizen', 'Senior Citizen'),
        ('minor', 'Minor'),
        ('other', 'Other'),
    ]
    occupation = models.CharField(max_length=50, choices=OCCUPATION_CHOICES, null=True, blank=True)

    # Bank Details Fields
    bank_name = models.CharField(max_length=255, null=True, blank=True)
    account_number = models.CharField(max_length=50, unique=False, null=True, blank=True)
    ifsc = models.CharField(max_length=20, null=True, blank=True)
    branch = models.CharField(max_length=255, null=True, blank=True)

    # Nominee Details Fields
    nominee_name = models.CharField(max_length=255, null=True, blank=True)
    nominee_relationship = models.CharField(max_length=50, null=True, blank=True)
    nominee_age = models.PositiveSmallIntegerField(null=True, blank=True)
    nominee_address = models.TextField(null=True, blank=True)
    nominee_city = models.CharField(max_length=100, null=True, blank=True)
    nominee_pincode = models.CharField(max_length=10, null=True, blank=True)
    nominee_mobile_number = models.CharField(max_length=20, null=True, blank=True)
    nominee_email = models.EmailField(null=True, blank=True)
    nominee_declaration_accepted = models.BooleanField(default=False,
                                                       help_text="Declaration that nominee details are correct.")

    terms_privacy_accepted = models.BooleanField(default=False,
                                                 help_text="Indicates if the user has accepted terms of use and privacy policy.")

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    groups = models.ManyToManyField(
        'auth.Group', verbose_name=('groups'), blank=True,
        help_text=('The groups this user belongs to. A user will get all permissions '
                   'granted to each of their groups.'),
        related_name="sha_user_groups", related_query_name="sha_user_group",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission', verbose_name=('user permissions'), blank=True,
        help_text=('Specific permissions for this user.'),
        related_name="sha_user_permissions", related_query_name="sha_user_permission",
    )

    objects = UserManager()

    USERNAME_FIELD = 'mobile_number' # <-- PRIMARY CHANGE: mobile_number is now the username
    REQUIRED_FIELDS = ['name'] # <-- REQUIRED FOR `createsuperuser` if not nullable
                               #     If `name` can be entirely optional, this can be empty []

    def is_otp_valid(self, otp_input, expiry_seconds=300):
        if self.otp is None or self.otp != otp_input or not self.otp_created_at:
            return False
        return (timezone.now() - self.otp_created_at).total_seconds() <= expiry_seconds

    def __str__(self):
        """
        String representation of the user, prioritizing mobile_number (as it's the username).
        """
        if self.mobile_number:
            return self.mobile_number
        if self.name: # Fallback to name if mobile_number is somehow missing
            return self.name
        return f"User ID: {self.id}"

    def get_full_name(self):
        return self.name if self.name else self.mobile_number

    def get_short_name(self):
        return self.name if self.name else self.mobile_number
