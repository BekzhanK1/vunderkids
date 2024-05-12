from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.routers import SimpleRouter
from .views import *

router = SimpleRouter()
router.register(r'children', ChildrenViewSet, basename = 'children')
router.register(r'classes', ClassViewSet, basename = 'classes')
router.register(r'students', StudentViewSet, basename='students')
router.register(r'rating', StudentRatingViewSet, basename='rating')

urlpatterns = [
    # path('register/', UserRegistrationAPIView.as_view()),
    path('login/', MyTokenObtainPairView.as_view()),
    path('token/refresh/', TokenRefreshView.as_view()),
    path('current-user/', CurrentUserView.as_view()),
    path('', include(router.urls)),
    path('register-school/', SchoolRegistrationAPIView.as_view(), name='register-school'),
    path('register-teacher/', TeacherRegistrationAPIView.as_view(), name='register-teacher'),
    path('register-student/', StudentRegistrationAPIView.as_view(), name='register-student'),
    path('register-parent/', ParentRegistrationAPIView.as_view(), name='register-parent'),
    path('activate/<uuid:token>/', ActivateAccount.as_view(), name='activate_account'),
    path('change-password/', ChangePassword.as_view(), name="change-password"),
    path('reset-password/', RequestResetPassword.as_view(), name='request-reset-password'),
    path('reset-password/<uuid:token>/', ResetPassword.as_view(), name='reset-password'),
]
