from django.shortcuts import get_object_or_404
from rest_framework import serializers
from .models import Course, Section, Lesson, Content, Task, Question, TaskCompletion, Answer
from account.models import Child

class ContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Content
        fields = '__all__'

class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = '__all__'

class LessonSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = '__all__'

class QuestionSerializer(serializers.ModelSerializer):
    is_completed = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = '__all__'

    def get_is_completed(self, obj):
        user = self.context['request'].user
        child_id = self.context['request'].query_params.get('child_id')
        if user.is_student:
            return Answer.objects.filter(user=user, question=obj, is_correct=True).exists()
        elif user.is_parent and child_id:
            child = get_object_or_404(Child, parent=user.parent, pk=child_id)
            return Answer.objects.filter(child=child, question=obj, is_correct=True).exists()
        return False
    
class AnswerSerializer(serializers.Serializer):
    answer = serializers.CharField()

class TaskSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    is_completed = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = '__all__'

    def get_is_completed(self, obj):
        user = self.context['request'].user
        child_id = self.context['request'].query_params.get('child_id')
        if user.is_student:
            return TaskCompletion.objects.filter(user=user, task=obj).exists()
        elif user.is_parent and child_id:
            child = get_object_or_404(Child, parent=user.parent, pk=child_id)
            return TaskCompletion.objects.filter(child=child, task=obj).exists()
        return False

class TaskSummarySerializer(serializers.ModelSerializer):
    is_completed = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'is_completed']

    def get_is_completed(self, obj):
        user = self.context['request'].user
        child_id = self.context['request'].query_params.get('child_id')
        if user.is_student:
            return TaskCompletion.objects.filter(user=user, task=obj).exists()
        elif user.is_parent and child_id:
            child = get_object_or_404(Child, parent=user.parent, pk=child_id)
            return TaskCompletion.objects.filter(child=child, task=obj).exists()
        return False

class SectionSerializer(serializers.ModelSerializer):
    tasks = TaskSummarySerializer(many=True, read_only=True)
    lessons = LessonSummarySerializer(many=True, read_only=True)
    total_tasks = serializers.SerializerMethodField()
    completed_tasks = serializers.SerializerMethodField()
    percentage_completed = serializers.SerializerMethodField()

    class Meta:
        model = Section
        fields = '__all__'

    def get_total_tasks(self, obj):
        return Task.objects.filter(section=obj).count()

    def get_completed_tasks(self, obj):
        user = self.context['request'].user
        child_id = self.context['request'].query_params.get('child_id')
        if user.is_student:
            return TaskCompletion.objects.filter(user=user, task__section=obj).count()
        elif user.is_parent and child_id:
            child = get_object_or_404(Child, parent=user.parent, pk=child_id)
            return TaskCompletion.objects.filter(child=child, task__section=obj).count()
        return 0

    def get_percentage_completed(self, obj):
        total_tasks = self.get_total_tasks(obj)
        completed_tasks = self.get_completed_tasks(obj)
        return (completed_tasks * 100 / total_tasks) if total_tasks > 0 else 0

class SectionSummarySerializer(serializers.ModelSerializer):
    total_tasks = serializers.SerializerMethodField()
    completed_tasks = serializers.SerializerMethodField()
    percentage_completed = serializers.SerializerMethodField()

    class Meta:
        model = Section
        fields = ['id', 'title', 'description', 'total_tasks', 'completed_tasks', 'percentage_completed']

    def get_total_tasks(self, obj):
        return Task.objects.filter(section=obj).count()

    def get_completed_tasks(self, obj):
        user = self.context['request'].user
        child_id = self.context['request'].query_params.get('child_id')
        if user.is_student:
            return TaskCompletion.objects.filter(user=user, task__section=obj).count()
        elif user.is_parent and child_id:
            child = get_object_or_404(Child, parent=user.parent, pk=child_id)
            return TaskCompletion.objects.filter(child=child, task__section=obj).count()
        return 0

    def get_percentage_completed(self, obj):
        total_tasks = self.get_total_tasks(obj)
        completed_tasks = self.get_completed_tasks(obj)
        return (completed_tasks * 100 / total_tasks) if total_tasks > 0 else 0

class CourseSerializer(serializers.ModelSerializer):
    sections = SectionSummarySerializer(many=True, read_only=True)
    total_tasks = serializers.SerializerMethodField()
    completed_tasks = serializers.SerializerMethodField()
    percentage_completed = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = '__all__'

    def get_total_tasks(self, obj):
        return Task.objects.filter(section__course=obj).count()

    def get_completed_tasks(self, obj):
        user = self.context['request'].user
        child_id = self.context['request'].query_params.get('child_id')
        if user.is_student:
            return TaskCompletion.objects.filter(user=user, task__section__course=obj).count()
        elif user.is_parent and child_id:
            child = get_object_or_404(Child, parent=user.parent, pk=child_id)
            return TaskCompletion.objects.filter(child=child, task__section__course=obj).count()
        return 0

    def get_percentage_completed(self, obj):
        total_tasks = self.get_total_tasks(obj)
        completed_tasks = self.get_completed_tasks(obj)
        return (completed_tasks * 100 / total_tasks) if total_tasks > 0 else 0
