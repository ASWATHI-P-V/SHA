# SHA_GROUP/sha/admin.py

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import UserProfileSettings

User = get_user_model()



@admin.register(UserProfileSettings)
class UserProfileSettingsAdmin(admin.ModelAdmin):
    list_display = ('editable_fields',)
    def has_add_permission(self, request):
        return not UserProfileSettings.objects.exists()

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # For creating a new user through the admin interface
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            # Mobile number is the USERNAME_FIELD, prompted first.
            # Name is in REQUIRED_FIELDS, so it will be prompted next.
            'fields': ('mobile_number', 'name', 'email', 'password'),
        }),
    )

    # For viewing/editing existing users in the admin interface
    fieldsets = (
        # Mobile number is now the primary identifier displayed first
        (None, {'fields': ('mobile_number', 'name', 'email', 'password')}),
        ('Profile Information', {
            'fields': (
                'profile_picture', 'date_of_birth', 'guardian_name', 'address',
                'city', 'pincode', 'father_husband_name', 'gender', 'location',
                'time_zone', 'occupation', 'terms_privacy_accepted',
            ),
        }),
        ('Bank Details', {
            'fields': (
                'bank_name', 'account_number', 'ifsc', 'branch',
            ),
        }),
        ('Nominee Details', {
            'fields': (
                'nominee_name', 'nominee_relationship', 'nominee_age',
                'nominee_address', 'nominee_city', 'nominee_pincode',
                'nominee_mobile_number', 'nominee_email', 'nominee_declaration_accepted',
            ),
        }),
        ('Proof Documents', {
            'fields': (
                'proof_of_identity_type', 'proof_of_identity_document',
                'proof_of_address_type', 'proof_of_address_document',
            ),
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('OTP Info', {'fields': ('otp', 'otp_created_at')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    # list_display now prioritizes mobile_number for identification
    list_display = (
        'mobile_number', 'name', 'email', 'occupation',
        'nominee_name', 'nominee_relationship',
        'is_active', 'is_staff', 'date_joined'
    )
    # list_filter and search_fields updated
    list_filter = ('occupation', 'nominee_relationship', 'is_active', 'is_staff', 'is_superuser', 'gender')
    search_fields = ('mobile_number', 'name', 'email', 'account_number', 'nominee_name', 'nominee_mobile_number')
    readonly_fields = ('last_login', 'date_joined', 'otp_created_at')
    ordering = ('-date_joined',)
