from django.contrib.auth.backends import BaseBackend
from .models import Usuario
from django.contrib.auth.hashers import check_password

class EmailOrCPFBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None):
        try:
            user = Usuario.objects.get(email=username)
        except Usuario.DoesNotExist:
            try:
                user = Usuario.objects.get(cpf=username)
            except Usuario.DoesNotExist:
                return None

        if check_password(password, user.senha):
            return user
        return None

    def get_user(self, user_id):
        try:
            return Usuario.objects.get(pk=user_id)
        except Usuario.DoesNotExist:
            return None
