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
from sha.permissions import IsAdminUser # Custom permissions
from sha.utils import api_response # Utility for consistent API responses
from rest_framework.exceptions import ValidationError as DRFValidationError # Alias it to avoid conflict with django.core.exceptions.ValidationError



class InvestmentServiceGroupViewSet(viewsets.ModelViewSet):
    queryset = InvestmentServiceGroup.objects.all().order_by('name')
    serializer_class = InvestmentServiceGroupSerializer
    permission_classes = [IsAdminUser]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset()) # Apply filtering (if any) and get the queryset

        page = self.paginate_queryset(queryset) # Apply pagination (if configured)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            # When pagination is applied, you usually return the paginated response
            # DRF's pagination renders its own structure, which includes 'results'
            # If you want to integrate this cleanly into api_response, it needs adjustment
            # For simplicity, here's a direct wrap.
            return api_response(
                True,
                "Investment Service Groups listed successfully.",
                data=self.get_paginated_response(serializer.data).data, # Get the paginated data structure
                status_code=status.HTTP_200_OK
            )

        serializer = self.get_serializer(queryset, many=True) # Serialize the list of objects

        return api_response(
            True,
            "Investment Service Groups listed successfully.",
            data=serializer.data, # Return the full serialized list of objects
            status_code=status.HTTP_200_OK
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object() # This will raise a 404 if not found (handled by your exception handler)
        serializer = self.get_serializer(instance) # Serialize the single object data

        return api_response(
            True,
            "Investment Service Group retrieved successfully.",
            data=serializer.data, # Return the full serialized object data here
            status_code=status.HTTP_200_OK
        )

    # Override the list method for multiple objects GET requests
    


    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        # Customize create response
        return api_response(
            True,
            "Investment Service Group created successfully.",
            data={"id": serializer.data.get('id'), "name": serializer.data.get('name')}, # Or data=None if you prefer
            status_code=status.HTTP_201_CREATED,
            headers=headers
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False) # Handles both PUT (partial=False) and PATCH (partial=True)
        instance = self.get_object() # Get the object to be updated
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True) # Validate data, raise 400 if invalid

        self.perform_update(serializer) # This calls serializer.save() internally

        # OPTION 1: Return a simple success message with data=null
        return api_response(
            True,
            "Investment Service Group updated successfully.",
            data={"id": serializer.data.get('id'), "name": serializer.data.get('name')},
            status_code=status.HTTP_200_OK
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object() # Get the object to be deleted
        self.perform_destroy(instance) # This performs the actual deletion

        
        return api_response(
            True,
            "Investment Service Group deleted successfully.",
            data=None, # Data should be null for a 204 No Content response
            status_code=status.HTTP_204_NO_CONTENT
        )


class InterestRateSettingViewSet(viewsets.ModelViewSet):
    queryset = InterestRateSetting.objects.all().select_related('service_group').order_by('service_group__name', 'period_in_years')
    serializer_class = InterestRateSettingSerializer
    permission_classes = [IsAdminUser]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset()) # Apply filtering (if any) and get the queryset

        page = self.paginate_queryset(queryset) # Apply pagination (if configured)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            # When pagination is applied, you usually return the paginated response
            # DRF's pagination renders its own structure, which includes 'results'
            # If you want to integrate this cleanly into api_response, it needs adjustment
            # For simplicity, here's a direct wrap.
            return api_response(
                True,
                "Interest Rate Settings listed successfully.",
                data=self.get_paginated_response(serializer.data).data, # Get the paginated data structure
                status_code=status.HTTP_200_OK
            )

        serializer = self.get_serializer(queryset, many=True) # Serialize the list of objects

        return api_response(
            True,
            "Interest Rate Settings listed successfully.",
            data=serializer.data, # Return the full serialized list of objects
            status_code=status.HTTP_200_OK
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object() # This will raise a 404 if not found (handled by your exception handler)
        serializer = self.get_serializer(instance) # Serialize the single object data

        return api_response(
            True,
            "Interest Rate Settings listed successfully.",
            data=serializer.data, # Return the full serialized object data here
            status_code=status.HTTP_200_OK
        )

    # Override the list method for multiple objects GET requests
    


    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        # Customize create response
        return api_response(
            True,
            "Interest Rate Setting created successfully.",
            data={
                "id": serializer.data.get('id'),
                "period_in_years": serializer.data.get('period_in_years'),
                "interest_percentage": serializer.data.get('interest_percentage'),
                "service_group": serializer.data.get('service_group'), # Include service group name or ID
                "rate": serializer.data.get('rate')
            },
            status_code=status.HTTP_201_CREATED,
            headers=headers
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False) # Handles both PUT (partial=False) and PATCH (partial=True)
        instance = self.get_object() # Get the object to be updated
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True) # Validate data, raise 400 if invalid

        self.perform_update(serializer) # This calls serializer.save() internally

        
        return api_response(
            True,
            "Interest Rate Setting updated successfully.",
            data={"id": serializer.data.get('id'), "period_in_years": serializer.data.get('period_in_years'), "interest_percentage": serializer.data.get('interest_percentage'), "service_group": serializer.data.get('service_group'), "rate": serializer.data.get('rate')},
            status_code=status.HTTP_200_OK
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object() # Get the object to be deleted
        self.perform_destroy(instance) # This performs the actual deletion

        
        return api_response(
            True,
            "Interest Rate Setting deleted successfully.",
            data=None, # Data should be null for a 204 No Content response
            status_code=status.HTTP_204_NO_CONTENT
        )



class InvestorViewSet(viewsets.ModelViewSet):
    # Pre-fetch selected_service_group and user for efficiency
    queryset = Investor.objects.all().select_related('user', 'selected_service_group')
    serializer_class = InvestorSerializer
    permission_classes = [permissions.IsAuthenticated] # Base permission: authenticated users

    def get_permissions(self):
        # Allow non-admins to only view their own profile. Admins can do anything.
        if self.action in ['retrieve', 'list', 'full_profile', 'my_profile', 'create']: # create is allowed for authenticated users
            return [permissions.IsAuthenticated()]
        # All other actions (update, delete) require admin
        return [IsAdminUser()]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_staff:
            # Admins can see all investors
            return queryset
        else:
            # Regular users can only see their own investor profiles (plural now)
            # The related_name on User is now 'investments'
            return queryset.filter(user=self.request.user) # No change needed here, filter(user=self.request.user) is fine.


    def create(self, request, *args, **kwargs):
        with transaction.atomic():
            mutable_data = request.data.copy()

            # For non-admins, inject the current user's ID into the mutable data.
            # This makes the 'user_id' field valid for their own profile.
            if not self.request.user.is_staff:
                mutable_data['user'] = self.request.user.id
            # else: # If admin is creating, they should explicitly provide 'user'
            #     if 'user' not in mutable_data:
            #         raise DRFValidationError({"user": "User ID is required for admin creation."})

            serializer = self.get_serializer(data=mutable_data)

            try:
                serializer.is_valid(raise_exception=True)
            except DRFValidationError as e:
                return api_response(
                    False,
                    "Validation error.",
                    data=e.detail,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
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
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            return api_response(True, "Investor profile updated successfully.", data=serializer.data)

    def destroy(self, request, *args, **kwargs):
        with transaction.atomic():
            instance = self.get_object()
            self.perform_destroy(instance)
            # For 204 No Content, data should typically be None
            return api_response(True, "Investor profile deleted successfully.", data=None, status_code=status.HTTP_204_NO_CONTENT)


    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def full_profile(self, request, pk=None):
        investor = self.get_object() # get_object() handles permissions based on get_queryset

        # This check might be redundant if get_object() already filtered correctly,
        # but it provides an extra layer of security.
        if not request.user.is_staff and investor.user != request.user:
            return api_response(False, "You do not have permission to access this investor's profile.", status_code=status.HTTP_403_FORBIDDEN)

        investor_data = self.get_serializer(investor).data
        user_data = UserSerializerForInvestor(investor.user).data

        response_data = {
            "investor_profile": investor_data, # This is for the specific investor instance
            "user_details": user_data,
            # If you wanted all investments for this user, you'd query them here:
            # "all_user_investments": self.get_serializer(investor.user.investments.all(), many=True).data
        }
        return api_response(True, "Full investor profile retrieved.", data=response_data)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_profile(self, request):
        """
        Allows an authenticated user to retrieve all their Investor profiles.
        """
        # The get_queryset method already filters by request.user for non-staff
        # It will return a queryset of potentially multiple Investor objects
        user_investments = self.get_queryset()

        if not user_investments.exists():
            return api_response(False, "No investor profiles found for this user.", status_code=status.HTTP_404_NOT_FOUND)

        # Serialize all investor profiles for the user
        serializer = self.get_serializer(user_investments, many=True)
        return api_response(True, "Your investor profiles retrieved.", data=serializer.data)













# class InvestorViewSet(viewsets.ModelViewSet):
#     # Pre-fetch selected_service_group and user for efficiency
#     queryset = Investor.objects.all().select_related('user', 'selected_service_group')
#     serializer_class = InvestorSerializer
#     permission_classes = [permissions.IsAuthenticated] # Base permission: authenticated users

#     def get_permissions(self):
#         # Allow non-admins to only view their own profile. Admins can do anything.
#         if self.action in ['retrieve', 'list', 'full_profile', 'my_profile', 'create', 'destroy']:
#             return [permissions.IsAuthenticated()] # Anyone authenticated can retrieve/list (list limited by queryset)
#         # All other actions (create, update, delete) require admin
#         return [IsAdminUser()]

#     def get_queryset(self):
#         queryset = super().get_queryset()
#         if self.request.user.is_staff:
#             # Admins can see all investors
#             return queryset
#         else:
#             # Regular users can only see their own investor profile
#             return queryset.filter(user=self.request.user)

#     def create(self, request, *args, **kwargs):
#         with transaction.atomic():
#             # Create a mutable copy of the request data
#             # It's crucial to do this before passing to the serializer if you intend to modify it.
#             mutable_data = request.data.copy()

#             # --- CUSTOM LOGIC FOR 'CREATE' PERMISSION FOR NON-ADMINS ---
#             # For non-admins, inject the current user's ID into the mutable data.
#             # This makes the 'user_id' field (now required=True in serializer) valid for their own profile.
#             if not self.request.user.is_staff:
#                 mutable_data['user'] = self.request.user.id
#             # --- END CUSTOM LOGIC ---

#             # Initialize serializer with the mutable data
#             serializer = self.get_serializer(data=mutable_data)

#             try:
#                 # Validate data; if invalid, DRFValidationError is raised here
#                 serializer.is_valid(raise_exception=True)
#             except DRFValidationError as e:
#                 # Catch the DRFValidationError and extract its detail
#                 return api_response(
#                     False,
#                     "Validation error.", # More specific message
#                     data=e.detail, # Pass the detailed error dictionary/list
#                     status_code=status.HTTP_400_BAD_REQUEST # Use 400 for validation errors
#                 )
#             except Exception as e:
#                 # Catch any other unexpected errors
#                 return api_response(
#                     False,
#                     f"An unexpected error occurred: {str(e)}",
#                     data=None,
#                     status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
#                 )

#             self.perform_create(serializer) # Saves the instance
#             headers = self.get_success_headers(serializer.data)

#             return api_response(
#                 True,
#                 "Investor profile created successfully.",
#                 data=serializer.data,
#                 status_code=status.HTTP_201_CREATED,
#                 headers=headers
#             )

#     def retrieve(self, request, *args, **kwargs):
#         # self.get_object() ensures the correct object is retrieved based on get_queryset permissions
#         instance = self.get_object()
#         serializer = self.get_serializer(instance)
#         return api_response(
#             True,
#             "Investor profile retrieved successfully.",
#             data=serializer.data,
#             status_code=status.HTTP_200_OK
#         )

#     def list(self, request, *args, **kwargs):
#         queryset = self.filter_queryset(self.get_queryset()) # Apply filtering if any

#         page = self.paginate_queryset(queryset) # Apply pagination if configured
#         if page is not None:
#             serializer = self.get_serializer(page, many=True)
#             return api_response(
#                 True,
#                 "Investor profiles listed successfully.",
#                 data=self.get_paginated_response(serializer.data).data, # Includes pagination metadata
#                 status_code=status.HTTP_200_OK
#             )

#         serializer = self.get_serializer(queryset, many=True) # Serialize all items if no pagination
#         return api_response(
#             True,
#             "Investor profiles listed successfully.",
#             data=serializer.data,
#             status_code=status.HTTP_200_OK
#         )


#     def update(self, request, *args, **kwargs):
#         with transaction.atomic():
#             partial = kwargs.pop('partial', False)
#             instance = self.get_object()
#             serializer = self.get_serializer(instance, data=request.data, partial=partial)
#             serializer.is_valid(raise_exception=True)
#             self.perform_update(serializer)

#             # Important: If prefetch_related/select_related was used on the queryset,
#             # and the underlying instance was modified, ensure the returned instance
#             # from the serializer has the latest calculated values.
#             # The instance.save() in the model will have updated these.
#             # Re-serializing the instance is usually sufficient.
#             # No explicit refresh_from_db is needed unless related objects were changed outside the ORM's knowledge.

#             return api_response(True, "Investor profile updated successfully.", data=serializer.data)

#     def destroy(self, request, *args, **kwargs):
#         with transaction.atomic():
#             instance = self.get_object()
#             self.perform_destroy(instance)
#             return api_response(True, "Investor profile deleted successfully.",data=serializer.data, status_code=status.HTTP_204_NO_CONTENT)

    
#     @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
#     def full_profile(self, request, pk=None):
#         """
#         Retrieves the investor's details along with the full User profile.
#         Accessible by admin for any investor, or by a user for their own investor profile.
#         """
#         # get_object() uses the filtered queryset, so it already handles permissions for non-admins
#         investor = self.get_object()

#         # Extra check just in case get_object() somehow returned a record not belonging to user
#         if not request.user.is_staff and investor.user != request.user:
#             return api_response(False, "You do not have permission to access this investor's profile.", status_code=status.HTTP_403_FORBIDDEN)

#         investor_data = self.get_serializer(investor).data
#         user_data = UserSerializerForInvestor(investor.user).data

#         response_data = {
#             "investor_profile": investor_data,
#             "user_details": user_data
#         }
#         return api_response(True, "Full investor profile retrieved.", data=response_data)

#     @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
#     def my_profile(self, request):
#         """
#         Allows an authenticated user to retrieve their own Investor profile.
#         """
#         # The get_queryset method already filters by request.user for non-staff
#         investor = self.get_queryset().first() # There should be at most one for a regular user

#         if not investor:
#             return api_response(False, "No investor profile found for this user.", status_code=status.HTTP_404_NOT_FOUND)

#         serializer = self.get_serializer(investor)
#         return api_response(True, "Your investor profile retrieved.", data=serializer.data)

#     # Standard ModelViewSet methods (create, update, destroy) are implicitly handled
#     # and their permissions are governed by `get_permissions()`.
#     # You only need to override them if you need custom logic for the API response
#     # or additional side effects beyond what perform_create/update/destroy offers.
