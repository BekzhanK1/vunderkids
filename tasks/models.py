from django.db import models
from django.contrib.auth import get_user_model
from account.models import Child

User = get_user_model()

class Course(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    grade = models.IntegerField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} ({self.grade} Класс)"

class Section(models.Model):
    course = models.ForeignKey(Course, related_name='sections', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()

    def __str__(self):
        return self.title


class Lesson(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    section = models.ForeignKey(Section, related_name='lessons', on_delete=models.CASCADE)

    def __str__(self):
        return f"[Section {self.section}] {self.title}"
class Content(models.Model):
    CONTENT_TYPE_CHOICES = [
        ('video', 'Video'),
        ('text', 'Text'),
        ('file', 'File'),
    ]
    lesson = models.ForeignKey(Lesson, related_name='contents', on_delete=models.CASCADE)
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPE_CHOICES)
    content = models.TextField()
    file = models.FileField(blank=True, null=True, upload_to='files/')

    def __str__(self):
        return f'{self.content_type}: {self.content[:30]}'

class Task(models.Model):
    section = models.ForeignKey(Section, related_name='tasks', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()

    def __str__(self):
        return self.title

class Question(models.Model):
    task = models.ForeignKey(Task, related_name='questions', on_delete=models.CASCADE)
    question_text = models.TextField()
    question_type = models.CharField(max_length=50, choices=[
        ('multiple_choice', 'Multiple Choice'),
        ('drag_and_drop', 'Drag and Drop'),
        ('true_false', 'True or False'),
    ])
    options = models.JSONField(blank=True, null=True)
    correct_answer = models.TextField()

    def __str__(self):
        return f"[Task: {self.task}] {self.question_text}"


class Answer(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, related_name='answers', on_delete=models.CASCADE)
    child = models.ForeignKey(Child, null=True, blank=True, related_name='answers', on_delete=models.CASCADE)
    question = models.ForeignKey(Question, related_name='answers', on_delete=models.CASCADE)
    answer = models.TextField()
    is_correct = models.BooleanField()

    def __str__(self):
        return f"{self.user} - {self.question}"

class TaskCompletion(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, related_name='completed_tasks', on_delete=models.CASCADE)
    child = models.ForeignKey(Child, null=True, blank=True, related_name='completed_tasks', on_delete=models.CASCADE)
    task = models.ForeignKey(Task, related_name='completed_by', on_delete=models.CASCADE)
    completed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.user:
            return f"{self.user} - {self.task}"
        if self.child:
            return f"{self.child} - {self.task}"