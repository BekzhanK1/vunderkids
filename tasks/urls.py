from django.urls import path
from rest_framework_nested import routers
from .views import CourseViewSet, PlayGameView, SectionViewSet, LessonViewSet, ContentViewSet, TaskViewSet, QuestionViewSet

router = routers.DefaultRouter()
router.register(r'courses', CourseViewSet)

courses_router = routers.NestedSimpleRouter(router, r'courses', lookup='course')
courses_router.register(r'sections', SectionViewSet, basename='course-sections')

sections_router = routers.NestedSimpleRouter(courses_router, r'sections', lookup='section')
sections_router.register(r'contents', ContentViewSet, basename='section-contents')
sections_router.register(r'lessons', LessonViewSet, basename='section-lessons')
sections_router.register(r'tasks', TaskViewSet, basename='section-tasks')

tasks_router = routers.NestedSimpleRouter(sections_router, r'tasks', lookup='task')
tasks_router.register(r'questions', QuestionViewSet, basename='task-questions')


urlpatterns = [
    path('play-game/', PlayGameView.as_view(), name='play-game'),
]

urlpatterns += router.urls + courses_router.urls + sections_router.urls + tasks_router.urls

