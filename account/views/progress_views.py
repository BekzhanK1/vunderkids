from datetime import timedelta

from django.conf import settings
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from account.models import Child, Student
from account.permissions import IsParent, IsStudent
from account.serializers import (ChildrenListSerializer, ChildSerializer,
                                 SimpleStudentSerializer,
                                 StudentsListSerializer)
from tasks.models import TaskCompletion


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
