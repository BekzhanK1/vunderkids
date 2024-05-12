from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework import status
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from account.permissions import *

from account.models import Student, Child, Parent
from .models import League, Task, TaskResponse
from .serializers import TaskResponseSerializer, TaskSerializer

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'], url_path='submit-answer')
    def submit_answer(self, request, pk=None):
        """
        A custom action to submit an answer for a task.
        `pk` will be the ID of the task to which the answer is submitted.
        """

        user = request.user
        child_id = request.data.get('child_id')
        
        data = {}

        child = None
        student = None
        


        if user.is_student() and not child_id:
            student = get_object_or_404(Student, user=user)
            data['student'] = student.pk
            entity = student
        elif child_id and user.is_parent():
            parent = get_object_or_404(Parent, user=user)
            child = get_object_or_404(Child, parent=parent, pk=child_id)
            data['child'] = child.pk
            entity = child
        else:
            return Response({"error": "Either you are not a child, or haven't provided child_id"}, status=status.HTTP_400_BAD_REQUEST)



        try:
            print(child, student)
            task = self.get_object()
            if student and TaskResponse.objects.filter(task=task, student=student, is_true=True).exists():
                return Response({"message": "You have already answered question"})
            if child and TaskResponse.objects.filter(task=task, child=child, is_true=True).exists():
                return Response({"message": "You have already answered question"})

        except Task.DoesNotExist:
            return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)


        data['task'] = task.id
        data['answer'] = request.data.get('answer') 

        serializer = TaskResponseSerializer(data=data)
        if serializer.is_valid():
            task_response = serializer.save()
            if task_response.is_correct():
                task_response.is_true = True
                task_response.save()
                xp_reward = task.xp_reward
                entity.xp += xp_reward
                entity.save()
                self.check_and_update_league(entity)
                return Response({'message': f'Correct answer! You got {xp_reward} XP', 'correct': True}, status=status.HTTP_200_OK)
            else:
                task_response.is_true = False
                task_response.save()
                return Response({'message': 'Wrong answer!', 'correct': False}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

    def check_and_update_league(self, entity):
        current_league = League.objects.filter(min_xp__lte=entity.xp).order_by('-min_xp').first()
        if current_league and (entity.league is None or current_league.pk != entity.league.pk):
            entity.league = current_league
            entity.save()





