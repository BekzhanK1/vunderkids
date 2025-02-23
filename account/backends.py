from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model


class UsernameBackend(ModelBackend):
    """
    Custom authentication backend that allows users to log in only with their username.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(username=username)
        except UserModel.DoesNotExist:
            return None
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        return None
