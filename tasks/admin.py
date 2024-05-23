from django.contrib import admin
from .models import Course, Section, Lesson, Content, Task, Question, Answer, TaskCompletion

# Register your models here.
admin.site.register(Course)
admin.site.register(Section)
admin.site.register(Lesson)
admin.site.register(Content)
admin.site.register(Task)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(TaskCompletion)
