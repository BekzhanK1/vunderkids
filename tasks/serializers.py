from django.shortcuts import get_object_or_404
from rest_framework import serializers
from .models import Course, Image, Section, Lesson, Content, Task, Question, TaskCompletion, Answer
from account.models import Child

class AnswerSerializer(serializers.Serializer):
    answer = serializers.CharField()



class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = '__all__'

class LessonSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['id', 'title', 'description', 'video_url', 'text', 'order']

class ImageSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    value = serializers.SerializerMethodField()
    class Meta:
        model = Image
        fields = ['id', 'value']

    def get_id(self, obj):
        return obj.option_id
    
    def get_value(self, obj):
        return obj.image.url

    

class QuestionSerializer(serializers.ModelSerializer):
    is_attempted = serializers.SerializerMethodField()
    is_correct = serializers.SerializerMethodField()
    images = ImageSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = '__all__'
       

    def get_is_attempted(self, obj):
        request = self.context.get('request', None)
        if not request:
            return False
        
        user = request.user
        child_id = request.query_params.get('child_id')

        if user.is_student:
            return Answer.objects.filter(user=user, question=obj).exists()
        elif user.is_parent:
            child = get_object_or_404(Child, parent=user.parent, pk=child_id)
            return Answer.objects.filter(child=child, question=obj).exists()
        else:
            return False

    def get_is_correct(self, obj):
        request = self.context.get('request', None)
        if not request:
            return False
        
        user = request.user
        child_id = request.query_params.get('child_id')
        if user.is_student:
            if Answer.objects.filter(user=user, question=obj, is_correct=True).exists():
                return True
            elif Answer.objects.filter(user=user, question=obj, is_correct=False).exists():
                return False
            else:
                return None
        elif user.is_parent and child_id:
            child = get_object_or_404(Child, parent=user.parent, pk=child_id)
            return Answer.objects.filter(child=child, question=obj, is_correct=True).exists()
        return False

    def create(self, validated_data):
        question = Question.objects.create(**validated_data)

        if question.question_type in ['multiple_choice_images', 'drag_and_drop_images']:
            images_data = self.context.get('request').FILES
            options = []
            for key in images_data:
                if 'image_' in key:
                    option_id = key.split('_')[1]  # Expecting the key to be formatted as 'image_OPTIONID'
                    image_file = images_data[key]
                    image = Image.objects.create(
                        question=question,
                        image=image_file,
                        option_id=option_id
                    )
                    options.append({'id': option_id, 'value': image.image.url})
            question.options = options
            question.save()

        return question
    

    def update(self, instance, validated_data):
        instance.title = validated_data.get('title', instance.title)
        instance.question_text = validated_data.get('question_text', instance.question_text)
        instance.question_type = validated_data.get('question_type', instance.question_type)
        instance.correct_answer = validated_data.get('correct_answer', instance.correct_answer)
        instance.template = validated_data.get('template', instance.template)

        if 'audio' in validated_data:
            instance.audio = validated_data['audio']

        if instance.question_type in ['multiple_choice_images', 'drag_and_drop_images']:
            images_data = self.context.get('request').FILES
            options = []
            # instance.images.all().delete()  # Delete existing images

            for key in images_data:
                if 'image_' in key:
                    option_id = key.split('_')[1]  # Expecting the key to be formatted as 'image_OPTIONID'
                    image_file = images_data[key]

                    # Check if image with the option_id already exists
                    image = instance.images.filter(option_id=option_id).first()
                    if image:
                        image.image = image_file
                        image.save()
                    else:
                        image = Image.objects.create(
                            question=instance,
                            image=image_file,
                            option_id=option_id
                        )

                    options.append({'id': option_id, 'image': image.image.url})

            instance.options = options
        else:
            instance.images.all().delete()
            instance.options = validated_data.get('options', instance.options)

        instance.save()
        return instance
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.question_type in ['multiple_choice_images', 'drag_and_drop_images']:
            representation['options'] = representation.pop('images', [])
        return representation
    
    
    



class TaskSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    is_completed = serializers.SerializerMethodField()
    total_questions = serializers.SerializerMethodField()
    correct_questions = serializers.SerializerMethodField()
    incorrect_questions = serializers.SerializerMethodField()
    answered_questions = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = '__all__'

    def get_task_completion(self, obj):
        request = self.context.get('request', None)
        if not request:
            return None
        
        user = request.user
        child_id = request.query_params.get('child_id')

        if user.is_student:
            return TaskCompletion.objects.filter(user=user, task=obj).exists()
        elif user.is_parent and child_id:
            child = get_object_or_404(Child, parent=user.parent, pk=child_id)
            return TaskCompletion.objects.filter(child=child, task=obj).exists()
        else:
            return None

    def get_answered_questions(self, obj):
        task_completion = self.get_task_completion(obj)
        if task_completion:
            return task_completion.correct + task_completion.wrong
        return 0

    def get_progress(self, obj):
        answered_questions = self.get_answered_questions(obj)
        total_questions = self.get_total_questions(obj)
        if total_questions == 0:
            return 0
        return (answered_questions / total_questions) * 100

    def get_incorrect_questions(self, obj):
        return self.get_total_questions(obj) - self.get_correct_questions(obj)

    def get_total_questions(self, obj):
        return obj.questions.count()

    def get_correct_questions(self, obj):
        task_completion = self.get_task_completion(obj)
        return task_completion.correct if task_completion else 0

    def get_is_completed(self, obj):
        task_completion = self.get_task_completion(obj)
        return task_completion is not None

class TaskSummarySerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    is_completed = serializers.SerializerMethodField()
    total_questions = serializers.SerializerMethodField()
    correct_questions = serializers.SerializerMethodField()
    incorrect_questions = serializers.SerializerMethodField()
    answered_questions = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'section', 'questions', 'order', 'progress', 'answered_questions', 'is_completed', 'total_questions', 'correct_questions', 'incorrect_questions']

    def get_task_completion(self, obj):
        request = self.context.get('request', None)
        if not request:
            return None

        user = request.user
        child_id = request.query_params.get('child_id')

        if user.is_student:
            return TaskCompletion.objects.filter(user=user, task=obj).first()
        elif user.is_parent and child_id:
            child = get_object_or_404(Child, parent=user.parent, pk=child_id)
            return TaskCompletion.objects.filter(child=child, task=obj).first()
        else:
            return None

    def get_answered_questions(self, obj):
        task_completion = self.get_task_completion(obj)
        if task_completion:
            return task_completion.correct + task_completion.wrong
        return 0

    def get_progress(self, obj):
        answered_questions = self.get_answered_questions(obj)
        total_questions = self.get_total_questions(obj)
        if total_questions == 0:
            return 0
        return (answered_questions / total_questions) * 100

    def get_incorrect_questions(self, obj):
        task_completion = self.get_task_completion(obj)
        return task_completion.wrong if task_completion else 0

    def get_total_questions(self, obj):
        return obj.questions.count()

    def get_correct_questions(self, obj):
        task_completion = self.get_task_completion(obj)
        return task_completion.correct if task_completion else 0

    def get_is_completed(self, obj):
        task_completion = self.get_task_completion(obj)
        return task_completion is not None
    


class ContentSerializer(serializers.ModelSerializer):
    is_completed = serializers.SerializerMethodField()

    class Meta:
        model = Content
        fields = '__all__'

    def get_is_completed(self, obj):
        request = self.context.get('request', None)
        if not request:
            return None
        
        if obj.content_type == "task":
            user = request.user
            child_id = request.query_params.get('child_id')

            if user.is_student:
                return TaskCompletion.objects.filter(user=user, task=obj).exists()
            elif user.is_parent and child_id:
                child = get_object_or_404(Child, parent=user.parent, pk=child_id)
                return TaskCompletion.objects.filter(child=child, task=obj).exists()
            else:
                return None
        
        return None

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.content_type != "task":
            representation.pop('is_completed', None)
        return representation

class SectionSerializer(serializers.ModelSerializer):
    contents = ContentSerializer(many=True, read_only=True)
    total_tasks = serializers.SerializerMethodField()
    completed_tasks = serializers.SerializerMethodField()
    percentage_completed = serializers.SerializerMethodField()

    class Meta:
        model = Section
        fields = '__all__'

    def get_total_tasks(self, obj):
        return Task.objects.filter(section=obj).count()

    def get_completed_tasks(self, obj):
        request = self.context.get('request', None)
        if not request:
            return 0

        user = request.user
        child_id = request.query_params.get('child_id')
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
        fields = ['id', 'title', 'description', 'order','total_tasks', 'completed_tasks', 'percentage_completed']

    def get_total_tasks(self, obj):
        return Task.objects.filter(section=obj).count()

    def get_completed_tasks(self, obj):
        request = self.context.get('request', None)
        if not request:
            return 0

        user = request.user
        child_id = request.query_params.get('child_id')
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
        request = self.context.get('request', None)
        if not request:
            return 0

        user = request.user
        child_id = request.query_params.get('child_id')
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
