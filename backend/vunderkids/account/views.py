from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics, permissions, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from django.shortcuts import get_object_or_404
from account.serializers import *
from account.models import *
from account.permissions import *

class UserRegistrationAPIView(APIView):
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User registered successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class SchoolRegistrationAPIView(APIView):
    permission_classes = [IsSuperUser]
    def post(self, request):
        serializer = SchoolRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "School registered successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
class ClassViewSet(viewsets.ModelViewSet):
    permission_classes = [IsPrincipal]
    serializer_class = ClassSerializer
    def get_queryset(self):
        principal = self.request.user
        school = get_object_or_404(School, user = principal)
        return Class.objects.filter(school = school)
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many = True)
        return Response(serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        school_class = get_object_or_404(queryset, pk = kwargs['pk'])
        serializer = self.serializer_class(school_class)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        principal = request.user
        school = get_object_or_404(School, user = principal)
        data = request.data
        data['school'] = school.pk
        serializer = self.serializer_class(data=data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def partial_update(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        school_class = get_object_or_404(queryset, pk = kwargs['pk'])
        data = request.data.copy()
        data.pop('school', None)
        serializer = self.serializer_class(school_class, data = data, partial = True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        school_class = get_object_or_404(queryset, pk = kwargs['pk'])
        self.perform_destroy(school_class)
        return Response(status=status.HTTP_204_NO_CONTENT)
        

class ChildrenViewSet(viewsets.ModelViewSet):
    serializer_class = ChildSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        parent = self.request.user
        return Child.objects.filter(parent = parent)
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many = True)
        return Response(serializer.data)
        
    def retrieve(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        child = get_object_or_404(queryset, pk = kwargs['pk'])
        serializer = self.serializer_class(child)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        data = request.data
        parent = request.user
        data['parent'] = parent.pk
        serializer = self.serializer_class(data = data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
    def partial_update(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        child = get_object_or_404(queryset, pk = kwargs['pk'])
        data = request.data.copy()
        data.pop('parent', None)
        serializer = self.serializer_class(child, data = data, partial = True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        child = get_object_or_404(queryset, pk = kwargs['pk'])
        self.perform_destroy(child)
        return Response(status=status.HTTP_204_NO_CONTENT)
       
    
        

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer
    
class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)