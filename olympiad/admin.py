from django.contrib import admin

from .models import Olympiad, OlympiadAnswer, OlympiadQuestion

admin.site.register(Olympiad)
admin.site.register(OlympiadQuestion)
admin.site.register(OlympiadAnswer)
