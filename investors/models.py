import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db.models.signals import pre_save # Import pre_save
from django.dispatch import receiver # Import receiver
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from django.utils.translation import gettext_lazy as _

# Assuming User, InvestmentServiceGroup, and InterestRateSetting models are defined as before

# Example placeholder for your User model, adjust as per your actual setup
# from django.contrib.auth import get_user_model
# User = get_user_model()


class InvestmentServiceGroup(models.Model):
    name = models.CharField(max_length=255, unique=True)
    share_value = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.01'))])
    description = models.TextField(blank=True, null=True, verbose_name=_("Description"))
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class InterestRateSetting(models.Model):
    service_group = models.ForeignKey(InvestmentServiceGroup, on_delete=models.CASCADE, related_name='interest_rates')
    period_in_years = models.PositiveIntegerField(choices=[(3, '3 Years'), (5, '5 Years'), (10, '10 Years')], unique=False)
    interest_percentage = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    is_active = models.BooleanField(default=True) # Added for better control
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('service_group', 'period_in_years')
        ordering = ['service_group__name', 'period_in_years']

    def __str__(self):
        return f"{self.service_group.name} - {self.period_in_years} Years: {self.interest_percentage}%"


class Investor(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, # Use settings.AUTH_USER_MODEL for custom User
        on_delete=models.CASCADE,
        related_name='investments',
        verbose_name=_("Associated User")
    )
    selected_service_group = models.ForeignKey(
        InvestmentServiceGroup,
        on_delete=models.SET_NULL,
        null=True, blank=True,
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
        default=Decimal('0.00'), # Add default for consistency
        verbose_name=_("Invested Amount (AED)")
    )
    investment_period = models.PositiveIntegerField(
        choices=[(3, '3 Years'), (5, '5 Years'), (10, '10 Years')],
        verbose_name=_("Investment Period")
    )
    interest_rate_applied = models.DecimalField(
        max_digits=7, decimal_places=4, # Changed to 4 decimal places for precision
        default=Decimal('0.0000'), # Default to 0.0000
        verbose_name=_("Interest Rate Applied (%)"),
        help_text=_("The interest rate applied at the time of investment.")
    )
    final_return_amount = models.DecimalField(
        max_digits=15, decimal_places=2,
        default=Decimal('0.00'), # Default to 0.00
        verbose_name=_("Final Return Amount (AED)"),
        help_text=_("Calculated based on invested amount and interest rate (Principal + Profit).")
    )
    profit = models.DecimalField(
        max_digits=15, decimal_places=2,
        default=Decimal('0.00'), # Default to 0.00
        verbose_name=_("Profit (AED)"),
        help_text=_("The calculated *projected* profit from the investment at full maturity (Final Return - Invested Amount).")
    )
    total_portfolio_value = models.DecimalField(
        max_digits=15, decimal_places=2,
        default=Decimal('0.00'), # Default to 0.00
        verbose_name=_("Total Portfolio Value (AED)"),
        help_text=_("Current value of the portfolio (Invested Amount + Current Accrued Profit).")
    )
    current_accrued_profit = models.DecimalField(
        max_digits=15, # Changed from 18 to 15 to match other fields, but 18 is fine too
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_("Current Accrued Profit (AED)"), # Added verbose_name
        help_text=_("Profit earned from the investment up to the current date.")
    )
    investment_start_date = models.DateField(
        auto_now_add=True,
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
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Investment")
        verbose_name_plural = _("Investments")
        ordering = ['user__id', 'created_at'] # Ordering by user ID is safer than mobile_number if not unique
        unique_together = ('user', 'selected_service_group', 'investment_period')

    def __str__(self):
        user_info = self.user.get_full_name() if hasattr(self.user, 'get_full_name') and self.user.get_full_name() else str(self.user)
        group_info = self.selected_service_group.name if self.selected_service_group else "No Group"
        return f"Investment by {user_info} in {group_info} ({self.investment_period}Y) - {self.number_of_shares} Shares"

    # MARK: Calculation Method
    def calculate_derived_fields(self):
        # 1. Recalculate invested_amount (Principal) based on current shares and group share_value
        share_value = self.selected_service_group.share_value if self.selected_service_group else Decimal('0.00')
        self.invested_amount = (self.number_of_shares * share_value).quantize(Decimal('0.01'))

        # Initialize all derived fields to default values before calculation
        self.interest_rate_applied = Decimal('0.0000')
        self.final_return_amount = self.invested_amount
        self.profit = Decimal('0.00') # This is the *projected* profit at maturity
        self.current_accrued_profit = Decimal('0.00') # NEW FIELD: Profit earned up to the current date
        self.total_portfolio_value = self.invested_amount # NEW: Current total portfolio value (principal + accrued)
        self.investment_end_date = None

        if self.invested_amount > 0 and \
           self.investment_period is not None and \
           self.selected_service_group:
            try:
                interest_setting = InterestRateSetting.objects.get(
                    service_group=self.selected_service_group,
                    period_in_years=self.investment_period,
                    is_active=True # Ensure only active rate settings are used
                )
                self.interest_rate_applied = interest_setting.interest_percentage

                rate_decimal = self.interest_rate_applied / Decimal('100.00')

                # Calculate projected final return (Simple Interest: A = P(1 + RT))
                self.final_return_amount = self.invested_amount * (Decimal('1.00') + (rate_decimal * self.investment_period))
                self.final_return_amount = self.final_return_amount.quantize(Decimal('0.01'))

                # Projected profit at maturity (total profit for the full term)
                self.profit = self.final_return_amount - self.invested_amount
                self.profit = self.profit.quantize(Decimal('0.01'))

                # Calculate investment end date
                if self.investment_start_date:
                    self.investment_end_date = self.investment_start_date + timedelta(days=int(self.investment_period * 365.25))

                # --- Calculate Current Accrued Profit ---
                # This profit is what's earned up to the current date, not the full projected amount
                if self.is_investment_active and self.investment_start_date:
                    current_date = timezone.now().date() # Use .date() because investment_start_date is a DateField

                    # Ensure we don't calculate profit beyond the projected end date
                    effective_calculation_date = current_date
                    if self.investment_end_date and current_date > self.investment_end_date:
                        effective_calculation_date = self.investment_end_date
                    
                    # Calculate days elapsed (ensure positive or zero)
                    time_elapsed = effective_calculation_date - self.investment_start_date
                    days_elapsed = max(0, time_elapsed.days)

                    if days_elapsed > 0:
                        # Simple interest accrued: P * R * (T_days / 365.25)
                        profit_calc = self.invested_amount * rate_decimal * (Decimal(str(days_elapsed)) / Decimal('365.25'))
                        self.current_accrued_profit = profit_calc.quantize(Decimal('0.01'))
                    else:
                        self.current_accrued_profit = Decimal('0.00')
                else: # If investment is not active or no start date, accrued profit is 0
                    self.current_accrued_profit = Decimal('0.00')

                # --- Set total_portfolio_value to reflect current value (principal + accrued profit) ---
                self.total_portfolio_value = self.invested_amount + self.current_accrued_profit
                self.total_portfolio_value = self.total_portfolio_value.quantize(Decimal('0.01'))


            except InterestRateSetting.DoesNotExist:
                # Fallback if no specific interest rate setting is found
                print(f"--- WARNING: No active InterestRateSetting found for Group '{self.selected_service_group.name}', Period {self.investment_period} years. Profit/Return set to 0. ---")
                self.final_return_amount = self.invested_amount
                self.profit = Decimal('0.00')
                self.current_accrued_profit = Decimal('0.00')
                self.total_portfolio_value = self.invested_amount
                self.interest_rate_applied = Decimal('0.0000')
                self.investment_end_date = None
            except Exception as e:
                # Catch any other unexpected errors during calculation
                print(f"--- ERROR in calculate_derived_fields for Investor {self.pk}: {e} ---")
                self.final_return_amount = self.invested_amount
                self.profit = Decimal('0.00')
                self.current_accrued_profit = Decimal('0.00')
                self.total_portfolio_value = self.invested_amount
                self.interest_rate_applied = Decimal('0.0000')
                self.investment_end_date = None
        else:
            # If fundamental conditions for calculation are not met (e.g., shares=0 or group missing)
            self.final_return_amount = self.invested_amount
            self.profit = Decimal('0.00')
            self.current_accrued_profit = Decimal('0.00')
            self.total_portfolio_value = self.invested_amount
            self.interest_rate_applied = Decimal('0.0000')
            self.investment_end_date = None

        # Ensure all Decimal fields are correctly rounded for storage
        self.invested_amount = self.invested_amount.quantize(Decimal('0.01'))
        self.final_return_amount = self.final_return_amount.quantize(Decimal('0.01'))
        self.profit = self.profit.quantize(Decimal('0.01'))
        self.current_accrued_profit = self.current_accrued_profit.quantize(Decimal('0.01'))
        self.total_portfolio_value = self.total_portfolio_value.quantize(Decimal('0.01'))
        self.interest_rate_applied = self.interest_rate_applied.quantize(Decimal('0.0000'))


# MARK: Pre-Save Signal Receiver
@receiver(pre_save, sender=Investor)
def investor_pre_save_receiver(sender, instance, **kwargs):
    """
    This signal ensures that derived fields (invested_amount, profit,
    final_return_amount, current_accrued_profit, total_portfolio_value,
    and investment_end_date) are calculated before an Investor instance is saved.
    """
    instance.calculate_derived_fields()