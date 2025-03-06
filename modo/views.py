from rest_framework import viewsets, filters, status
from .models import Test, Question, Content, AnswerOption
from .serializers import (
    TestSerializer,
    QuestionSerializer,
    ContentSerializer,
    AnswerOptionSerializer,
)
from account.permissions import IsSuperUserOrStaffOrReadOnly
from rest_framework.exceptions import ValidationError

from rest_framework.response import Response
from django.db import transaction

MAX_ANSWER_OPTIONS = 4
MAX_CONTENTS = 4


class TestViewSet(viewsets.ModelViewSet):
    queryset = Test.objects.all()
    serializer_class = TestSerializer
    permission_classes = [IsSuperUserOrStaffOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "description"]
    ordering_fields = ["order", "title"]
    ordering = ["order"]


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [IsSuperUserOrStaffOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title"]
    ordering_fields = ["order", "title"]
    ordering = ["order"]

    def get_queryset(self):
        test_id = self.request.query_params.get("test_id")
        if not test_id:
            raise ValidationError({"detail": "Parameter 'test_id' is required."})
        queryset = super().get_queryset().filter(test_id=test_id)
        return queryset


class ContentViewSet(viewsets.ModelViewSet):
    queryset = Content.objects.all()
    serializer_class = ContentSerializer
    permission_classes = [IsSuperUserOrStaffOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["order"]
    ordering = ["order"]

    def create(self, request, *args, **kwargs):
        question_id = request.data["question"]
        existing_count = self.queryset.filter(question_id=question_id).count()
        if existing_count >= MAX_CONTENTS:
            raise ValidationError(
                {"detail": "Total content count for this question must not exceed 4."}
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AnswerOptionViewSet(viewsets.ModelViewSet):
    queryset = AnswerOption.objects.all()
    serializer_class = AnswerOptionSerializer
    permission_classes = [IsSuperUserOrStaffOrReadOnly]

    def create(self, request, *args, **kwargs):
        question_id = (
            request.data[0]["question"]
            if isinstance(request.data, list)
            else request.data["question"]
        )
        existing_count = self.queryset.filter(question_id=question_id).count()
        new_count = len(request.data) if isinstance(request.data, list) else 1

        if existing_count + new_count > MAX_ANSWER_OPTIONS:
            raise ValidationError(
                {
                    "detail": "Total answer options count for this question must not exceed 4."
                }
            )

        if isinstance(request.data, list):
            serializer = self.get_serializer(data=request.data, many=True)
            serializer.is_valid(raise_exception=True)
            with transaction.atomic():
                self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save()
