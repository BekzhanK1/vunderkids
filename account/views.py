from rest_framework import status, viewsets, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate
from django.conf import settings
from django.core import cache
from account.serializers import *
from account.models import *
from account.permissions import *
from tasks.models import TaskCompletion
from .tasks import send_password_reset_request_email
import uuid
from datetime import timedelta, datetime

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
            staff = serializer.save()
            return Response({
                "message": "Staff user is registered successfully",
                "staff_id": staff.pk
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ParentRegistrationAPIView(APIView):
    def post(self, request):
        data = request.data
        serializer = ParentRegistrationSerializer(data=data)
        if serializer.is_valid():
            parent = serializer.save()
            return Response({
                "message": f"Вам было отправлено письмо активаций по адресу {data['email']}",
                "parent_id": parent.pk
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SchoolViewSet(viewsets.ModelViewSet):
    queryset = School.objects.all()
    serializer_class = SchoolSerializer
    permission_classes = [IsSuperUser]

    def create(self, request, *args, **kwargs):
        serializer = SchoolSerializer(data=request.data)
        if serializer.is_valid():
            school = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

    @action(detail=True, methods=['post'])
    def assign_supervisor(self, request, pk=None):
        school = self.get_object()

        if school.supervisor:
            return Response({"message": "School already has a supervisor"}, status=status.HTTP_400_BAD_REQUEST)
        
        data = request.data.copy()


        serializer = SupervisorRegistrationSerializer(data=data)
        if serializer.is_valid():
            supervisor = serializer.save()
            school.supervisor = supervisor
            school.save()
            return Response({
                "message": "Staff user is registered successfully",
                "supervisor_id": supervisor.pk
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def deassign_supervisor(self, request, pk=None):
        school = self.get_object()
        if school.supervisor is None:
            return Response({"message": "School doesn't have a supervisor"}, status=status.HTTP_400_BAD_REQUEST)
        
        supervisor = school.supervisor
        supervisor.delete()
        school.supervisor = None
        school.save()
        return Response({"message": "Supervisor has been deleted from the school"}, status=status.HTTP_200_OK)



class SupervisorSchoolViewset(viewsets.ReadOnlyModelViewSet):
    queryset = School.objects.all()
    permission_classes = [IsSupervisor]
    serializer_class = SchoolSerializer

    def get_queryset(self):
        return School.objects.filter(supervisor=self.request.user)
    
    @action(detail=False, methods=['get'], url_path='school')
    def my_school(self, request):
        school = get_object_or_404(School, supervisor=request.user)
        serializer = SchoolSerializer(school)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='classes')
    def my_classes(self, request):
        school = get_object_or_404(School, supervisor=request.user)
        classes = Class.objects.filter(school=school)
        serializer = ClassSerializer(classes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='classes/(?P<class_pk>[^/.]+)')
    def my_class(self, request, pk=None, class_pk=None):
        school = get_object_or_404(School, supervisor=request.user)
        school_class = get_object_or_404(Class, pk=class_pk, school=school)
        serializer = ClassSerializer(school_class)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='classes/(?P<class_pk>[^/.]+)/students')
    def students_of_class(self, request, class_pk=None):
        school = get_object_or_404(School, supervisor=request.user)
        school_class = get_object_or_404(Class, pk=class_pk, school=school)
        students = Student.objects.filter(school_class=school_class).order_by('-cups')
        serializer = StudentSerializer(students, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='students/(?P<student_pk>[^/.]+)')
    def student_of_class(self, request, class_pk=None, student_pk=None):
        school = get_object_or_404(School, supervisor=request.user)
        student = get_object_or_404(Student, pk=student_pk, school=school)
        serializer = StudentSerializer(student)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='students/(?P<student_pk>[^/.]+)/progress')
    def student_progress(self, request, student_pk=None):
        student = get_object_or_404(Student, pk=student_pk)
        
        today = timezone.now().date()
        start_date = today - timedelta(days=6)

        task_completions = TaskCompletion.objects.filter(user=student.user, completed_at__date__gte=start_date, completed_at__date__lte=today)
        daily_progress = {str(start_date + timedelta(days=i)): 0 for i in range(7)}
        
        for task_completion in task_completions:
            day = str(task_completion.completed_at.date())
            if day in daily_progress:
                correct_questions_number = task_completion.correct
                daily_progress[day] += correct_questions_number * settings.QUESTION_REWARD
        
        date_to_day = {
            (start_date + timedelta(days=i)): (start_date + timedelta(days=i)).strftime('%A')
            for i in range(7)
        }
        
        response_data = {
            "weekly_progress": [
                {"day": date_to_day[datetime.strptime(date, "%Y-%m-%d").date()], "cups": cups}
                for date, cups in daily_progress.items()
            ]
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


    @action(detail=False, methods=['get'], url_path='top-students')
    def top_students(self, request):
        school = get_object_or_404(School, supervisor=request.user)
        top_students = Student.objects.filter(school=school).order_by('-cups')[:10]
        serializer = StudentSerializer(top_students, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
 

class ClassViewSet(viewsets.ModelViewSet):
    serializer_class = ClassSerializer
    permission_classes = [IsSuperUser]

    def get_queryset(self):
        return Class.objects.filter(school_id=self.kwargs['school_pk']).order_by("grade")
    
    def create(self, request, *args, **kwargs):
        school_id = self.kwargs['school_pk']
        data = request.data.copy()
        data['school'] = school_id

        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            school_class = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class StudentViewSet(viewsets.ModelViewSet):
    serializer_class = StudentSerializer
    permission_classes = [IsSuperUser]

    def get_queryset(self):
        return Student.objects.filter(school_class_id=self.kwargs['class_pk'])
    
    def create(self, request, *args, **kwargs):
        school_id = self.kwargs['school_pk']
        class_id = self.kwargs['class_pk']
        school_class = get_object_or_404(Class, pk = class_id)
        data = request.data.copy()
        data['school'] = school_id
        data['school_class'] = class_id
        data['grade'] = school_class.grade

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
    permission_classes = [IsParent | IsSuperUser]

    def create(self, request):
        parent = request.user.parent
        if parent.children.count() >= 3:
            return Response({"message": "You cant add more than 3 children"}, status=status.HTTP_400_BAD_REQUEST)
        data = request.data.copy()
        data['parent'] = parent.pk
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self):
        if self.request.user.is_parent:
            parent = self.request.user.parent
            return Child.objects.filter(parent=parent)
        if self.request.user.is_superuser:
            return Child.objects.all()
    


class TopStudentsView(APIView):
    permission_classes = [IsParent | IsStudent]

    def get(self, request, rating_type):
        user = request.user
        child_id = request.query_params.get('child_id', None)
        top_students = []
        current_student = None
        top_children = []
        current_child = None

        if user.is_student:
            current_student = user.student
            if rating_type == 'class':
                if current_student.school_class:
                    top_students = Student.objects.filter(school_class=current_student.school_class).order_by('-cups')[:10]
                else:
                    return Response({"detail": "Student is not assigned to any class."}, status=400)
            
            elif rating_type == 'school':
                if current_student.school:
                    top_students = Student.objects.filter(school=current_student.school).order_by('-cups')[:10]
                else:
                    return Response({"detail": "Student is not assigned to any school."}, status=400)
            
            elif rating_type == 'global':
                if current_student.grade:
                    top_students = Student.objects.filter(grade=current_student.grade).order_by('-cups')[:10]
                else:
                    return Response({"detail": "Student grade is not set."}, status=400)
            else:
                return Response({"detail": "Invalid rating type. Use 'class', 'school', or 'global'."}, status=400)

            # Check if current student is in the top_students, otherwise add them
            if current_student not in top_students:
                top_students = list(top_students)
                top_students.append(current_student)
                top_students.sort(key=lambda student: student.cups, reverse=True)
                top_students = top_students[:10]

            serializer = SimpleStudentSerializer(top_students, many=True, context={'request': request})
            return Response(serializer.data, status=200)

        elif user.is_parent and child_id:
            current_child = get_object_or_404(Child, parent=user.parent, pk=child_id)
            if rating_type == 'class' or rating_type == 'school' or rating_type == 'global':
                if current_child.grade:
                    top_children = Child.objects.filter(grade=current_child.grade).order_by('-cups')[:10]
                else:
                    return Response({"detail": "Child is not assigned to any grade."}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"detail": "Invalid rating type. Use 'global'."}, status=status.HTTP_400_BAD_REQUEST)

            # Check if current child is in the top_children, otherwise add them
            if current_child not in top_children:
                top_children = list(top_children)
                top_children.append(current_child)
                top_children.sort(key=lambda child: child.cups, reverse=True)
                top_children = top_children[:10]

            serializer = ChildSerializer(top_children, many=True, context={'request': request})
            return Response(serializer.data, status=200)
        
        return Response({"detail": "Invalid request. Parent must provide child_id."}, status=400)
    

class WeeklyProgressAPIView(APIView):
    permission_classes = [IsStudent | IsParent]
    def get(self, request):
        user = request.user
        child_id = request.query_params.get('child_id', None)

        today = timezone.now().date()
        start_date = today - timedelta(days=6)
        
        if user.is_student:
            task_completions = TaskCompletion.objects.filter(
                user=user,
                completed_at__date__gte=start_date,
                completed_at__date__lte=today
            )
        elif user.is_parent and child_id:
            parent = user.parent
            child = get_object_or_404(Child, pk=child_id, parent=parent)
            task_completions = TaskCompletion.objects.filter(
                child=child,
                completed_at__date__gte=start_date,
                completed_at__date__lte=today
            )
        else:
            return Response({"message": "Invalid request. Parent must provide child_id."}, status=status.HTTP_400_BAD_REQUEST)

        
        daily_progress = {str(start_date + timedelta(days=i)): 0 for i in range(7)}
        
        for task_completion in task_completions:
            day = str(task_completion.completed_at.date())
            if day in daily_progress:
                correct_questions_number = task_completion.correct
                daily_progress[day] += correct_questions_number * settings.QUESTION_REWARD
        
        date_to_day = {
            (start_date + timedelta(days=i)): (start_date + timedelta(days=i)).strftime('%A')
            for i in range(7)
        }
        
        response_data = {
            "weekly_progress": [
                {"day": date_to_day[datetime.strptime(date, "%Y-%m-%d").date()], "cups": cups}
                for date, cups in daily_progress.items()
            ]
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    
class AllStudentsView(APIView):
    def get(self, request, *args, **kwargs):
        students = Student.objects.all().order_by('user__first_name')
        children = Child.objects.all().order_by('first_name')
        
        student_serializer = StudentsListSerializer(students, many=True)
        child_serializer = ChildrenListSerializer(children, many=True)
        
        combined_data = student_serializer.data + child_serializer.data

        sorted_combined_data = sorted(combined_data, key=lambda x: x['first_name'])
        
        return Response(sorted_combined_data, status=status.HTTP_200_OK)
        



        

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = {}
        if request.user.is_student:
            student = Student.objects.get(user=request.user)
            tasks_completed = request.user.completed_tasks.count()
            data['user'] = {
                'id': request.user.id,
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'role': request.user.role,
                'grade': student.grade,
                'level': student.level,
                'streak': student.streak,
                'cups': student.cups,
                'stars': student.stars,
                'is_superuser': request.user.is_superuser,
                'is_staff': request.user.is_staff,
                'tasks_completed': tasks_completed
            }
        elif request.user.is_parent:
            parent = request.user.parent
            children = Child.objects.filter(parent = parent)
            data['user'] = {
                'id': request.user.id,
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'role': request.user.role,
                'children': ChildSerializer(children, many=True).data,
                'is_superuser': request.user.is_superuser,
                'is_staff': request.user.is_staff
            }

        elif request.user.is_supervisor:
            data['user'] = {
                'id': request.user.id,
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'role': request.user.role,
                'is_superuser': request.user.is_superuser,
                'is_staff': request.user.is_staff
            }
        else:
            data['user'] = {
                'id': request.user.id,
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'role': 'superadmin',
                'is_superuser': request.user.is_superuser,
                'is_staff': request.user.is_staff
            }

        return Response(data)
