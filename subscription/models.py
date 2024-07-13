from django.db import models
from datetime import timedelta
from django.utils import timezone  # Corrected import
from account.models import User

class Plan(models.Model):
    price = models.DecimalField(max_digits=10, decimal_places=0)
    duration = models.CharField(max_length=10, choices=[
        ('free_trial', 'Free Trial'),
        ('monthly', 'Monthly'),
        ('annual', 'Annual'),
    ], unique=True)
    is_enabled = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if self.duration == 'free_trial':
            self.price = 0
        elif self.duration == 'monthly':
            self.price = 1000
        elif self.duration == 'annual':
            self.price = 10000
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.get_duration_display()} Plan"  # Corrected string representation


class Subscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='subscriptions')
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.end_date:
            if self.plan.duration == 'free_trial':
                self.end_date = self.start_date + timedelta(days=7)
            elif self.plan.duration == 'monthly':
                self.end_date = self.start_date + timedelta(days=30)
            elif self.plan.duration == 'annual':
                self.end_date = self.start_date + timedelta(days=365)
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        return timezone.now() < self.end_date

    def __str__(self):
        return f"{self.user.email} - {self.plan.duration} Plan (Expires: {self.end_date})"
