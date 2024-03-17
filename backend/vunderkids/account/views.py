from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics, permissions, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.decorators import action
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
    
class ParentRegistrationAPIView(APIView):
    def post(self, request):
        serializer = ParentRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Parent registered successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class SchoolRegistrationAPIView(APIView):
    permission_classes = [IsSuperUser]
    def post(self, request):
        serializer = SchoolRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "School registered successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class TeacherRegistrationAPIView(APIView):
    permission_classes = [IsPrincipal]
    def post(self, request):
        school = get_object_or_404(School, user=request.user)
        serializer = TeacherRegistrationSerializer(data={**request.data, "school": school.pk})
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Teacher registered successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class StudentRegistrationAPIView(APIView):
    permission_classes = [IsTeacher]
    def post(self, request):
        user = request.user
        if user.is_principal():
            school = get_object_or_404(School, user=request.user)
        elif user.is_teacher():
            teacher = get_object_or_404(Teacher, user=request.user)
            school = teacher.school
        serializer = StudentRegistrationSerializer(data={**request.data, "school": school.pk})
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Student registered successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
    
class ClassViewSet(viewsets.ModelViewSet):
    serializer_class = ClassSerializer
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['create', 'destroy']:
            permission_classes = [IsPrincipal]
        else:
            permission_classes = [IsTeacher]
        return [permission() for permission in permission_classes]
    
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
    
    @action(detail=True, methods=['patch'], permission_classes=[IsPrincipal])
    def assign_teacher(self, request, pk=None):
        school_class = self.get_object()
        teacher_id = request.data.get('teacher_id')
        teacher = get_object_or_404(Teacher, pk=teacher_id, school=school_class.school)  # Ensure teacher belongs to the same school

        school_class.teacher = teacher
        school_class.save()
        return Response({'message': 'Teacher assigned successfully'}, status=status.HTTP_200_OK)

    
    @action(detail=True, methods=['patch'], permission_classes=[IsTeacher])
    def add_student(self, request, pk=None):
        user = request.user

        if user.is_teacher():
            teacher = get_object_or_404(Teacher, user = user)
            school_class = get_object_or_404(Class, pk = pk, teacher = teacher)
        else:
            school_class = get_object_or_404(Class, pk = pk)
        student_id = request.data.get('student_id')
        student = get_object_or_404(Student, pk=student_id, school=school_class.school)  # Ensure student is part of the same school

        # Optionally check if the student is already in another class and handle according to your business logic

        student.school_class = school_class
        student.save()
        return Response({'message': 'Student added successfully'}, status=status.HTTP_200_OK)

class ChildrenViewSet(viewsets.ModelViewSet):
    serializer_class = ChildSerializer
    permission_classes = [IsParent]
    
    def get_queryset(self):
        parent = Parent.objects.get(user = self.request.user)
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
        parent = Parent.objects.get(user = request.user)
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