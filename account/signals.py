from django.db.models.signals import post_delete
from django.dispatch import receiver
from account.models import Student


@receiver(post_delete, sender=Student)
def delete_user_with_student(sender, instance, **kwargs):
    """Deletes the related User when a Student is deleted."""
    if instance.user:
        instance.user.delete()
