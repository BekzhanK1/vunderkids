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

# class UserRegistrationAPIView(APIView):
#     def post(self, request):
#         serializer = UserRegistrationSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response({"message": f"User registered successfully. Please check your email to activate your account. Email: {user.email}"}, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class ActivateAccount(APIView):
    def get(self, request, token):
        try:
            user = User.objects.get(activation_token=token)
            user.is_active = True
            user.activation_token = None  # Clear token after activation
            user.save()
            return Response('Your account has been activated successfully!', status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response('Invalid activation link!', status=status.HTTP_400_BAD_REQUEST)

class ParentRegistrationAPIView(APIView):
    def post(self, request):
        data = request.data
        serializer = ParentRegistrationSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": f"Activation email have been sent to {data['email']}"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class SchoolRegistrationAPIView(APIView):
    permission_classes = [IsSuperUser]
    def post(self, request):
        data = request.data
        serializer = SchoolRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": f"Activation email have been sent to {data['email']}"}, status=status.HTTP_201_CREATED)
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
    permission_classes = [IsTeacher | IsPrincipal]
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
        action_permissions = {
            'create': [IsPrincipal],
            'destroy': [IsPrincipal],
            'class_students': [IsTeacher | IsPrincipal],
            'specific_student': [IsTeacher | IsPrincipal],
            'assign_teacher': [IsPrincipal],
            'deassign_teacher': [IsPrincipal],
            'add_student': [IsPrincipal |IsTeacher],
            'remove_student': [IsPrincipal | IsTeacher],
            'my_class': [IsStudent],
            'my_class_students': [IsStudent],
            'my_class_specific_student': [IsStudent]
        }
        permission_classes = action_permissions.get(self.action, [IsTeacher])
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_principal():
            school = get_object_or_404(School, user = user)
            return Class.objects.filter(school = school)
        elif user.is_teacher():
            teacher = get_object_or_404(Teacher, user = user)
            return Class.objects.filter(school = teacher.school, teacher = teacher)
    
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
    
    @action(detail=True, methods=['patch'], url_path='assign_teacher/(?P<teacher_id>\d+)')
    def assign_teacher(self, request, pk=None, teacher_id=None):
        """Assigns a teacher to a class."""
        school_class = self.get_object()
        teacher = get_object_or_404(Teacher, pk=teacher_id, school=school_class.school)

        if school_class.teacher:
            return Response({'error': 'Class already has a teacher assigned.'}, status=status.HTTP_400_BAD_REQUEST)

        school_class.teacher = teacher
        school_class.save()
        return Response({'message': 'Teacher assigned successfully.'})
    
    @action(detail=True, methods=['patch'], url_path='deassign_teacher')
    def deassign_teacher(self, request, pk=None):
        """Deassigns the teacher from a class, given the teacher's ID."""
        school_class = self.get_object()
        if not school_class.teacher:
            return Response({'error': 'No teacher is assigned to this class.'}, status=status.HTTP_400_BAD_REQUEST)

        school_class.teacher = None
        school_class.save()
        return Response({'message': 'Teacher deassigned successfully.'})
    
    @action(detail=True, methods=['patch'], url_path='add_student/(?P<student_id>\d+)')
    def add_student(self, request, pk=None, student_id=None):
        """Adds a student to a class."""
        school_class = self.get_object()
        student = get_object_or_404(Student, pk=student_id, school=school_class.school)

        if student.school_class:
            return Response({'error': 'Student is already assigned to a class.'}, status=status.HTTP_400_BAD_REQUEST)

        student.school_class = school_class
        student.save()
        return Response({'message': 'Student added successfully.'})
    
    @action(detail=True, methods=['patch'], url_path='remove_student/(?P<student_id>\d+)')
    def remove_student(self, request, pk=None, student_id=None):
        """Removes a student from a class, given the student's ID."""
        school_class = self.get_object()
        student = get_object_or_404(Student, pk=student_id, school_class=school_class)

        student.school_class = None
        student.save()
        return Response({'message': 'Student removed successfully.'})
    
    @action(detail=True, methods=['get'], url_path='students')
    def class_students(self, request, pk=None):
        """
        Retrieve a list of students for a specific class.
        """
        school_class = self.get_object()
        
        students = Student.objects.filter(school_class=school_class).order_by('-xp').values()
        serializer = StudentSerializer(students, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='students/(?P<student_id>\d+)')
    def specific_student(self, request, pk=None, student_id=None):
        """
        Retrieve details for a specific student within a class.
        """
        school_class = self.get_object()

        student = get_object_or_404(Student, pk=student_id, school_class=school_class)

        serializer = StudentSerializer(student)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail = False, methods=['get'])
    def my_class(self, request):
        """
        Retrive info about student's class
        """
        user = request.user
        student = get_object_or_404(Student, user = user)
        school_class = student.school_class
        serializer = self.serializer_class(school_class)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail = False, methods=['get'], url_path='classmates')
    def my_class_students(self, request):
        """
        Retrieve data about student's classmates
        """
        user = request.user
        student = get_object_or_404(Student, user=user)
        school_class = student.school_class
        classmates = Student.objects.filter(school=student.school, school_class=school_class).order_by('-xp')
        serializer = StudentSerializer(classmates, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail = False, methods=['get'], url_path='classmates/(?P<student_id>\d+)')
    def my_class_specific_student(self, request, student_id=None):
        """
        Retrieve data about student's specific classmate
        """
        user = request.user
        student = get_object_or_404(Student, user=user)
        school_class = student.school_class
        classmate = get_object_or_404(Student, school = student.school, school_class = school_class, pk = student_id)
        serializer = StudentSerializer(classmate)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
        
    
    
class StudentViewSet(viewsets.ModelViewSet):
    serializer_class = StudentSerializer
    permission_classes = [IsPrincipal | IsTeacher]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_principal():
            school = get_object_or_404(School, user = user)
            return Student.objects.filter(school = school)
        elif user.is_teacher():
            teacher = get_object_or_404(Teacher, user = user)
            school_class = get_object_or_404(Class, teacher = teacher)
            return Student.objects.filter(school_class = school_class)
        
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many = True)
        return Response(serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        school_class = get_object_or_404(queryset, pk = kwargs['pk'])
        serializer = self.serializer_class(school_class)
        return Response(serializer.data)
        

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
        child = get_object_or_404(queryset, pk=kwargs['pk'])
        data = request.data.copy()
        data.pop('parent', None)
        serializer = self.serializer_class(child, data=data, partial=True)
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