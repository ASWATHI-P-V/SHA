# SHA_GROUP/investors/models.py
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import uuid
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

User = settings.AUTH_USER_MODEL
# MARK: Investment Service Group Model
class InvestmentServiceGroup(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name=_("Service Group Name"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Description"))
    share_value = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('100.00'),
        verbose_name=_("Share Value (AED per share)"),
        help_text=_("The value of one share in this service group (e.g., 100.00 AED).")
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Investment Service Group")
        verbose_name_plural = _("Investment Service Groups")
        ordering = ['name']

    def __str__(self):
        return self.name

#MARK: Interest Rate Setting Model
class InterestRateSetting(models.Model):
    #
    service_group = models.ForeignKey(
        InvestmentServiceGroup,
        on_delete=models.CASCADE,
        related_name='interest_settings',
        verbose_name=_("Associated Service Group")
    )
    period_in_years = models.PositiveIntegerField(verbose_name=_("Investment Period (Years)"))
    interest_percentage = models.DecimalField(max_digits=5, decimal_places=2, verbose_name=_("Interest Percentage (%)"))
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Interest Rate Setting")
        verbose_name_plural = _("Interest Rate Settings")
        # Ensure that for a given service group, a period_in_years is unique
        unique_together = ('service_group', 'period_in_years')
        ordering = ['service_group__name', 'period_in_years']

    def __str__(self):
        return f"{self.service_group.name} - {self.period_in_years} Years - {self.interest_percentage}%"

#MARK: Investor Model
class Investor(models.Model):
    user = models.ForeignKey( 
        User,
        on_delete=models.CASCADE,
        related_name='investments', 
        verbose_name=_("Associated User")
    )
    # NEW: Foreign key to the InvestmentServiceGroup the user invested in
    selected_service_group = models.ForeignKey(
        InvestmentServiceGroup,
        on_delete=models.SET_NULL, # If the group is deleted, don't delete investor record
        null=True, blank=True, # Allow for null if group is deleted or not initially set
        related_name='investments_in_group',
        verbose_name=_("Selected Service Group for Investment")
    )
    number_of_shares = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('0.00'),
        verbose_name=_("Number of Shares"),
        help_text=_("The total number of shares purchased for this investment.")
    )
    invested_amount = models.DecimalField(
        max_digits=15, decimal_places=2,
        verbose_name=_("Invested Amount (AED)")
    )
    investment_period = models.PositiveIntegerField(
        choices=[(3, '3 Years'), (5, '5 Years'), (10, '10 Years')],
        verbose_name=_("Investment Period")
    )
    interest_rate_applied = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        verbose_name=_("Interest Rate Applied (%)"),
        help_text=_("The interest rate applied at the time of investment.")
    )
    final_return_amount = models.DecimalField(
        max_digits=15, decimal_places=2,
        null=True, blank=True,
        verbose_name=_("Final Return Amount (AED)"),
        help_text=_("Calculated based on invested amount and interest rate (Principal + Profit).")
    )
    profit = models.DecimalField(
        max_digits=15, decimal_places=2,
        null=True, blank=True,
        verbose_name=_("Profit (AED)"),
        help_text=_("The calculated profit from the investment (Final Return - Invested Amount).")
    )
    total_portfolio_value = models.DecimalField(
        max_digits=15, decimal_places=2,
        null=True, blank=True,
        verbose_name=_("Total Portfolio Value (AED)"),
        help_text=_("Sum of invested amount and profit.")
    )
    investment_start_date = models.DateField(
        auto_now_add=True, # This sets the date automatically on creation
        verbose_name=_("Investment Start Date")
    )
    investment_end_date = models.DateField(
        null=True, blank=True,
        verbose_name=_("Investment End Date"),
        help_text=_("Calculated based on start date and period.")
    )
    is_investment_active = models.BooleanField(
        default=True,
        verbose_name=_("Is Investment Active")
    )
    # The original ManyToMany 'service_groups' field is removed or repurposed if needed.
    # For a specific investment, 'selected_service_group' is more appropriate.
    # If you still need a general M2M for an investor (not tied to a specific investment), you can add it back with a different name.
    # For now, I'm removing it to keep the model focused on the specific investment.

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Investment") # Changed for clarity, as each instance is an investment
        verbose_name_plural = _("Investments") # Changed for clarity
        ordering = ['user__mobile_number', 'created_at'] # Assuming mobile_number is primary, adjust if 'name' is preferred for ordering
        # Ensure a user cannot have two identical investments (same group, same period).
        unique_together = ('user', 'selected_service_group', 'investment_period')

