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
        queryset=User.objects.all(), source='user', write_only=True, required=True,
        help_text="ID of the user associated with this investment. Required if creating a new investor."
    )
    # NEW: Handle selected_service_group using PrimaryKeyRelatedField for writing
    selected_service_group = serializers.PrimaryKeyRelatedField(
        queryset=InvestmentServiceGroup.objects.all(),
        # You can make it required=False if the model allows null=True and you want to allow creating without it
        required=True, # Make it required if an investment *must* have a service group
        help_text="ID of the selected Investment Service Group."
    )
    # If you still want the full service group details on read, you can add another field:
    selected_service_group_details = InvestmentServiceGroupSerializer(
        source='selected_service_group', read_only=True
    )

    class Meta:
        model = Investor
        fields = [
            'id','uuid', 'user', 'user_id', 'invested_amount', 'tokens_generated',
            'investment_period', 'interest_rate_applied', 'final_return_amount',
            'profit', 'total_portfolio_value',
            'investment_start_date', 'investment_end_date', 'is_investment_active',
            'selected_service_group',
            'selected_service_group_details',  'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id','uuid', 'tokens_generated', 'interest_rate_applied',
            'final_return_amount', 'profit', 'total_portfolio_value', 
            'investment_end_date', 'created_at', 'updated_at',
            'selected_service_group_details'
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
        # user will be handled by source='user' in user_id field
        # selected_service_group will be handled by the direct field
        
        # Remove the old service_groups_data pop, as it no longer exists
        # service_groups_data = validated_data.pop('service_group_ids', []) # REMOVE THIS LINE

        # The uniqueness check for user is still relevant
        user = validated_data.get('user') # Get user directly from validated_data
        if Investor.objects.filter(user=user).exists():
            raise serializers.ValidationError({"user_id": "An investor profile already exists for this user."})

        # Create the investor instance directly with validated_data
        # 'user' and 'selected_service_group' will be in validated_data because of their respective fields
        investor = Investor.objects.create(**validated_data)
        
        # No need to set service groups explicitly here as it's a ForeignKey now
        # investor.service_groups.set(service_groups_data) # REMOVE THIS LINE

        return investor

    def update(self, instance, validated_data):
        # Remove service_groups_data pop, as it no longer exists
        # service_groups_data = validated_data.pop('service_group_ids', None) # REMOVE THIS LINE

        # Handle updating selected_service_group if it's in validated_data
        # This will be automatically handled by DRF's ModelSerializer if the field name matches
        # but you can explicitly handle it if needed
        # e.g., if 'selected_service_group' is passed and it's allowed to change:
        # if 'selected_service_group' in validated_data:
        #    instance.selected_service_group = validated_data.pop('selected_service_group')


        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save() # Call save to trigger calculations

        # No need to set service groups explicitly here as it's a ForeignKey now
        # if service_groups_data is not None:
        #    instance.service_groups.set(service_groups_data) # REMOVE THIS LINE

        return instance