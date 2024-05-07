from django.contrib import admin
from .models import League, Task, TaskResponse

# Register your models here.
admin.site.register(League)
admin.site.register(Task)
admin.site.register(TaskResponse)

