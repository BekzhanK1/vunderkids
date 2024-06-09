from django.db import models
from django.contrib.auth import get_user_model
from account.models import Child

User = get_user_model()

class Course(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    grade = models.IntegerField(db_index=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} ({self.grade} Класс)"

class Section(models.Model):
    course = models.ForeignKey(Course, related_name='sections', on_delete=models.CASCADE, db_index=True)
    title = models.CharField(max_length=255)
    description = models.TextField()

    def __str__(self):
        return self.title

class Content(models.Model):
    CONTENT_TYPE_CHOICES = (
        ('task', 'Task'),
        ('lesson', 'Lesson'),
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    order = models.IntegerField(default=0)
    section = models.ForeignKey(Section, related_name='contents', null=True, on_delete=models.CASCADE, db_index=True)
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPE_CHOICES)

    def __str__(self):
        return f"Content: (Section: {self.section.title} | Order: {self.order})"

class Lesson(Content):
    video_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"Lesson: {self.title}"

class Task(Content):
    def __str__(self):
        return f"Task: {self.title}"

class Question(models.Model):
    QUESTION_TYPES = [
        ('multiple_choice_text', 'Multiple Choice Text'),
        ('multiple_choice_images', 'Multiple Choice Images'),
        ('drag_and_drop', 'Drag and Drop'),
        ('true_false', 'True or False'),
        ('mark_all', 'Mark All That Apply'),
        ('number_line', 'Number Line'),
        ('drag_position', 'Drag Position'),
    ]
    task = models.ForeignKey(Task, related_name='questions', on_delete=models.CASCADE, db_index=True)
    question_text = models.TextField()
    question_type = models.CharField(max_length=50, choices=QUESTION_TYPES)
    options = models.JSONField(blank=True, null=True)  # For multiple choice, mark all, drag and drop
    correct_answer = models.JSONField()  # Adjusted to JSONField to store complex answers if needed

    def __str__(self):
        return f"[Task: {self.task}] {self.question_text}"

class Answer(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, related_name='answers', on_delete=models.CASCADE, db_index=True)
    child = models.ForeignKey(Child, null=True, blank=True, related_name='answers', on_delete=models.CASCADE, db_index=True)
    question = models.ForeignKey(Question, related_name='answers', on_delete=models.CASCADE)
    answer = models.TextField()
    is_correct = models.BooleanField()

    def __str__(self):
        return f"{self.user} - {self.question}"

class TaskCompletion(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, related_name='completed_tasks', on_delete=models.CASCADE, db_index=True)
    child = models.ForeignKey(Child, null=True, blank=True, related_name='completed_tasks', on_delete=models.CASCADE, db_index=True)
    task = models.ForeignKey(Task, related_name='completed_by', on_delete=models.CASCADE, db_index=True)
    completed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.user:
            return f"{self.user} - {self.task}"
        if self.child:
            return f"{self.child} - {self.task}"
