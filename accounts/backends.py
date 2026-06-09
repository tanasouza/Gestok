from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

class MatriculaBackend(ModelBackend):
    """
    Custom authentication backend that authenticates users using their 'matricula'
    and checks if they are active (ativo=True).
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()

        # If 'username' is not provided, check in kwargs
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)

        try:
            # Authenticate only active users
            user = UserModel._default_manager.get(matricula=username, ativo=True)
        except UserModel.DoesNotExist:
            # Run the password hasher once to reduce timing vulnerability
            UserModel().set_password(password)
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None
