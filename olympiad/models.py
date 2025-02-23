from datetime import timezone

from django.db import models

from account.models import GRADE_CHOICES, LANGUAGE_CHOICES, Child, User


# Create your models here.
class Olympiad(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    language = models.CharField(max_length=50, choices=LANGUAGE_CHOICES, default="ru")
    price = models.DecimalField(max_digits=7, decimal_places=0)
    start_date = models.DateTimeField()
    grade = models.IntegerField(choices=GRADE_CHOICES, null=True)
    end_date = models.DateTimeField()
    is_for_teachers = models.BooleanField(default=False)
    is_displayed = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_active(self):
        return self.start_date < timezone.now() < self.end_date

    def __str__(self):
        return self.name


class OlympiadQuestion(models.Model):
    olympiad = models.ForeignKey(
        Olympiad, on_delete=models.CASCADE, related_name="questions"
    )
    question_text = models.TextField()
    options = models.JSONField()
    correct_answer = models.JSONField()
    template = models.CharField(default="1", max_length=20, blank=True, null=True)
    audio = models.FileField(upload_to="audio/", blank=True, null=True)

    def __str__(self):
        return self.question[:30]


class OlympiadAnswer(models.Model):
    user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        related_name="olympiad_answers",
        on_delete=models.CASCADE,
    )
    child = models.ForeignKey(
        Child,
        null=True,
        blank=True,
        related_name="olympiad_answers",
        on_delete=models.CASCADE,
    )
    question = models.ForeignKey(
        OlympiadQuestion, related_name="answers", on_delete=models.CASCADE
    )
    answer = models.TextField()
    is_correct = models.BooleanField()

    class Meta:
        unique_together = (("user", "question"), ("child", "question"))

    def __str__(self):
        return f"{self.user} - {self.question}"
