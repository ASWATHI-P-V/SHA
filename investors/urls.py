# SHA_GROUP/investors/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InvestorViewSet, InvestmentServiceGroupViewSet, InterestRateSettingViewSet

router = DefaultRouter()
router.register(r'investors', InvestorViewSet)
router.register(r'service-groups', InvestmentServiceGroupViewSet)
router.register(r'interest-rates', InterestRateSettingViewSet)

urlpatterns = [
    # API endpoints for investor-related data (handled by router)
    path('api/', include(router.urls)),
]