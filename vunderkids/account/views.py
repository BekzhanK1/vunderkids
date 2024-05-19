from rest_framework import status, viewsets, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate
from account.serializers import *
from account.models import *
from account.permissions import *
from .tasks import send_password_reset_request_email
import uuid

class ActivateAccount(APIView):
    def get(self, request, token):
        try:
            user = User.objects.get(activation_token=token)
            user.is_active = True
            user.activation_token = None
            user.save()
            return Response('Your account has been activated successfully!', status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response('Invalid activation link!', status=status.HTTP_400_BAD_REQUEST)

class ChangePassword(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user = request.user
        data = request.data
        current_password = data['current_password']
        new_password = data['new_password']
        auth_user = authenticate(email=user.email, password=current_password)
        if auth_user:
            try:
                auth_user.set_password(new_password)
                auth_user.save()
            except Exception("Couldn't change password"):
                return Response({"message": "Error during password change"}, status=status.HTTP_400_BAD_REQUEST)
        else: 
            return Response({"message": "Current password is incorrect"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "Successfully changed password"}, status=status.HTTP_200_OK)

class RequestResetPassword(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        data = request.data
        if 'email' in data:
            email = data['email']
            user = get_object_or_404(User, email=email)
            user.activation_token = uuid.uuid4()
            user.save()
            send_password_reset_request_email.delay(user.pk)
            return Response({"message": "Request has been sent to email"}, status=status.HTTP_201_CREATED)
        else:
            return Response({"message": "You need to enter the email to reset password"}, status=status.HTTP_400_BAD_REQUEST)

class ResetPassword(APIView):
    permission_classes = [AllowAny]
    def post(self, request, token):
        try:
            data = request.data
            password = data['password']
            user = User.objects.get(activation_token=token)
            user.set_password(password)
            user.save()
            return Response({"message": "Successfully resseted password"}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response('Invalid reset link!', status=status.HTTP_400_BAD_REQUEST)

class StaffRegistrationAPIView(APIView):
    permission_classes = [IsSuperUser]
    def post(self, request):
        data = request.data
        data['role'] = 'staff'
        serializer = StaffRegistrationSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Staff user is registered successfully"})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ParentRegistrationAPIView(APIView):
    def post(self, request):
        data = request.data
        serializer = ParentRegistrationSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": f"Activation email have been sent to {data['email']}"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SchoolRegistrationAPIView(APIView):
    permission_classes = [IsSuperUser | IsStaff]
    def post(self, request):
        serializer = SchoolSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Successfully created school"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SchoolViewSet(viewsets.ModelViewSet):
    queryset = School.objects.all()
    serializer_class = SchoolSerializer
    permission_classes = [IsSuperUser | IsStaff]

class ClassViewSet(viewsets.ModelViewSet):
    serializer_class = ClassSerializer
    permission_classes = [IsSuperUser | IsStaff]

    def get_queryset(self):
        return Class.objects.filter(school_id=self.kwargs['school_pk'])
    

    def create(self, request, *args, **kwargs):
        school_id = self.kwargs['school_pk']
        data = request.data.copy()
        data['school'] = school_id

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    


class StudentViewSet(viewsets.ModelViewSet):
    serializer_class = StudentSerializer
    permission_classes = [IsSuperUser | IsStaff]

    def get_queryset(self):
        return Student.objects.filter(school_class_id=self.kwargs['class_pk'])
    

    @action(detail=False, methods=['post'], url_path='register_student')
    def register_student(self, request, *args, **kwargs):
        school_id = self.kwargs['school_pk']
        class_id = self.kwargs['class_pk']
        data = request.data.copy()
        data['school'] = school_id
        data['school_class'] = class_id

        serializer = StudentRegistrationSerializer(data=data)
        if serializer.is_valid():
            student = serializer.save()
            return Response({
                "message": f"Activation email have been sent to {data['email']}",
                "student_id": student.pk
            }, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class ChildrenViewSet(viewsets.ModelViewSet):
    serializer_class = ChildSerializer
    permission_classes = [IsParent]

    def get_queryset(self):
        parent = Parent.objects.get(user=self.request.user)
        return Child.objects.filter(parent=parent)

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
