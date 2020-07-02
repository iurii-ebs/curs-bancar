from django.contrib.auth.models import User

from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .serializers import UserRegisterSerializer


class RegisterView(GenericAPIView):
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny]

    @staticmethod
    def post(request):
        serializer = UserRegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            data = {
                'success': f'User {user.username} was created'
            }
        else:
            data = {
                'error': serializer.errors
            }

        return Response(data)
