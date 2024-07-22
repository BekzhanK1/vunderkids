from django.db import models
from datetime import timedelta
from django.utils import timezone
from account.models import User


DURATION_CHOICES = [
    ('free-trial', 'Free Trial'),
    ('monthly', 'Monthly'),
    ('6-month', '6 Month'),
    ('annual', 'Annual'),
]

class Plan(models.Model):
    price = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    duration = models.CharField(max_length=10, choices=DURATION_CHOICES, unique=True)
    is_enabled = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if self.duration == 'monthly':
            self.price = 1000
        elif self.duration == 'annual':
            self.price = 10000
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.get_duration_display()} Plan"


class Subscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='subscriptions')
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.start_date:
            self.start_date = timezone.now()

        if not self.end_date:
            if self.plan.duration == 'monthly':
                self.end_date = self.start_date + timedelta(days=30)
            elif self.plan.duration == '6-month':
                self.end_date = self.start_date + timedelta(days=180)
            elif self.plan.duration == 'annual':
                self.end_date = self.start_date + timedelta(days=365)
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        if self.plan.duration == "free-trial":
            if self.user.is_parent:
                if self.user.parent.children.count() == 0:
                    return True
                for child in self.user.parent.children.all():
                    if child.completed_tasks.count() > 9:  # 10 is the maximum number of tasks to complete
                        return False
                return True
        return self.end_date is not None and timezone.now() < self.end_date

    def __str__(self):
        return f"{self.user.email} - {self.plan.duration} Plan (Expires: {self.end_date})"
