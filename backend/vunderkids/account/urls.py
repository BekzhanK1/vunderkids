from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.routers import SimpleRouter
from .views import UserRegistrationAPIView, MyTokenObtainPairView, CurrentUserView, ChildrenViewSet

router = SimpleRouter()
router.register(r'children', ChildrenViewSet, basename = 'children')

urlpatterns = [
    path('register/', UserRegistrationAPIView.as_view()),
    path('login/', MyTokenObtainPairView.as_view()),
    path('token/refresh/', TokenRefreshView.as_view()),
    path('current-user/', CurrentUserView.as_view()),
    path('', include(router.urls)),
]
