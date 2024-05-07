from django.db import models

class League(models.Model):
    name = models.CharField(max_length=100)
    min_xp = models.PositiveIntegerField()
    max_xp = models.PositiveIntegerField()  # Add this to handle upper limits

    def __str__(self):
        return f"{self.name} | XP Range: {self.min_xp}-{self.max_xp}"
    

from django.db import models
import json

class Task(models.Model):
    TASK_TYPES = [
        ('MCQ', 'Multiple-Choice Questions'),
        ('DD', 'Drag and Drop'),
        ('FIB', 'Fill-in-the-Blanks'),
        ('TF', 'True or False'),
        ('SA', 'Short Answer'),
        ('SO', 'Sorting and Ordering'),
    ]


    XP_CHOICES = [
        (10, '10 XP'),
        (20, '20 XP'),
        (30, '30 XP'),
        (40, '40 XP'),
        (50, '50 XP'),
    ]

    title = models.CharField(max_length=255)
    task_type = models.CharField(max_length=3, choices=TASK_TYPES)
    description = models.TextField()
    xp_reward = models.PositiveIntegerField(choices=XP_CHOICES)
    data = models.TextField(help_text="Stores task-specific data in JSON format")

    def __str__(self):
        return f"{self.title} ({self.get_task_type_display()})"

    def save(self, *args, **kwargs):
        if isinstance(self.data, dict):
            self.data = json.dumps(self.data)
        super().save(*args, **kwargs)

    @property
    def data_dict(self):
        return json.loads(self.data)
    



    

class TaskResponse(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='responses')
    student = models.ForeignKey('account.Student', on_delete=models.CASCADE, related_name='task_responses', null=True, blank=True)
    child = models.ForeignKey('account.Child', on_delete=models.CASCADE, related_name='task_responses', null=True, blank=True)
    answer = models.TextField()
    response_date = models.DateTimeField(auto_now_add=True)
    is_true = models.BooleanField(blank=True, null=True, default=None)


    def __str__(self) -> str:
        return f"Task: {self.task.pk} Answer: {self.is_true}"



    def is_correct(self):
        task_data = self.task.data_dict
        if self.task.task_type == 'MCQ':
            return self.answer == task_data['answer']
        elif self.task.task_type == 'TF':
            return str(task_data['answer']).lower() == self.answer.lower()
        elif self.task.task_type in ['DD', 'SO']:
            return json.loads(self.answer) == task_data['correct_order']
        elif self.task.task_type == 'FIB':
            user_answers = json.loads(self.answer)
            return all(user_answers.get(str(key)) == val for key, val in task_data['blanks'].items())
        elif self.task.task_type == 'SA':
            return self.answer.strip().lower() == task_data['answer'].strip().lower()
        return False

    @property
    def user_type(self):
        return 'Student' if self.student else 'Child'

