# SHA_GROUP/investor/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Investor, InvestmentServiceGroup, InterestRateSetting
from decimal import Decimal

User = get_user_model()
#MARK: Investment Service Group Serializer
class InvestmentServiceGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvestmentServiceGroup
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
#MARK: Interest Rate Setting Serializer
class InterestRateSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterestRateSetting
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
#MARK: User Serializer for Investor
class UserSerializerForInvestor(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'mobile_number', 'email']
        read_only_fields = ['id', 'name', 'mobile_number', 'email']
#MARK: Investor Serializer
class InvestorSerializer(serializers.ModelSerializer):
    user = UserSerializerForInvestor(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='user', write_only=True, required=True,
        help_text="ID of the user associated with this investment. Required if creating a new investor."
    )
    selected_service_group = serializers.PrimaryKeyRelatedField(
        queryset=InvestmentServiceGroup.objects.all(),
        required=True,
        help_text="ID of the selected Investment Service Group."
    )
    selected_service_group_details = InvestmentServiceGroupSerializer(
        source='selected_service_group', read_only=True
    )
    number_of_shares = serializers.DecimalField(
        max_digits=15, decimal_places=2, required=True, min_value=Decimal('0.01'),
        help_text="The total number of shares to purchase for this investment."
    )

    # invested_amount is now read-only and calculated
    invested_amount = serializers.DecimalField(
        max_digits=15, decimal_places=2, read_only=True,
        help_text="Calculated based on number of shares and the service group's share value."
    )

    class Meta:
        model = Investor
        fields = [
            'id','uuid', 'user', 'user_id', 'number_of_shares', 'invested_amount',
            'investment_period', 'interest_rate_applied', 'final_return_amount',
            'profit', 'total_portfolio_value',
            'investment_start_date', 'investment_end_date', 'is_investment_active',
            'selected_service_group',
            'selected_service_group_details', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id','uuid', 'invested_amount', 'interest_rate_applied',
            'final_return_amount', 'profit', 'total_portfolio_value',
            'investment_end_date', 'created_at', 'updated_at',
            'selected_service_group_details'
        ]
        # NEW: Add validators for unique_together here for better API error messages
        
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Investor.objects.all(),
                fields=['user', 'selected_service_group', 'investment_period'],
                message="An investment with this user, service group, and investment period already exists."
            )
        ]

    def validate_number_of_shares(self, value):
        if value <= 0:
            raise serializers.ValidationError("Number of shares must be a positive number.")
        return value

    def validate_investment_period(self, value):
        if value not in [3, 5, 10]:
            raise serializers.ValidationError("Investment period must be 3, 5, or 10 years.")
        return value
