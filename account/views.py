from datetime import timedelta, datetime
import uuid
from django.conf import settings
import pandas as pd
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate
from django.utils.dateparse import parse_date
from django.db.models import Sum
from account.serializers import (
    ClassSerializer,
    UserSerializer,
    StaffRegistrationSerializer,
    SupervisorRegistrationSerializer,
    ParentRegistrationSerializer,
    SchoolSerializer,
    StudentRegistrationSerializer,
    StudentSerializer,
    StudentsListSerializer,
    ChildrenListSerializer,
    ChildSerializer,
    SimpleStudentSerializer,
    MyTokenObtainPairSerializer,
)
from account.models import User, Parent, Child, Student, School, Class
from account.permissions import IsSuperUser, IsParent, IsStudent, IsSupervisor
from subscription.models import Plan, Subscription
from tasks.models import TaskCompletion
from .tasks import (
    send_activation_email,
    send_mass_activation_email,
    send_password_reset_request_email,
)
from .utils import generate_password


class ActivateAccount(APIView):
    def get(self, request, token):
        try:
            user = User.objects.get(activation_token=token)
            if user.is_activation_token_expired:
                user.activation_token = uuid.uuid4()
                user.activation_token_expires_at = timezone.now() + timedelta(days=1)
                user.save()
                send_activation_email.delay(user.pk, generate_password())
                return Response(
                    "Your activation link has expired! You will receive a new email soon",
                    status=status.HTTP_403_FORBIDDEN,
                )
            user.is_active = True
            user.activation_token = None
            user.save()
            if user.is_parent:
                plan, _ = Plan.objects.get_or_create(duration="free-trial")
                Subscription.objects.create(user=user, plan=plan)
            elif user.is_student:
                plan, _ = Plan.objects.get_or_create(duration="annual")
                Subscription.objects.create(user=user, plan=plan)
            return Response(
                "Your account has been activated successfully!",
                status=status.HTTP_200_OK,
            )
        except User.DoesNotExist:
            return Response(
                "Invalid activation link!", status=status.HTTP_400_BAD_REQUEST
            )


