from rest_framework.exceptions import PermissionDenied
from django.utils import timezone

class SubscriptionMixin:
    def check_subscription(self, user, child=None):
        if user.is_student or user.is_parent:
            if not user.subscription.filter(end_date__gt=timezone.now()).exists():
                raise PermissionDenied("You do not have an active subscription.")
        else:
            return True