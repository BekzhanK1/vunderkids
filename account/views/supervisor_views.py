from datetime import datetime, timedelta

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from account.models import Class, School, Student
from account.permissions import IsSupervisor
from account.serializers import (ClassSerializer, SchoolSerializer,
                                 StudentSerializer)
from tasks.models import TaskCompletion


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