# MARK: Investor Model Save Method
    def save(self, *args, **kwargs):
        # 1. Calculate invested_amount based on number_of_shares and group's share_value
        # This needs to happen BEFORE the main calculation block.
        if self.number_of_shares is not None and self.number_of_shares > 0 and self.selected_service_group_id:
            try:
                # Retrieve the service group to get its current share_value
                service_group = InvestmentServiceGroup.objects.get(id=self.selected_service_group_id)
                self.invested_amount = (self.number_of_shares * service_group.share_value).quantize(Decimal('0.01'))
            except InvestmentServiceGroup.DoesNotExist:
                # If the service group doesn't exist (e.g., due to race condition or invalid ID)
                self.invested_amount = Decimal('0.00') # Default to 0
                print(f"--- WARNING: Selected Service Group (ID: {self.selected_service_group_id}) not found for investment amount calculation. ---")
            except Exception as e:
                self.invested_amount = Decimal('0.00')
                print(f"--- ERROR calculating invested_amount: {e} ---")
        else:
            self.invested_amount = Decimal('0.00') # Default to 0 if shares/group are missing or shares <= 0

        # 2. Main calculation block for interest, profit, return, and end date
        # This block now relies on the calculated self.invested_amount
        if self.invested_amount > 0 and \
           self.investment_period is not None and \
           self.selected_service_group is not None:

            

            try:
                # Find the interest rate specific to the selected group and period
                interest_setting = InterestRateSetting.objects.get(
                    service_group=self.selected_service_group,
                    period_in_years=self.investment_period,
                    is_active=True
                )

                self.interest_rate_applied = interest_setting.interest_percentage

                # Convert percentage to a decimal for calculation (e.g., 5.00% -> 0.05)
                rate_decimal = self.interest_rate_applied / Decimal('100.00')

                # Simple interest calculation: A = P(1 + RT)
                self.final_return_amount = self.invested_amount * (Decimal('1.00') + (rate_decimal * self.investment_period))
                self.final_return_amount = self.final_return_amount.quantize(Decimal('0.01'))

                self.profit = self.final_return_amount - self.invested_amount
                self.profit = self.profit.quantize(Decimal('0.01'))

                # total_portfolio_value for this specific investment is its final return
                # This field generally makes more sense as a summary across investments,
                # but if it's meant to reflect the final return of *this* investment, then this is correct.
                self.total_portfolio_value = self.final_return_amount

                # Calculate end date based on investment_start_date (auto_now_add)
                if self.investment_start_date:
                    # Using 365.25 for a slightly more accurate year, accounting for leap years
                    self.investment_end_date = self.investment_start_date + timedelta(days=int(self.investment_period * 365.25))
                else:
                    # Fallback if investment_start_date somehow isn't set (unlikely with auto_now_add)
                    self.investment_start_date = timezone.now().date()
                    self.investment_end_date = self.investment_start_date + timedelta(days=int(self.investment_period * 365.25))

               

            except InterestRateSetting.DoesNotExist:
                
                self.final_return_amount = self.invested_amount
                self.profit = Decimal('0.00')
                self.total_portfolio_value = self.invested_amount
                self.interest_rate_applied = Decimal('0.00')
                self.investment_end_date = None
            except Exception as e:
               
                self.final_return_amount = self.invested_amount
                self.profit = Decimal('0.00')
                self.total_portfolio_value = self.invested_amount
                self.interest_rate_applied = Decimal('0.00')
                self.investment_end_date = None
        else:
            # print("--- Investor.save() Conditions for main calculation NOT met. Defaulting fields. ---") # For debugging
            
            self.final_return_amount = self.invested_amount if self.invested_amount is not None else Decimal('0.00')
            self.profit = Decimal('0.00')
            self.total_portfolio_value = self.invested_amount if self.invested_amount is not None else Decimal('0.00')
            self.interest_rate_applied = Decimal('0.00')
            self.investment_end_date = None

        super().save(*args, **kwargs)
        # print("--- Investor.save() Calculations End ---") # For debugging

    def __str__(self):
        user_info = self.user.get_full_name() if hasattr(self.user, 'get_full_name') and self.user.get_full_name() else self.user.mobile_number # Use mobile_number as fallback from your User model
        group_info = self.selected_service_group.name if self.selected_service_group else "No Group"
        return f"Investment by {user_info} in {group_info} ({self.investment_period}Y) - {self.number_of_shares} Shares"