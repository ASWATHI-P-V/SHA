# SHA_GROUP/investors/models.py
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import uuid
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

User = settings.AUTH_USER_MODEL

class InvestmentServiceGroup(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name=_("Service Group Name"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Description"))
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Investment Service Group")
        verbose_name_plural = _("Investment Service Groups")
        ordering = ['name']

    def __str__(self):
        return self.name


class InterestRateSetting(models.Model):
    # NEW: Link InterestRateSetting to a specific InvestmentServiceGroup
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


class Investor(models.Model):
    user = models.ForeignKey( # CHANGED FROM OneToOneField
        User,
        on_delete=models.CASCADE,
        related_name='investments', # Changed related_name to reflect multiple investments
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
    invested_amount = models.DecimalField(
        max_digits=15, decimal_places=2,
        verbose_name=_("Invested Amount (AED)")
    )
    tokens_generated = models.DecimalField(
        max_digits=15, decimal_places=2,
        null=True, blank=True,
        verbose_name=_("Tokens Generated"),
        help_text=_("Calculated based on invested amount (e.g., 1 token per 100 AED).")
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
        verbose_name = _("Investor")
        verbose_name_plural = _("Investors")
        ordering = ['user__name', 'created_at']
        # NEW: Add unique_together constraint to prevent duplicate investments
        # A user cannot have two identical investments (same group, same period).
        unique_together = ('user', 'selected_service_group', 'investment_period')


    def save(self, *args, **kwargs):
        # Calculate tokens_generated if invested_amount is provided and tokens_generated is not set
        if self.invested_amount is not None and (self.tokens_generated is None or self.tokens_generated == Decimal('0.00')):
            # Example: 1 token per 100 AED
            token_rate = Decimal('100.00')
            self.tokens_generated = (self.invested_amount / token_rate).quantize(Decimal('0.01'))

        # Main calculation block for interest, profit, return, and end date
        if self.invested_amount is not None and self.invested_amount > 0 and \
           self.investment_period is not None and \
           self.selected_service_group is not None:
            
            print("--- Investor.save() Calculations Start ---")
            print(f"Checking for InterestRateSetting with:")
            print(f"   Service Group ID: {self.selected_service_group.id}")
            print(f"   Period (Years): {self.investment_period}")
            
            try:
                # Find the interest rate specific to the selected group and period
                interest_setting = InterestRateSetting.objects.get(
                    service_group=self.selected_service_group,
                    period_in_years=self.investment_period,
                    is_active=True # Crucial: This must be True in DB for calculations to apply
                )
                
                self.interest_rate_applied = interest_setting.interest_percentage
                
                # Convert percentage to a decimal for calculation (e.g., 5.00% -> 0.05)
                rate_decimal = self.interest_rate_applied / Decimal('100.00')

                # Simple interest calculation: Principal * (1 + (Rate * Time))
                # Formula: A = P(1 + RT) where A=final_return_amount, P=invested_amount, R=rate_decimal, T=investment_period
                self.final_return_amount = self.invested_amount * (Decimal('1.00') + (rate_decimal * self.investment_period))
                
                # Round to 2 decimal places to prevent floating point issues and match decimal_places
                self.final_return_amount = self.final_return_amount.quantize(Decimal('0.01'))

                self.profit = self.final_return_amount - self.invested_amount
                self.profit = self.profit.quantize(Decimal('0.01'))

                self.total_portfolio_value = self.invested_amount + self.profit
                self.total_portfolio_value = self.total_portfolio_value.quantize(Decimal('0.01'))

                # Calculate end date
                if self.investment_start_date:
                    self.investment_end_date = self.investment_start_date + timedelta(days=self.investment_period * 365)
                else:
                    # If start date is not set (should be default=timezone.now().date in model)
                    self.investment_start_date = timezone.now().date()
                    self.investment_end_date = self.investment_start_date + timedelta(days=self.investment_period * 365)
                
                print(f"Calculations applied:")
                print(f"   Interest Rate Applied: {self.interest_rate_applied}%")
                print(f"   Final Return Amount: {self.final_return_amount}")
                print(f"   Profit: {self.profit}")
                print(f"   Total Portfolio Value: {self.total_portfolio_value}")
                print(f"   Investment End Date: {self.investment_end_date}")

            except InterestRateSetting.DoesNotExist:
                print("--- WARNING: No matching active InterestRateSetting found. Defaulting calculations. ---")
                self.final_return_amount = self.invested_amount
                self.profit = Decimal('0.00')
                self.total_portfolio_value = self.invested_amount
                self.interest_rate_applied = Decimal('0.00')
                self.investment_end_date = None
            except Exception as e:
                print(f"--- ERROR during calculation in Investor.save(): {e} ---")
                # Ensure fields are set to default/safe values on unexpected error
                self.final_return_amount = self.invested_amount
                self.profit = Decimal('0.00')
                self.total_portfolio_value = self.invested_amount
                self.interest_rate_applied = Decimal('0.00')
                self.investment_end_date = None
        else:
            print("--- Investor.save() Conditions for main calculation NOT met. Defaulting fields. ---")
            print(f"   invested_amount: {self.invested_amount}")
            print(f"   investment_period: {self.investment_period}")
            print(f"   selected_service_group: {self.selected_service_group}")
            self.final_return_amount = self.invested_amount if self.invested_amount is not None else Decimal('0.00')
            self.profit = Decimal('0.00')
            self.total_portfolio_value = self.invested_amount if self.invested_amount is not None else Decimal('0.00')
            self.interest_rate_applied = Decimal('0.00')
            self.investment_end_date = None

        super().save(*args, **kwargs)
        print("--- Investor.save() Calculations End ---")

    def __str__(self):
        user_info = self.user.get_full_name() if self.user else f"User ID: {self.user_id}"
        group_info = self.selected_service_group.name if self.selected_service_group else "No Group"
        return f"Investment by {user_info} in {group_info} ({self.investment_period}Y)"



    # def save(self, *args, **kwargs):
    #     # ... (initial invested_amount and tokens_generated calculation) ...

    #     # Main calculation block for interest, profit, return, and end date
    #     if self.invested_amount is not None and self.invested_amount > 0 and \
    #        self.investment_period is not None and \
    #        self.selected_service_group is not None:
            
    #         print("--- Investor.save() Calculations Start ---")
    #         print(f"Checking for InterestRateSetting with:")
    #         print(f"  Service Group ID: {self.selected_service_group.id}")
    #         print(f"  Period (Years): {self.investment_period}")
            
    #         try:
    #             # Find the interest rate specific to the selected group and period
    #             interest_setting = InterestRateSetting.objects.get(
    #                 service_group=self.selected_service_group,
    #                 period_in_years=self.investment_period,
    #                 is_active=True # Crucial: This must be True in DB for calculations to apply
    #             )
                
    #             self.interest_rate_applied = interest_setting.interest_percentage
                
    #             # Convert percentage to a decimal for calculation (e.g., 5.00% -> 0.05)
    #             rate_decimal = self.interest_rate_applied / Decimal('100.00')

    #             # Simple interest calculation: Principal * (1 + (Rate * Time))
    #             # Formula: A = P(1 + RT) where A=final_return_amount, P=invested_amount, R=rate_decimal, T=investment_period
    #             self.final_return_amount = self.invested_amount * (Decimal('1.00') + (rate_decimal * self.investment_period))
                
    #             # Round to 2 decimal places to prevent floating point issues and match decimal_places
    #             self.final_return_amount = self.final_return_amount.quantize(Decimal('0.01'))

    #             self.profit = self.final_return_amount - self.invested_amount
    #             self.profit = self.profit.quantize(Decimal('0.01'))

    #             self.total_portfolio_value = self.invested_amount + self.profit
    #             self.total_portfolio_value = self.total_portfolio_value.quantize(Decimal('0.01'))

    #             # Calculate end date
    #             from datetime import timedelta
    #             if self.investment_start_date:
    #                 self.investment_end_date = self.investment_start_date + timedelta(days=self.investment_period * 365)
    #             else:
    #                 # If start date is not set (should be default=timezone.now().date in model)
    #                 self.investment_start_date = timezone.now().date()
    #                 self.investment_end_date = self.investment_start_date + timedelta(days=self.investment_period * 365)
                
    #             print(f"Calculations applied:")
    #             print(f"  Interest Rate Applied: {self.interest_rate_applied}%")
    #             print(f"  Final Return Amount: {self.final_return_amount}")
    #             print(f"  Profit: {self.profit}")
    #             print(f"  Total Portfolio Value: {self.total_portfolio_value}")
    #             print(f"  Investment End Date: {self.investment_end_date}")

    #         except InterestRateSetting.DoesNotExist:
    #             print("--- WARNING: No matching active InterestRateSetting found. Defaulting calculations. ---")
    #             self.final_return_amount = self.invested_amount
    #             self.profit = Decimal('0.00')
    #             self.total_portfolio_value = self.invested_amount
    #             self.interest_rate_applied = Decimal('0.00')
    #             self.investment_end_date = None
    #         except Exception as e:
    #             print(f"--- ERROR during calculation in Investor.save(): {e} ---")
    #             # Ensure fields are set to default/safe values on unexpected error
    #             self.final_return_amount = self.invested_amount
    #             self.profit = Decimal('0.00')
    #             self.total_portfolio_value = self.invested_amount
    #             self.interest_rate_applied = Decimal('0.00')
    #             self.investment_end_date = None
    #     else:
    #         print("--- Investor.save() Conditions for main calculation NOT met. Defaulting fields. ---")
    #         print(f"  invested_amount: {self.invested_amount}")
    #         print(f"  investment_period: {self.investment_period}")
    #         print(f"  selected_service_group: {self.selected_service_group}")
    #         self.final_return_amount = self.invested_amount if self.invested_amount is not None else Decimal('0.00')
    #         self.profit = Decimal('0.00')
    #         self.total_portfolio_value = self.invested_amount if self.invested_amount is not None else Decimal('0.00')
    #         self.interest_rate_applied = Decimal('0.00')
    #         self.investment_end_date = None

    #     super().save(*args, **kwargs)
    #     print("--- Investor.save() Calculations End ---")

    # def __str__(self):
    #     user_info = self.user.get_full_name() if self.user else f"User ID: {self.user_id}"
    #     group_info = self.selected_service_group.name if self.selected_service_group else "No Group"
    #     return f"Investment by {user_info} in {group_info}"
    






##############################
    # def save(self, *args, **kwargs):
    #     # Ensure invested_amount is treated as Decimal for calculations
    #     if self.invested_amount is None:
    #         self.invested_amount = Decimal('0.00')

    #     # Calculate tokens_generated
    #     if self.invested_amount > 0:
    #         self.tokens_generated = self.invested_amount / Decimal('100.00')
    #     else:
    #         self.tokens_generated = Decimal('0.00')

    #     # Calculate final_return_amount, profit, total_portfolio_value, and investment_end_date
    #     # NEW LOGIC: Use selected_service_group to find the interest rate
    #     if self.invested_amount > 0 and self.investment_period and self.selected_service_group:
    #         try:
    #             # Find the interest rate specific to the selected group and period
    #             interest_setting = InterestRateSetting.objects.get(
    #                 service_group=self.selected_service_group,
    #                 period_in_years=self.investment_period,
    #                 is_active=True
    #             )
    #             self.interest_rate_applied = interest_setting.interest_percentage
    #             rate_decimal = self.interest_rate_applied / Decimal('100.00')

    #             # Simple interest calculation: Principal * (1 + (Rate/100 * Time))
    #             self.final_return_amount = self.invested_amount * (Decimal('1.00') + (rate_decimal * self.investment_period))
    #             self.profit = self.final_return_amount - self.invested_amount
    #             self.total_portfolio_value = self.invested_amount + self.profit


    #             # Calculate end date
    #             if self.investment_start_date:
    #                 self.investment_end_date = self.investment_start_date + timezone.timedelta(days=self.investment_period * 365)
    #             else:
    #                 self.investment_start_date = timezone.now().date() # Set to today if not set
    #                 self.investment_end_date = self.investment_start_date + timezone.timedelta(days=self.investment_period * 365)

    #         except InterestRateSetting.DoesNotExist:
    #             # Fallback if no matching active interest rate setting is found for the chosen group/period
    #             self.final_return_amount = self.invested_amount
    #             self.profit = Decimal('0.00')
    #             self.total_portfolio_value = self.invested_amount
    #             self.interest_rate_applied = Decimal('0.00')
    #             self.investment_end_date = None
    #     else:
    #         # If no invested amount, period, or selected group, clear calculated fields
    #         self.final_return_amount = self.invested_amount
    #         self.profit = Decimal('0.00')
    #         self.total_portfolio_value = self.invested_amount
    #         self.interest_rate_applied = Decimal('0.00')
    #         self.investment_end_date = None

    #     super().save(*args, **kwargs)

    # def __str__(self):
    #     user_info = self.user.get_full_name() if self.user else f"User ID: {self.user_id}"
    #     group_info = self.selected_service_group.name if self.selected_service_group else "No Group"
    #     return f"Investment by {user_info} in {group_info}"
