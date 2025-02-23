from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (PlanViewSet, SubscriptionViewSet, initiate_payment,
                    payment_confirmation)

router = DefaultRouter()
router.register(r"plans", PlanViewSet, basename="plan")
router.register(r"subscriptions", SubscriptionViewSet, basename="subscription")

urlpatterns = [
    path("", include(router.urls)),
    path("payments/initiate-payment/", initiate_payment),
    path("payments/payment-confirmation/", payment_confirmation),
]
