# SHA_GROUP/investors/admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Investor, InterestRateSetting, InvestmentServiceGroup
from django.contrib.auth import get_user_model

User = get_user_model()

# Register InvestmentServiceGroup
@admin.register(InvestmentServiceGroup)
class InvestmentServiceGroupAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name',)

# Register InterestRateSetting
@admin.register(InterestRateSetting)
class InterestRateSettingAdmin(admin.ModelAdmin):
    # NEW: Include service_group in list display and fieldsets
    list_display = ('id','service_group', 'period_in_years', 'interest_percentage', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'service_group',) # Filter by service group
    search_fields = ('service_group__name', 'period_in_years',) # Search by group name
    ordering = ('service_group__name', 'period_in_years',)
    # NEW: Ensure service_group is in fieldsets
    fieldsets = (
        (None, {'fields': ('service_group', 'period_in_years', 'interest_percentage', 'is_active')}),
    )


# Custom Admin for Investor
@admin.register(Investor)
class InvestorAdmin(admin.ModelAdmin):
    list_display = (
        'id','user_display_name', 'user_mobile_number', 'selected_service_group', # NEW: Display selected group
        'number_of_shares',
        'invested_amount', 'profit', 'total_portfolio_value', 'investment_period',
        'interest_rate_applied', 'final_return_amount',
        'investment_start_date', 'investment_end_date', 'is_investment_active'
    )
    list_filter = (
        'is_investment_active', 'investment_period', 'selected_service_group' # NEW: Filter by selected group
    )
    search_fields = (
        'user__name', 'user__mobile_number', 'user__email', 'invested_amount',
        'selected_service_group__name' # NEW: Search by selected group name
    )
    raw_id_fields = ('user',) # Keep user as raw_id for performance
    # NEW: Add selected_service_group to raw_id_fields if you anticipate many groups
    # raw_id_fields = ('user', 'selected_service_group',)

    fieldsets = (
        (_('Investor Link'), {
            'fields': ('user',)
        }),
        (_('Investment Input Details'), { # Renamed for clarity
            'fields': (
                'selected_service_group',
                'number_of_shares',    # This is the field for admin input now
                'investment_period',
                'is_investment_active',
            ),
            'description': _("Enter the user, service group, number of shares, investment period, and active status. Other values will be calculated automatically upon saving.")
        }),
        (_('Calculated & Auto-Generated Values'), { # New fieldset for calculated fields
            'fields': (
                'invested_amount',
                'interest_rate_applied',
                'final_return_amount',
                'profit',
                'total_portfolio_value',
                'investment_start_date',
                'investment_end_date',
                'uuid',
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',), # Makes this section collapsible in the admin
        }),
    )

    readonly_fields = (
        # Mark all calculated and auto-generated fields as read-only
        'invested_amount',
        'interest_rate_applied',
        'final_return_amount',
        'profit',
        'total_portfolio_value',
        'investment_start_date',
        'investment_end_date',
        'uuid',
        'created_at',
        'updated_at'
        
    )

    def user_display_name(self, obj):
        return obj.user.get_full_name() if obj.user else '-'
    user_display_name.short_description = _("User Name")
    user_display_name.admin_order_field = 'user__name'

    def user_mobile_number(self, obj):
        return obj.user.mobile_number if obj.user else '-'
    user_mobile_number.short_description = _("Mobile Number")
    user_mobile_number.admin_order_field = 'user__mobile_number'