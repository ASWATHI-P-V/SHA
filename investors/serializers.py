# SHA_GROUP/investor_api/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Investor, InvestmentServiceGroup, InterestRateSetting
from decimal import Decimal

User = get_user_model()

class InvestmentServiceGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvestmentServiceGroup
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class InterestRateSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterestRateSetting
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class UserSerializerForInvestor(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'mobile_number', 'email']
        read_only_fields = ['id', 'name', 'mobile_number', 'email']

class InvestorSerializer(serializers.ModelSerializer):
    user = UserSerializerForInvestor(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='user', write_only=True, required=False, allow_null=True,
        help_text="ID of the user associated with this investment. Required if creating a new investor."
    )
    service_groups = InvestmentServiceGroupSerializer(many=True, read_only=True)
    service_group_ids = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=InvestmentServiceGroup.objects.all()),
        write_only=True, required=False, help_text="List of Investment Service Group IDs."
    )

    class Meta:
        model = Investor
        fields = [
            'uuid', 'user', 'user_id', 'invested_amount', 'tokens_generated',
            'investment_period', 'interest_rate_applied', 'final_return_amount',
            'profit', 'total_portfolio_value', # Added profit and total_portfolio_value here
            'investment_start_date', 'investment_end_date', 'is_investment_active',
            'service_groups', 'service_group_ids', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'uuid', 'tokens_generated', 'interest_rate_applied',
            'final_return_amount', 'profit', 'total_portfolio_value', # Added profit and total_portfolio_value here
            'investment_end_date', 'created_at', 'updated_at'
        ]

    def validate_invested_amount(self, value):
        if value is None or value <= 0:
            raise serializers.ValidationError("Invested amount must be a positive number.")
        return value

    def validate_investment_period(self, value):
        if value not in [3, 5, 10]:
            raise serializers.ValidationError("Investment period must be 3, 5, or 10 years.")
        return value

    def create(self, validated_data):
        user = validated_data.pop('user', None)
        service_groups_data = validated_data.pop('service_group_ids', [])

        if not user:
            raise serializers.ValidationError({"user_id": "User ID is required to create an investor profile."})

        if Investor.objects.filter(user=user).exists():
            raise serializers.ValidationError({"user_id": "An investor profile already exists for this user."})

        investor = Investor.objects.create(user=user, **validated_data)
        investor.service_groups.set(service_groups_data)
        return investor

    def update(self, instance, validated_data):
        service_groups_data = validated_data.pop('service_group_ids', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save() # Call save to trigger calculations

        if service_groups_data is not None:
            instance.service_groups.set(service_groups_data)

        return instance