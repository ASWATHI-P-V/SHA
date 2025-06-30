# SHA_GROUP/investors/views.py
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction

from .models import Investor, InvestmentServiceGroup, InterestRateSetting
from .serializers import (
    InvestorSerializer, InvestmentServiceGroupSerializer,
    InterestRateSettingSerializer, UserSerializerForInvestor
)
from sha.permissions import IsAdminUser # Custom permissions
from sha.utils import api_response # Utility for consistent API responses


class InvestmentServiceGroupViewSet(viewsets.ModelViewSet):
    queryset = InvestmentServiceGroup.objects.all().order_by('name')
    serializer_class = InvestmentServiceGroupSerializer
    permission_classes = [IsAdminUser]


class InterestRateSettingViewSet(viewsets.ModelViewSet):
    queryset = InterestRateSetting.objects.all().select_related('service_group').order_by('service_group__name', 'period_in_years')
    serializer_class = InterestRateSettingSerializer
    permission_classes = [IsAdminUser]


class InvestorViewSet(viewsets.ModelViewSet):
    # Pre-fetch selected_service_group and user for efficiency
    queryset = Investor.objects.all().select_related('user', 'selected_service_group')
    serializer_class = InvestorSerializer
    permission_classes = [permissions.IsAuthenticated] # Base permission: authenticated users

    def get_permissions(self):
        # Allow non-admins to only view their own profile. Admins can do anything.
        if self.action in ['retrieve', 'list', 'full_profile', 'my_profile']:
            return [permissions.IsAuthenticated()] # Anyone authenticated can retrieve/list (list limited by queryset)
        # All other actions (create, update, delete) require admin
        return [IsAdminUser()]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_staff:
            # Admins can see all investors
            return queryset
        else:
            # Regular users can only see their own investor profile
            return queryset.filter(user=self.request.user)

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def full_profile(self, request, pk=None):
        """
        Retrieves the investor's details along with the full User profile.
        Accessible by admin for any investor, or by a user for their own investor profile.
        """
        # get_object() uses the filtered queryset, so it already handles permissions for non-admins
        investor = self.get_object()

        # Extra check just in case get_object() somehow returned a record not belonging to user
        if not request.user.is_staff and investor.user != request.user:
            return api_response(False, "You do not have permission to access this investor's profile.", status_code=status.HTTP_403_FORBIDDEN)

        investor_data = self.get_serializer(investor).data
        user_data = UserSerializerForInvestor(investor.user).data

        response_data = {
            "investor_profile": investor_data,
            "user_details": user_data
        }
        return api_response(True, "Full investor profile retrieved.", data=response_data)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_profile(self, request):
        """
        Allows an authenticated user to retrieve their own Investor profile.
        """
        # The get_queryset method already filters by request.user for non-staff
        investor = self.get_queryset().first() # There should be at most one for a regular user

        if not investor:
            return api_response(False, "No investor profile found for this user.", status_code=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(investor)
        return api_response(True, "Your investor profile retrieved.", data=serializer.data)

    # Standard ModelViewSet methods (create, update, destroy) are implicitly handled
    # and their permissions are governed by `get_permissions()`.
    # You only need to override them if you need custom logic for the API response
    # or additional side effects beyond what perform_create/update/destroy offers.

    def create(self, request, *args, **kwargs):
        with transaction.atomic():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return api_response(True, "Investor profile created successfully.", data=serializer.data, status_code=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        with transaction.atomic():
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            # Important: If prefetch_related/select_related was used on the queryset,
            # and the underlying instance was modified, ensure the returned instance
            # from the serializer has the latest calculated values.
            # The instance.save() in the model will have updated these.
            # Re-serializing the instance is usually sufficient.
            # No explicit refresh_from_db is needed unless related objects were changed outside the ORM's knowledge.

            return api_response(True, "Investor profile updated successfully.", data=serializer.data)

    def destroy(self, request, *args, **kwargs):
        with transaction.atomic():
            instance = self.get_object()
            self.perform_destroy(instance)
            return api_response(True, "Investor profile deleted successfully.", status_code=status.HTTP_204_NO_CONTENT)