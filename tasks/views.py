from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.conf import settings
from rest_framework.decorators import action
from account.permissions import IsSuperUserOrStaffOrReadOnly
from account.models import Student, Child
from .models import Answer, Course, Image, Section, Lesson, Content, Task, Question, TaskCompletion
from .serializers import CourseSerializer, SectionSerializer, LessonSerializer, ContentSerializer, TaskSerializer, QuestionSerializer

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
        data = request.data.copy()
        data['created_by'] = user.id
        serializer = self.serializer_class(data=data, context={'request': request})
        if serializer.is_valid():
            course = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

class SectionViewSet(viewsets.ModelViewSet):
    queryset = Section.objects.all()
    serializer_class = SectionSerializer
    permission_classes = [IsSuperUserOrStaffOrReadOnly]

    def get_queryset(self):
        return Section.objects.filter(course_id=self.kwargs['course_pk']).order_by('id')
    
    def create(self, request, course_pk=None):
        data = request.data.copy()

        if isinstance(data, list):
            for item in data:
                item['course'] = course_pk
        else:
            data['course'] = course_pk

        serializer = self.serializer_class(data=data, many=isinstance(data, list))
        if serializer.is_valid():
            sections = serializer.save()
            return Response(self.serializer_class(sections, many=isinstance(data, list)).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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

    def create(self, request, course_pk=None, section_pk=None):
        data = request.data.copy()
        data['section'] = section_pk
        serializer = self.serializer_class(data=data, context={'request': request})
        if serializer.is_valid():
            content = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['patch'], permission_classes=[IsSuperUserOrStaffOrReadOnly])
    def update_contents(self, request, course_pk=None, section_pk=None):
        contents_data = request.data.get('contents')
        if not contents_data:
            return Response({"detail": "Contents data is missing."}, status=status.HTTP_400_BAD_REQUEST)

        for content_data in contents_data:
            content = get_object_or_404(Content, id=content_data['id'])
            content.order = content_data.get('order', content.order)
            content.title = content_data.get('title', content.title)
            content.description = content_data.get('description', content.description)
            content.save()

        return Response({"detail": "Contents updated successfully."}, status=status.HTTP_200_OK)

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
        data = request.data.copy()

        if isinstance(data, list):
            for item in data:
                item['section'] = section_pk
                item['content_type'] = "lesson"
        else:
            data['section'] = section_pk
            data['content_type'] = "lesson"

        serializer = self.serializer_class(data=data, many=isinstance(data, list), context={'request': request})
        if serializer.is_valid():
            lessons = serializer.save()
            return Response(self.serializer_class(lessons, many=isinstance(data, list)).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
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
        data = request.data.copy()

        if isinstance(data, list):
            for item in data:
                item['section'] = section_pk
                item['content_type'] = "task"
        else:
            data['section'] = section_pk
            data['content_type'] = "task"

        serializer = self.serializer_class(data=data, many=isinstance(data, list), context={'request': request})
        if serializer.is_valid():
            tasks = serializer.save()
            return Response(self.serializer_class(tasks, many=isinstance(data, list)).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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

    def create(self, request, *args, **kwargs):
        data = request.data

        if isinstance(data, list):
            for item in data:
                item['task'] = self.kwargs['task_pk']
        else:
            data['task'] = self.kwargs['task_pk']
            
        serializer = self.serializer_class(data=data, many=isinstance(data, list), context={'request': request})
        if serializer.is_valid():
            questions = serializer.save()
            return Response(self.serializer_class(questions, many=isinstance(data, list)).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='answer', permission_classes=[IsAuthenticated])
    def answer(self, request, *args, **kwargs):
        question = self.get_object()
        user = request.user
        child_id = request.data.get('child_id')
        answer = request.data.get('answer')

        if user.is_student:
            is_answered = Answer.objects.filter(user=user, question=question, is_correct=True).exists()
        elif user.is_parent and child_id:
            child = get_object_or_404(Child, parent=user.parent, pk=child_id)
            is_answered = Answer.objects.filter(child=child, question=question, is_correct=True).exists()
        else:
            return Response({"message": "Invalid request. Parent must provide child_id."}, status=status.HTTP_400_BAD_REQUEST)

        if is_answered:
            return Response({"message": "Question already answered."}, status=status.HTTP_400_BAD_REQUEST)

        is_correct = self.validate_answer(question, answer)

        if is_correct:
            Answer.objects.create(user=user if user.is_student else None, child=child if user.is_parent else None, question=question, answer=answer, is_correct=is_correct)
            return self.handle_correct_answer(user, child, question)
        else:
            Answer.objects.create(user=user if user.is_student else None, child=child if user.is_parent else None, question=question, answer=answer, is_correct=is_correct)
            return Response({"message": "Incorrect answer.", "is_correct": False}, status=status.HTTP_400_BAD_REQUEST)

    def validate_answer(self, question, answer):
        if question.question_type in ['multiple_choice_text', 'true_false', 'drag_and_drop', 'drag_position', 'number_line']:
            return answer == question.correct_answer
        elif question.question_type == 'mark_all':
            return set(answer) == set(question.correct_answer)
        return False

    def handle_correct_answer(self, user, child, question):
        task = question.task
        questions = task.questions.all()
        entity = user if user.is_student else child

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
            TaskCompletion.objects.create(user=user if user.is_student else None, child=child if user.is_parent else None, task=task)
            entity.update_streak()
            return Response({"message": "Correct answer! Task completed. Cups and stars updated.", "is_correct": True}, status=status.HTTP_200_OK)
        return Response({"message": "Correct answer! Cups and stars updated.", "is_correct": True}, status=status.HTTP_200_OK)
