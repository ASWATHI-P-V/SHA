# SHA_GROUP/sha/admin.py

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

User = get_user_model()

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Customize the add_fieldsets for creating a new user through the admin,
    # as the default BaseUserAdmin's add_fieldsets expect a 'username' field.
    # We are explicitly defining it based on our model's REQUIRED_FIELDS.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('name', 'mobile_number', 'email', 'password'),
        }),
    )

    # Use fieldsets for viewing/editing existing users in the admin interface.
    fieldsets = (
        (None, {'fields': ('name', 'mobile_number', 'email', 'password')}),
        ('Profile Information', {
            'fields': (
                'profile_picture', 'date_of_birth', 'guardian_name', 'address',
                'city', 'pincode', 'father_husband_name', 'gender', 'location',
                'time_zone', 'terms_privacy_accepted',
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

    list_display = ('name', 'mobile_number', 'email', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'gender')
    search_fields = ('name', 'email', 'mobile_number')
    readonly_fields = ('last_login', 'date_joined', 'otp_created_at')
    ordering = ('-date_joined',)
