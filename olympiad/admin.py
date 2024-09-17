from django.contrib import admin
from .models import Olympiad, OlympiadQuestion, OlympiadAnswer

admin.site.register(Olympiad)
admin.site.register(OlympiadQuestion)
admin.site.register(OlympiadAnswer)
