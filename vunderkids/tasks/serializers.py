from rest_framework import serializers
from .models import Task, TaskResponse

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'

class TaskResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskResponse
        fields = '__all__'
