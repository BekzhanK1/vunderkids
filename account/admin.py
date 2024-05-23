from django.contrib import admin
from account.models import *

# Register your models here.
admin.site.register(User)
admin.site.register(Child)
admin.site.register(Parent)
admin.site.register(School)
admin.site.register(Student)
admin.site.register(Class)
admin.site.register(LevelRequirement)