class ChangePassword(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        current_password = request.data["current_password"]
        new_password = request.data["new_password"]
        auth_user = authenticate(email=user.email, password=current_password)
        if auth_user:
            try:
                auth_user.set_password(new_password)
                auth_user.save()
                return Response(
                    {"message": "Successfully changed password"},
                    status=status.HTTP_200_OK,
                )
            except Exception:
                return Response(
                    {"message": "Error during password change"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            return Response(
                {"message": "Current password is incorrect"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class RequestResetPassword(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        if email:
            user = get_object_or_404(User, email=email)
            user.reset_password_token = uuid.uuid4()
            user.reset_password_token_expires_at = timezone.now() + timedelta(days=1)
            user.save()
            send_password_reset_request_email.delay(user.pk)
            return Response(
                {"message": "Request has been sent to email"},
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(
                {"message": "You need to enter the email to reset the password"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ResetPassword(APIView):
    permission_classes = [AllowAny]

    def post(self, request, token):
        try:
            user = User.objects.get(reset_password_token=token)
            if user.is_reset_password_token_expired:
                return Response(
                    "Your reset password link has expired!",
                    status=status.HTTP_403_FORBIDDEN,
                )
            password = request.data["password"]
            user.set_password(password)
            user.reset_password_token = None
            user.save()
            return Response(
                {"message": "Successfully reset password"}, status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response("Invalid reset link!", status=status.HTTP_400_BAD_REQUEST)


class StaffRegistrationAPIView(APIView):
    permission_classes = [IsSuperUser]

    def post(self, request):
        data = request.data
        data["role"] = "staff"
        serializer = StaffRegistrationSerializer(data=data)
        if serializer.is_valid():
            staff = serializer.save()
            return Response(
                {
                    "message": "Staff user is registered successfully",
                    "staff_id": staff.pk,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ParentRegistrationAPIView(APIView):
    def post(self, request):
        data = request.data
        print(data)
        serializer = ParentRegistrationSerializer(data=data)
        if serializer.is_valid():
            parent = serializer.save()
            return Response(
                {
                    "message": f"Activation email sent to {data['email']}",
                    "parent_id": parent.pk,
                },
                status=status.HTTP_201_CREATED,
            )
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SchoolViewSet(viewsets.ModelViewSet):
    queryset = School.objects.all()
    serializer_class = SchoolSerializer
    permission_classes = [IsSuperUser]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            school = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def assign_supervisor(self, request, pk=None):
        school = self.get_object()

        if school.supervisor:
            return Response(
                {"message": "School already has a supervisor"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = SupervisorRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            supervisor = serializer.save()
            school.supervisor = supervisor
            school.save()
            return Response(
                {
                    "message": "Supervisor is registered successfully",
                    "supervisor_id": supervisor.pk,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get"])
    def deassign_supervisor(self, request, pk=None):
        school = self.get_object()
        if not school.supervisor:
            return Response(
                {"message": "School doesn't have a supervisor"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        school.supervisor.delete()
        school.supervisor = None
        school.save()
        return Response(
            {"message": "Supervisor has been removed from the school"},
            status=status.HTTP_200_OK,
        )

    @action(
        detail=False,
        methods=["post"],
        url_path="upload-excel",
        url_name="upload-excel",
        permission_classes=[IsSuperUser],
    )
    def upload_excel(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response(
                {"message": "No file was uploaded"}, status=status.HTTP_400_BAD_REQUEST
            )

        self.process_excel(file)
        return Response(
            {"message": "Excel file has been processed successfully"},
            status=status.HTTP_200_OK,
        )

    def process_excel(self, excel_file):
        df = pd.read_excel(excel_file, engine="openpyxl")
        school_name = df.iloc[0]["School Name"]
        city = df.iloc[0]["City"]
        school_email = df.iloc[0]["Email"]

        school, created = School.objects.get_or_create(
            name=school_name, defaults={"city": city, "email": school_email}
        )

        # Extract the supervisor information
        supervisor_first_name = df.iloc[2]["School Name"]
        supervisor_last_name = df.iloc[2]["City"]
        supervisor_email = df.iloc[2]["Email"]
        supervisor_phone = df.iloc[2]["Unnamed: 3"]

        supervisor, created = User.objects.get_or_create(
            email=supervisor_email,
            defaults={
                "first_name": supervisor_first_name,
                "last_name": supervisor_last_name,
                "role": "supervisor",
                "is_active": False,
                "phone_number": supervisor_phone if pd.notna(supervisor_phone) else "",
            },
        )
        if created:
            supervisor.activation_token = uuid.uuid4()
            password = generate_password()
            supervisor.set_password(password)
            supervisor.save()
            send_activation_email.delay(supervisor.pk, password)

        school.supervisor = supervisor
        school.save()

        # Extract the class and student information
        df_students = pd.read_excel(excel_file, engine="openpyxl", skiprows=4)
        new_user_ids = []
        for idx, row in df_students.iterrows():
            if pd.notna(row["Class"]):
                class_info = row["Class"]
                grade = int("".join(filter(str.isdigit, class_info)))
                section = "".join(filter(str.isalpha, class_info))
                language = row["Language"]

                school_class, created = Class.objects.get_or_create(
                    school=school,
                    grade=grade,
                    section=section,
                    defaults={"language": language},
                )

            if pd.notna(row["Student Firstname"]):
                student_first_name = row["Student Firstname"]
                student_last_name = row["Student Lastname"]
                student_email = row["Email"]
                student_phone = row["Phone(optional)"]
                birth_date = row["Birthdate"]

                user, created = User.objects.get_or_create(
                    email=student_email,
                    defaults={
                        "first_name": student_first_name,
                        "last_name": student_last_name,
                        "role": "student",
                        "is_active": False,
                        "phone_number": (
                            student_phone if pd.notna(student_phone) else ""
                        ),
                    },
                )
                if created:
                    user.activation_token = uuid.uuid4()
                    user.save()
                    new_user_ids.append(user.pk)

                Student.objects.get_or_create(
                    user=user,
                    school_class=school_class,
                    school=school,
                    grade=grade,
                    defaults={"language": language, "birth_date": birth_date},
                )

        if new_user_ids:
            send_mass_activation_email.delay(new_user_ids)


class SupervisorSchoolViewset(viewsets.ReadOnlyModelViewSet):
    serializer_class = SchoolSerializer
    permission_classes = [IsSupervisor]

    def get_queryset(self):
        return School.objects.filter(supervisor=self.request.user)

    @action(detail=False, methods=["get"], url_path="school")
    def my_school(self, request):
        school = get_object_or_404(School, supervisor=request.user)
        serializer = self.get_serializer(school)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="classes")
    def my_classes(self, request):
        school = get_object_or_404(School, supervisor=request.user)
        classes = Class.objects.filter(school=school)
        serializer = ClassSerializer(classes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="classes/(?P<class_pk>[^/.]+)")
    def my_class(self, request, class_pk=None):
        school = get_object_or_404(School, supervisor=request.user)
        school_class = get_object_or_404(Class, pk=class_pk, school=school)
        serializer = ClassSerializer(school_class)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False, methods=["get"], url_path="classes/(?P<class_pk>[^/.]+)/students"
    )
    def students_of_class(self, request, class_pk=None):
        school_class = get_object_or_404(
            Class, pk=class_pk, school__supervisor=request.user
        )
        students = Student.objects.filter(school_class=school_class).order_by("-cups")
        serializer = StudentSerializer(students, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="students/(?P<student_pk>[^/.]+)")
    def student_of_class(self, request, student_pk=None):
        student = get_object_or_404(
            Student, pk=student_pk, school__supervisor=request.user
        )
        serializer = StudentSerializer(student)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=["get"],
        url_path="students/(?P<student_pk>[^/.]+)/progress",
    )
    def student_progress(self, request, student_pk=None):
        student = get_object_or_404(
            Student, pk=student_pk, school__supervisor=request.user
        )

        today = timezone.now().date()
        start_date = today - timedelta(days=6)

        task_completions = TaskCompletion.objects.filter(
            user=student.user,
            completed_at__date__gte=start_date,
            completed_at__date__lte=today,
        )
        daily_progress = {str(start_date + timedelta(days=i)): 0 for i in range(7)}

        for task_completion in task_completions:
            day = str(task_completion.completed_at.date())
            if day in daily_progress:
                correct_questions_number = task_completion.correct
                daily_progress[day] += (
                    correct_questions_number * settings.QUESTION_REWARD
                )

        date_to_day = {
            (start_date + timedelta(days=i)): (start_date + timedelta(days=i)).strftime(
                "%A"
            )
            for i in range(7)
        }

        response_data = {
            "weekly_progress": [
                {
                    "day": date_to_day[datetime.strptime(date, "%Y-%m-%d").date()],
                    "cups": cups,
                }
                for date, cups in daily_progress.items()
            ]
        }

        return Response(response_data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="top-students")
    def top_students(self, request):
        school = get_object_or_404(School, supervisor=request.user)
        top_students = Student.objects.filter(school=school).order_by("-cups")[:10]
        serializer = StudentSerializer(top_students, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ClassViewSet(viewsets.ModelViewSet):
    serializer_class = ClassSerializer
    permission_classes = [IsSuperUser]

    def get_queryset(self):
        return Class.objects.filter(school_id=self.kwargs["school_pk"]).order_by(
            "grade"
        )

    def create(self, request, *args, **kwargs):
        school_id = self.kwargs["school_pk"]
        data = request.data.copy()
        data["school"] = school_id

        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            school_class = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StudentViewSet(viewsets.ModelViewSet):
    serializer_class = StudentSerializer
    permission_classes = [IsSuperUser]

    def get_queryset(self):
        return Student.objects.filter(school_class_id=self.kwargs["class_pk"])

    def create(self, request, *args, **kwargs):
        school_id = self.kwargs["school_pk"]
        class_id = self.kwargs["class_pk"]
        school_class = get_object_or_404(Class, pk=class_id)
        data = request.data.copy()
        data["school"] = school_id
        data["school_class"] = class_id
        data["grade"] = school_class.grade
        data["language"] = school_class.language

        serializer = StudentRegistrationSerializer(data=data)
        if serializer.is_valid():
            student = serializer.save()
            return Response(
                {
                    "message": f"Activation email has been sent to {data['email']}",
                    "student_id": student.pk,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChildrenViewSet(viewsets.ModelViewSet):
    serializer_class = ChildSerializer
    permission_classes = [IsParent | IsSuperUser]

    def create(self, request):
        parent = request.user.parent
        if parent.children.count() >= 3:
            return Response(
                {"message": "You can't add more than 3 children"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        data = request.data.copy()
        data["parent"] = parent.pk
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
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
        child_id = request.query_params.get("child_id", None)

        if user.is_student:
            return self._get_top_students_for_student(user, rating_type, request)
        elif user.is_parent and child_id:
            return self._get_top_students_for_child(
                user, child_id, rating_type, request
            )

        return Response(
            {"detail": "Invalid request. Parent must provide child_id."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def _get_top_students_for_student(self, user, rating_type, request):
        current_student = user.student
        top_students = []

        if rating_type == "class":
            if current_student.school_class is not None:
                top_students = Student.objects.filter(
                    school_class=current_student.school_class
                ).order_by("-cups")[:10]
            else:
                return Response(
                    {"detail": "Student is not assigned to any class."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        elif rating_type == "school":
            if current_student.school is not None:
                top_students = Student.objects.filter(
                    school=current_student.school
                ).order_by("-cups")[:10]
            else:
                return Response(
                    {"detail": "Student is not assigned to any school."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        elif rating_type == "global":
            if current_student.grade is not None:
                top_students = Student.objects.filter(
                    grade=current_student.grade
                ).order_by("-cups")[:10]
            else:
                return Response(
                    {"detail": "Student grade is not set."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            return Response(
                {"detail": "Invalid rating type. Use 'class', 'school', or 'global'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        top_students = self._ensure_current_student_in_top_students(
            current_student, top_students
        )
        serializer = SimpleStudentSerializer(
            top_students, many=True, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def _get_top_students_for_child(self, user, child_id, rating_type, request):
        current_child = get_object_or_404(Child, parent=user.parent, pk=child_id)
        top_children = []

        if rating_type in ["class", "school", "global"]:
            if current_child.grade is not None:
                top_children = Child.objects.filter(grade=current_child.grade).order_by(
                    "-cups"
                )[:10]
            else:
                return Response(
                    {"detail": "Child is not assigned to any grade."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            return Response(
                {"detail": "Invalid rating type. Use 'global'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        top_children = self._ensure_current_child_in_top_children(
            current_child, top_children
        )
        serializer = ChildSerializer(
            top_children, many=True, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def _ensure_current_student_in_top_students(self, current_student, top_students):
        if current_student not in top_students:
            top_students = list(top_students)
            top_students.append(current_student)
            top_students.sort(key=lambda student: student.cups, reverse=True)
            top_students = top_students[:10]
        return top_students

    def _ensure_current_child_in_top_children(self, current_child, top_children):
        if current_child not in top_children:
            top_children = list(top_children)
            top_children.append(current_child)
            top_children.sort(key=lambda child: child.cups, reverse=True)
            top_children = top_children[:10]
        return top_children


class WeeklyProgressAPIView(APIView):
    permission_classes = [IsStudent | IsParent]

    def get(self, request):
        user = request.user
        child_id = request.query_params.get("child_id", None)

        today = timezone.now().date()
        start_date = today - timedelta(days=6)

        task_completions = self._get_task_completions(user, child_id, start_date, today)
        if task_completions is None:
            return Response(
                {"message": "Invalid request. Parent must provide child_id."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        daily_progress = self._calculate_daily_progress(task_completions, start_date)
        response_data = self._format_weekly_progress_response(
            daily_progress, start_date
        )

        return Response(response_data, status=status.HTTP_200_OK)

    def _get_task_completions(self, user, child_id, start_date, today):
        if user.is_student:
            return TaskCompletion.objects.filter(
                user=user,
                completed_at__date__gte=start_date,
                completed_at__date__lte=today,
            )
        elif user.is_parent and child_id:
            child = get_object_or_404(Child, pk=child_id, parent=user.parent)
            return TaskCompletion.objects.filter(
                child=child,
                completed_at__date__gte=start_date,
                completed_at__date__lte=today,
            )
        return None

    def _calculate_daily_progress(self, task_completions, start_date):
        daily_progress = {str(start_date + timedelta(days=i)): 0 for i in range(7)}

        for task_completion in task_completions:
            day = str(task_completion.completed_at.date())
            if day in daily_progress:
                daily_progress[day] += (
                    task_completion.correct * settings.QUESTION_REWARD
                )

        return daily_progress

    def _format_weekly_progress_response(self, daily_progress, start_date):
        date_to_day = {
            str(start_date + timedelta(days=i)): (
                start_date + timedelta(days=i)
            ).strftime("%A")
            for i in range(7)
        }
        return {
            "weekly_progress": [
                {"day": date_to_day[date], "cups": cups}
                for date, cups in daily_progress.items()
            ]
        }


class AllStudentsView(APIView):
    def get(self, request, *args, **kwargs):
        students = Student.objects.all().order_by("user__first_name")
        children = Child.objects.all().order_by("first_name")

        student_serializer = StudentsListSerializer(students, many=True)
        child_serializer = ChildrenListSerializer(children, many=True)

        combined_data = student_serializer.data + child_serializer.data
        sorted_combined_data = sorted(combined_data, key=lambda x: x["first_name"])

        return Response(sorted_combined_data, status=status.HTTP_200_OK)


class ProgressForSpecificDay(APIView):
    def get(self, request, *args, **kwargs):
        user = request.user
        child_id = request.query_params.get("child_id")
        date_str = request.query_params.get("date")

        if not date_str:
            return Response(
                {"message": "You haven't selected the date"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        date = parse_date(date_str)
        if not date:
            return Response(
                {"message": "Invalid date format"}, status=status.HTTP_400_BAD_REQUEST
            )

        if user.is_student:
            task_completions = TaskCompletion.objects.filter(
                completed_at__date=date, user=user
            )
        elif user.is_parent and child_id:
            child = get_object_or_404(Child, pk=child_id, parent=user.parent)
            task_completions = TaskCompletion.objects.filter(
                completed_at__date=date, child=child
            )
        else:
            return Response(
                {"message": "Invalid request parameters"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        total_cups = (
            task_completions.aggregate(total_cups=Sum("correct"))["total_cups"] or 0
        )
        total_correct_answers = (
            task_completions.aggregate(total_correct_answers=Sum("correct"))[
                "total_correct_answers"
            ]
            or 0
        )
        total_wrong_answers = (
            task_completions.aggregate(total_wrong_answers=Sum("wrong"))[
                "total_wrong_answers"
            ]
            or 0
        )
        total_cups *= settings.QUESTION_REWARD
        response_dict = {
            "total_cups": total_cups,
            "total_tasks": task_completions.count(),
            "total_correct_answers": total_correct_answers,
            "total_wrong_answers": total_wrong_answers,
        }
        return Response(response_dict, status=status.HTTP_200_OK)


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = self._get_user_data(request.user)
        return Response(data)

    def _get_user_data(self, user):
        data = {}
        has_subscription = hasattr(user, "subscription")
        active_subscription = user.subscription if has_subscription else None
        is_free_trial = False
        subscription_active = (
            active_subscription.is_active if active_subscription else False
        )
        if active_subscription:
            is_free_trial = active_subscription.plan.duration == "free-trial"

        if user.is_student:
            data["user"] = self._get_student_data(
                user, subscription_active, is_free_trial
            )
        elif user.is_parent:
            data["user"] = self._get_parent_data(
                user, subscription_active, is_free_trial
            )
        elif user.is_supervisor:
            data["user"] = self._get_supervisor_data(user)
        else:
            data["user"] = self._get_superadmin_data(user)
        return data

    def _get_student_data(self, user, subscription_active, is_free_trial):
        student = Student.objects.get(user=user)
        tasks_completed = user.completed_tasks.count()
        return {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
            "grade": student.grade,
            "gender": student.gender,
            "language": student.language,
            "level": student.level,
            "streak": student.streak,
            "cups": student.cups,
            "stars": student.stars,
            "is_superuser": user.is_superuser,
            "is_staff": user.is_staff,
            "tasks_completed": tasks_completed,
            "has_subscription": subscription_active,
            "is_free_trial": is_free_trial,
        }

    def _get_parent_data(self, user, subscription_active, is_free_trial):
        parent = user.parent
        children = Child.objects.filter(parent=parent)
        return {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
            "children": ChildSerializer(children, many=True).data,
            "is_superuser": user.is_superuser,
            "is_staff": user.is_staff,
            "has_subscription": subscription_active,
            "is_free_trial": is_free_trial,
        }

    def _get_supervisor_data(self, user):
        return {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
            "is_superuser": user.is_superuser,
            "is_staff": user.is_staff,
        }

    def _get_superadmin_data(self, user):
        return {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": "superadmin",
            "is_superuser": user.is_superuser,
            "is_staff": user.is_staff,
        }


class UserUpdateView(APIView):
    def patch(self, request):
        user = request.user
        data = request.data
        child_id = request.query_params.get("child_id", None)

        if not child_id:
            self._update_user(user, data)
        else:
            child = get_object_or_404(Child, pk=child_id, parent=user.parent)
            self._update_child(child, data)

        return Response(status=status.HTTP_204_NO_CONTENT)

    def _update_user(self, user, data):
        updated = False
        if "first_name" in data and data["first_name"] != user.first_name:
            user.first_name = data["first_name"]
            updated = True
        if "last_name" in data and data["last_name"] != user.last_name:
            user.last_name = data["last_name"]
            updated = True
        if "phone_number" in data and data["phone_number"] != user.phone_number:
            user.phone_number = data["phone_number"]
            updated = True

        if user.is_student:
            student = user.student
            if "language" in data and data["language"] != student.language:
                student.language = data["language"]
                student.save()
                updated = True
            if "avatar" in data and data["avatar"] != student.avatar:
                student.avatar = data["avatar"]
                student.save()
                updated = True

        if updated:
            user.save()

    def _update_child(self, child, data):
        updated = False
        if "first_name" in data and data["first_name"] != child.first_name:
            child.first_name = data["first_name"]
            updated = True
        if "last_name" in data and data["last_name"] != child.last_name:
            child.last_name = data["last_name"]
            updated = True
        if "grade" in data and data["grade"] != child.grade:
            child.grade = data["grade"]
            updated = True
        if "avatar" in data and data["avatar"] != child.avatar:
            child.avatar = data["avatar"]
            updated = True

        if updated:
            child.save()
