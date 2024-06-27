from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from account.permissions import IsSuperUserOrStaffOrReadOnly
from account.models import Student, Child
from .models import Answer, Course, Image, Section, Lesson, Content, Task, Question, TaskCompletion
from .serializers import CourseSerializer, SectionSerializer, LessonSerializer, ContentSerializer, TaskSerializer, QuestionSerializer, TaskSummarySerializer
from rest_framework.views import APIView


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
        return Section.objects.filter(course_id=self.kwargs['course_pk']).order_by('order')
    
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
        print(serializer.errors)
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

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return TaskSummarySerializer
        return TaskSerializer

    def create(self, request, course_pk=None, section_pk=None):
        data = request.data.copy()
        if isinstance(data, list):
            for item in data:
                item['section'] = section_pk
                item['content_type'] = "task"
        else:
            data['section'] = section_pk
            data['content_type'] = "task"

        serializer = self.get_serializer(data=data, many=isinstance(data, list), context={'request': request})
        if serializer.is_valid():
            tasks = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [IsSuperUserOrStaffOrReadOnly]

    def get_queryset(self):
        return Question.objects.filter(task_id=self.kwargs['task_pk'])

    def create(self, request, *args, **kwargs):
        data = request.data
        print(data)

        if isinstance(data, list):
            for item in data:
                item['task'] = self.kwargs['task_pk']
        else:
            data['task'] = self.kwargs['task_pk']
            
        serializer = self.serializer_class(data=data, many=isinstance(data, list), context={'request': request})
        if serializer.is_valid():
            questions = serializer.save()
            return Response(self.serializer_class(questions, many=isinstance(data, list)).data, status=status.HTTP_201_CREATED)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='answer', permission_classes=[IsAuthenticated])
    def answer(self, request, *args, **kwargs):
        question = self.get_object()
        user = request.user
        child_id = request.data.get('child_id')
        answer_text = request.data.get('answer')

        # Fetch the correct answer status
        is_correct = self.validate_answer(question, answer_text)
        print(is_correct)

        if user.is_student:
            result = self.handle_answer(user=user, question=question, answer_text=answer_text, is_correct=is_correct)
        elif user.is_parent and child_id:
            child = get_object_or_404(Child, parent=user.parent, pk=child_id)
            result = self.handle_answer(child=child, question=question, answer_text=answer_text, is_correct=is_correct)
        else:
            return Response({"message": "Invalid request. Parent must provide child_id."}, status=status.HTTP_400_BAD_REQUEST)

        return Response(result, status=status.HTTP_200_OK)

    def validate_answer(self, question, answer):
        print(f"Answer: {answer}")
        print(f"Correct Answer: {question.correct_answer}")
        if question.question_type in ['multiple_choice_text', 'true_false', 'drag_and_drop', 'drag_position', 'number_line']:
            return int(answer) == question.correct_answer
        elif question.question_type == 'multiple_choice_images':
            return int(answer) == question.correct_answer
        elif question.question_type == 'mark_all':
            return set(answer) == set(question.correct_answer)
        return False

    def handle_answer(self, user=None, child=None, question=None, answer_text=None, is_correct=False):
        entity = user.student if user else child
        is_answer_exists = Answer.objects.filter(
            user=user, child=child,
            question=question
        ).exists()


        print(f"Does answer exists?: {is_answer_exists}")

        if is_answer_exists:
            return {
                "message": "Answer proccessed, but no reward is given",
                "is_correct": is_correct
            }

        Answer.objects.create(
            user=user if user else None,
            child=child if child else None,
            question=question,
            answer=answer_text,
            is_correct=is_correct
        )

        if is_correct:
            entity.add_question_reward()
            entity.update_level()

        # Handle task completion
        task = question.task
        total_questions = task.questions.count()
        answered_questions = Answer.objects.filter(
            user=user, child=child,
            question__task=task
        ).count()

        correct_answers = Answer.objects.filter( 
            user=user, child=child,
            question__task=task,
            is_correct=True
        ).count()

        wrong_answers = Answer.objects.filter(
            user=user, child=child,
            question__task=task,
            is_correct=False
        ).count()


        if answered_questions == total_questions:
            TaskCompletion.objects.get_or_create(
                user=user if user else None,
                child=child if child else None,
                task=task,
                correct=correct_answers,
                wrong=wrong_answers
            )
            entity.update_streak()

        return {
            "message": "Answer processed, reward is given",
            "is_correct": is_correct
        }




class PlayGameView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        child_id = request.GET.get('child_id', None)

        if user.is_student:
            student = get_object_or_404(Student, user=user)
            if student.stars < 500:
                return Response({"message": "Not enough stars"}, status=status.HTTP_400_BAD_REQUEST)
            student.stars -= 500
            student.save()
            return Response({"message": "500 stars have been deducted"}, status=status.HTTP_200_OK)
        
        elif user.is_parent and child_id:
            child = get_object_or_404(Child, parent=user.parent, pk=child_id)
            if child.stars < 500:
                return Response({"message": "Not enough stars"}, status=status.HTTP_400_BAD_REQUEST)
            child.stars -= 500
            child.save()
            return Response({"message": "500 stars have been deducted from the child"}, status=status.HTTP_200_OK)
        
        return Response({"message": "Invalid request. Parent must provide child_id."}, status=status.HTTP_400_BAD_REQUEST)