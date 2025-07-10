# SHA_GROUP/investors/views.py
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.shortcuts import get_object_or_404
from .models import Investor, InvestmentServiceGroup, InterestRateSetting
from .serializers import (
    InvestorSerializer, InvestmentServiceGroupSerializer,
    InterestRateSettingSerializer, UserSerializerForInvestor
)
from sha.permissions import IsAdminUser
from sha.utils import api_response 
from rest_framework.exceptions import ValidationError as DRFValidationError 
from .permissions import IsAdminUser, IsOwnerOrAdmin
from django.db.models import Sum, Count
from decimal import Decimal

# MARK: servicegroup
class InvestmentServiceGroupViewSet(viewsets.ModelViewSet):
    queryset = InvestmentServiceGroup.objects.all().order_by('name')
    serializer_class = InvestmentServiceGroupSerializer
    permission_classes = [IsAdminUser]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset()) 
        page = self.paginate_queryset(queryset) 
        if page is not None:
            serializer = self.get_serializer(page, many=True)
           
            return api_response(
                True,
                "Investment Service Groups listed successfully.",
                data=self.get_paginated_response(serializer.data).data,
                status_code=status.HTTP_200_OK
            )

        serializer = self.get_serializer(queryset, many=True) 

        return api_response(
            True,
            "Investment Service Groups listed successfully.",
            data=serializer.data, 
            status_code=status.HTTP_200_OK
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object() 
        serializer = self.get_serializer(instance)
        return api_response(
            True,
            "Investment Service Group retrieved successfully.",
            data=serializer.data, 
            status_code=status.HTTP_200_OK
        )

   
    


    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        
        return api_response(
            True,
            "Investment Service Group created successfully.",
            data={"id": serializer.data.get('id'), "name": serializer.data.get('name')}, 
            status_code=status.HTTP_201_CREATED,
            headers=headers
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True) 
        self.perform_update(serializer) 
        return api_response(
            True,
            "Investment Service Group updated successfully.",
            data={"id": serializer.data.get('id'), "name": serializer.data.get('name')},
            status_code=status.HTTP_200_OK
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object() 
        self.perform_destroy(instance)

        
        return api_response(
            True,
            "Investment Service Group deleted successfully.",
            data=None,
            status_code=status.HTTP_204_NO_CONTENT
        )

# MARK: interest rate
class InterestRateSettingViewSet(viewsets.ModelViewSet):
    queryset = InterestRateSetting.objects.all().select_related('service_group').order_by('service_group__name', 'period_in_years')
    serializer_class = InterestRateSettingSerializer
    permission_classes = [IsAdminUser]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            
            return api_response(
                True,
                "Interest Rate Settings listed successfully.",
                data=self.get_paginated_response(serializer.data).data,
                status_code=status.HTTP_200_OK
            )

        serializer = self.get_serializer(queryset, many=True) 

        return api_response(
            True,
            "Interest Rate Settings listed successfully.",
            data=serializer.data, 
            status_code=status.HTTP_200_OK
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance) 
        return api_response(
            True,
            "Interest Rate Settings listed successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    
    


    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

       
        return api_response(
            True,
            "Interest Rate Setting created successfully.",
            data={
                "id": serializer.data.get('id'),
                "period_in_years": serializer.data.get('period_in_years'),
                "interest_percentage": serializer.data.get('interest_percentage'),
                "service_group": serializer.data.get('service_group'), 
                # "rate": serializer.data.get('rate')
            },
            status_code=status.HTTP_201_CREATED,
            headers=headers
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object() 
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        
        return api_response(
            True,
            "Interest Rate Setting updated successfully.",
            data={"id": serializer.data.get('id'), "period_in_years": serializer.data.get('period_in_years'), "interest_percentage": serializer.data.get('interest_percentage'), "service_group": serializer.data.get('service_group'), "rate": serializer.data.get('rate')},
            status_code=status.HTTP_200_OK
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        
        return api_response(
            True,
            "Interest Rate Setting deleted successfully.",
            data=None, 
            status_code=status.HTTP_204_NO_CONTENT
        )


# MARK: investor
class InvestorViewSet(viewsets.ModelViewSet):
    
    queryset = Investor.objects.all().select_related('user', 'selected_service_group')
    serializer_class = InvestorSerializer
    permission_classes = [permissions.IsAuthenticated] 

    def get_permissions(self):
       
        if self.action in ['retrieve', 'list', 'full_profile', 'my_profile', 'create', 'dashboard_summary']:
            return [permissions.IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'destroy']:
           
            return [IsOwnerOrAdmin()]
       
        return [IsAdminUser()] 


    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_staff:
           
            return queryset
        else:
            
            return queryset.filter(user=self.request.user) 

    def create(self, request, *args, **kwargs):
        with transaction.atomic():
            mutable_data = request.data.copy()

            if not self.request.user.is_staff:
                mutable_data['user_id'] = self.request.user.id
            else:
                
                if 'user_id' not in mutable_data:
                   
                    return api_response(
                        False,
                        "As an admin, you must provide the 'user' ID for whom the investor profile is being created.",
                        data={"user_id": ["This field is required for admin creation."]},
                        status_code=status.HTTP_400_BAD_REQUEST
                    )


            serializer = self.get_serializer(data=mutable_data)

            try:
                serializer.is_valid(raise_exception=True)
            except DRFValidationError as e:
               
                if 'non_field_errors' in e.detail:
                    
                    error_message = e.detail['non_field_errors'][0]
                else:
                   
                    first_error_key = next(iter(e.detail))
                    error_message = f"{first_error_key}: {e.detail[first_error_key][0]}"

                return api_response(
                    False,
                    error_message, 
                    data=None,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            # except DRFValidationError as e:
            #     # Extract the first error message from the serializer errors
            #     # This makes the 'message' field in the response more specific
            #     first_error_key = next(iter(e.detail)) # Get the first field with an error
            #     first_error_message = e.detail[first_error_key][0] # Get the first error message for that field

            #     return api_response(
            #         False,
            #         f"{first_error_key}: {first_error_message}", # Specific message
            #         data=e.detail, # Keep the full error details in 'data'
            #         status_code=status.HTTP_400_BAD_REQUEST
            #     )
            except Exception as e:
                return api_response(
                    False,
                    f"An unexpected error occurred: {str(e)}",
                    data=None,
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)

            return api_response(
                True,
                "Investor profile created successfully.",
                data=serializer.data,
                status_code=status.HTTP_201_CREATED,
                headers=headers
            )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return api_response(
            True,
            "Investor profile retrieved successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        if not queryset.exists():
            return api_response(
                True,
                "No investor profiles found for this user.", 
                data=[],
                status_code=status.HTTP_200_OK 
            )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return api_response(
                True,
                "Investor profiles listed successfully.",
                data=self.get_paginated_response(serializer.data).data,
                status_code=status.HTTP_200_OK
            )

        serializer = self.get_serializer(queryset, many=True)
        return api_response(
            True,
            "Investor profiles listed successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    def update(self, request, *args, **kwargs):
        with transaction.atomic():
            partial = kwargs.pop('partial', False)
            instance = self.get_object()

            
            mutable_data = request.data.copy()
            if 'user_id' in mutable_data and mutable_data['user_id'] != instance.user.id and not request.user.is_staff:
                 return api_response(False, "You are not authorized to change the user of this investment.", status_code=status.HTTP_403_FORBIDDEN)

            serializer = self.get_serializer(instance, data=mutable_data, partial=partial)
            try:
                serializer.is_valid(raise_exception=True)
            except DRFValidationError as e:
                
                if 'non_field_errors' in e.detail:
                    error_message = e.detail['non_field_errors'][0]
                else:
                    first_error_key = next(iter(e.detail))
                    error_message = f"{first_error_key}: {e.detail[first_error_key][0]}"
                return api_response(False, error_message, data=e.detail, status_code=status.HTTP_400_BAD_REQUEST)


            self.perform_update(serializer)

            return api_response(True, "Investor profile updated successfully.", data=serializer.data)

    def destroy(self, request, *args, **kwargs):
        with transaction.atomic():
            instance = self.get_object()
            self.perform_destroy(instance)
            
            return api_response(True, "Investor profile deleted successfully.", data=None, status_code=status.HTTP_204_NO_CONTENT)

# MARK: full profile

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def full_profile(self, request, pk=None):
        investor = self.get_object()
        
        if not request.user.is_staff and investor.user != request.user:
            return api_response(False, "You do not have permission to access this investor's profile.", status_code=status.HTTP_403_FORBIDDEN)

        investor_data = self.get_serializer(investor).data
        user_data = UserSerializerForInvestor(investor.user).data

        response_data = {
            "investor_profile": investor_data, 
            "user_details": user_data,
           
        }
        return api_response(True, "Full investor profile retrieved.", data=response_data)

#MARK: my profile
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_profile(self, request):
        """
        Allows an authenticated user to retrieve all their Investor profiles.
        """
        
        user_investments = self.get_queryset()

        if not user_investments.exists():
            return api_response(False, "No investor profiles found for this user.", status_code=status.HTTP_404_NOT_FOUND)

        
        serializer = self.get_serializer(user_investments, many=True)
        return api_response(True, "Your investor profiles retrieved.", data=serializer.data)
# MARK: dashboard summary
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def dashboard_summary(self, request):
        """
        Provides a summary of the authenticated user's investor portfolio for dashboard display.
        This endpoint is for the currently authenticated user only, regardless of staff status.
        Includes total invested amount, profit, portfolio value, and count of active investments,
        with a breakdown by service group, including the total shares for each group.
        """
        user_investments = Investor.objects.filter(user=request.user).select_related('selected_service_group')

        if not user_investments.exists():
            return api_response(
                True,
                "No investment data found for your dashboard.",
                data={
                    "total_active_investments_count": 0,
                    "total_invested_amount_active": "0.00",
                    "total_profit_active": "0.00",
                    "total_portfolio_value_active": "0.00",
                    "active_investments_by_service_group": []
                },
                status_code=status.HTTP_200_OK
            )

        
        active_investments = user_investments.filter(is_investment_active=True)
        summary_data = active_investments.aggregate(
            total_active_investments_count=Count('id'),
            total_invested_amount_active=Sum('invested_amount'),
            total_profit_active=Sum('profit'),
            total_portfolio_value_active=Sum('total_portfolio_value')
        )

        total_invested_amount_active = summary_data['total_invested_amount_active'] or Decimal('0.00')
        total_profit_active = summary_data['total_profit_active'] or Decimal('0.00')
        total_portfolio_value_active = summary_data['total_portfolio_value_active'] or Decimal('0.00')

        
        service_group_breakdown = active_investments.values('selected_service_group__id', 'selected_service_group__name').annotate(
            invested_in_group=Sum('invested_amount'),
            profit_in_group=Sum('profit'),
            portfolio_value_in_group=Sum('total_portfolio_value'),
            count_in_group=Count('id'),
            total_shares_in_group=Sum('number_of_shares') 
        ).order_by('selected_service_group__name')

        
        formatted_breakdown = []
        for item in service_group_breakdown:
            formatted_breakdown.append({
                "service_group_id": item['selected_service_group__id'],
                "service_group_name": item['selected_service_group__name'],
                "count_in_group": item['count_in_group'],
                "invested_in_group": str(item['invested_in_group'] or Decimal('0.00')),
                "profit_in_group": str(item['profit_in_group'] or Decimal('0.00')),
                "portfolio_value_in_group": str(item['portfolio_value_in_group'] or Decimal('0.00')),
                "total_shares_in_group": str(item['total_shares_in_group'] or Decimal('0.00')) 
            })

        response_data = {
            "total_active_investments_count": summary_data['total_active_investments_count'],
            "total_invested_amount_active": str(total_invested_amount_active),
            "total_profit_active": str(total_profit_active),
            "total_portfolio_value_active": str(total_portfolio_value_active),
            "active_investments_by_service_group": formatted_breakdown
        }

        return api_response(
            True,
            "Dashboard summary retrieved successfully.",
            data=response_data,
            status_code=status.HTTP_200_OK
        )