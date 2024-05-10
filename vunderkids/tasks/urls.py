from django.urls import path, include
from .views import TaskViewSet, TestingView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'tasks', TaskViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('test/', TestingView.as_view()),

]