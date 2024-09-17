from django.urls import path
from rest_framework_nested import routers

from .views import OlympiadViewSet

router = routers.DefaultRouter()
router.register(r"olympiads", OlympiadViewSet)

urlpatterns = []
urlpatterns += router.urls
