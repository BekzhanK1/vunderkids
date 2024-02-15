from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import UserRegistrationAPIView, MyTokenObtainPairView, CurrentUserView

urlpatterns = [
    path('register/', UserRegistrationAPIView.as_view()),
    path('login/', MyTokenObtainPairView.as_view()),
    path('token/refresh/', TokenRefreshView.as_view()),
    path('current-user/', CurrentUserView.as_view()),
]
