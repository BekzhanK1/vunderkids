from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.routers import SimpleRouter
from .views import *

router = SimpleRouter()
router.register(r'children', ChildrenViewSet, basename = 'children')
router.register(r'classes', ClassViewSet, basename = 'classes')

urlpatterns = [
    path('register/', UserRegistrationAPIView.as_view()),
    path('login/', MyTokenObtainPairView.as_view()),
    path('token/refresh/', TokenRefreshView.as_view()),
    path('current-user/', CurrentUserView.as_view()),
    path('', include(router.urls)),
    path('register-school/', SchoolRegistrationAPIView.as_view(), name='register-school')
]