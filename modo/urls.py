from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TestViewSet, QuestionViewSet, ContentViewSet, AnswerOptionViewSet

router = DefaultRouter()
router.register(r"tests", TestViewSet)
router.register(r"questions", QuestionViewSet)
router.register(r"contents", ContentViewSet)
router.register(r"answer-options", AnswerOptionViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
