from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.conf import settings
from rest_framework.decorators import action
from account.permissions import IsSuperUserOrStaffOrReadOnly
from account.models import Student, Child
from .models import Answer, Course, Section, Lesson, Content, Task, Question, TaskCompletion
from .serializers import AnswerSerializer, CourseSerializer, SectionSerializer, LessonSerializer, ContentSerializer, TaskSerializer, QuestionSerializer

class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsSuperUserOrStaffOrReadOnly]

    def list(self, request):
        user = request.user
        child_id = request.query_params.get('child_id', None)
        
        if user.is_student:
            student = get_object_or_404(Student, user=user)
            queryset = Course.objects.filter(grade=student.grade)
        elif user.is_parent and child_id:
            child = get_object_or_404(Child, parent=user.parent, pk=child_id)
            queryset = Course.objects.filter(grade=child.grade)
        else:
            queryset = Course.objects.all()

        serializer = self.serializer_class(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    def create(self, request):
        user = request.user
        data = request.data
        data['created_by'] = user.id
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Course created successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

class SectionViewSet(viewsets.ModelViewSet):
    queryset = Section.objects.all()
    serializer_class = SectionSerializer
    permission_classes = [IsSuperUserOrStaffOrReadOnly]

    def get_queryset(self):
        return Section.objects.filter(course_id=self.kwargs['course_pk']).order_by('contents__order')
    
    def create(self, request, course_pk=None):
        data = request.data
        data['course'] = course_pk
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Section created successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

class ContentViewSet(viewsets.ModelViewSet):
    queryset = Content.objects.all()
    serializer_class = ContentSerializer
    permission_classes = [IsSuperUserOrStaffOrReadOnly]

    def get_queryset(self):
        return Content.objects.filter(section_id=self.kwargs['section_pk']).order_by('order')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context


class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsSuperUserOrStaffOrReadOnly]

    def get_queryset(self):
        return Lesson.objects.filter(section_id=self.kwargs['section_pk']).order_by('order')
    
    def create(self, request, course_pk=None, section_pk=None):
        data = request.data
        data['section'] = section_pk
        data['type'] = "lesson"
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Lesson created successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors)
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsSuperUserOrStaffOrReadOnly]

    def get_queryset(self):
        return Task.objects.filter(section_id=self.kwargs['section_pk']).order_by('order')
    
    def create(self, request, course_pk=None, section_pk=None):
        data = request.data
        data['section'] = section_pk
        data['type'] = "task"
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Task created successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Question.objects.filter(task_id=self.kwargs['task_pk'])

    def create(self, request, course_pk=None, section_pk=None, task_pk=None):
        data = request.data
        data['task'] = task_pk
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Question created successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors)

    @action(detail=True, methods=['post'], url_path='answer', permission_classes=[IsAuthenticated])
    def answer(self, request, *args, **kwargs):
        question = self.get_object()
        user = request.user
        child_id = request.data.get('child_id')

        if user.is_student:
            student = user.student
            is_answered = Answer.objects.filter(user=user, question=question, is_correct=True).exists()
        elif user.is_parent and child_id:
            child = get_object_or_404(Child, parent=user.parent, pk=child_id)
            is_answered = Answer.objects.filter(child=child, question=question, is_correct=True).exists()
        else:
            return Response({"message": "Invalid request. Parent must provide child_id."}, status=status.HTTP_400_BAD_REQUEST)

        if is_answered:
            return Response({"message": "Question already answered."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = AnswerSerializer(data=request.data)
        if serializer.is_valid():
            answer = serializer.validated_data['answer']
            is_correct = answer == question.correct_answer

            if user.is_student:
                Answer.objects.create(user=user, question=question, answer=answer, is_correct=is_correct)
                entity = student
            elif user.is_parent:
                Answer.objects.create(child=child, question=question, answer=answer, is_correct=is_correct)
                entity = child

            if is_correct:
                task = question.task
                questions = task.questions.all()
                if user.is_student:
                    answered_questions = Answer.objects.filter(user=user, question__in=questions, is_correct=True).count()
                elif user.is_parent:
                    answered_questions = Answer.objects.filter(child=child, question__in=questions, is_correct=True).count()

                if answered_questions == questions.count():
                    task_reward = settings.TASK_REWARD
                    entity.cups += task_reward
                    entity.stars += task_reward
                    entity.save()
                    entity.update_level()
                    TaskCompletion.objects.create(user=user, task=task) if user.is_student else TaskCompletion.objects.create(child=child, task=task)
                    entity.update_streak()
                    return Response({"message": "Correct answer! Task completed. Cups and stars updated.", "is_correct": True}, status=status.HTTP_200_OK)
                return Response({"message": "Correct answer! Cups and stars updated.", "is_correct": True}, status=status.HTTP_200_OK)
            else:
                return Response({"message": "Incorrect answer.", "is_correct": False}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
