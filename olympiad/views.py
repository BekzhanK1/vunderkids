from django.shortcuts import get_object_or_404, render
from rest_framework import viewsets, status

from account.models import Child, Student
from account.permissions import IsSuperUserOrStaffOrReadOnly
from olympiad.models import Olympiad
from rest_framework.response import Response

from olympiad.serializers import OlympiadSerializer


# Create your views here.
class OlympiadViewSet(viewsets.ModelViewSet):
    queryset = Olympiad.objects.all()
    serializer_class = OlympiadSerializer
    permission_classes = [IsSuperUserOrStaffOrReadOnly]

    def list(self, request):
        user = request.user
        child_id = request.query_params.get("child_id", None)

        if user.is_student:
            student = get_object_or_404(Student, user=user)
            queryset = Olympiad.objects.filter(
                grade=student.grade, language=student.language, is_for_teachers=False
            )

        elif user.is_parent and child_id:
            child = get_object_or_404(Child, parent=user.parent, pk=child_id)
            queryset = Olympiad.objects.filter(
                grade=child.grade, language=child.language, is_for_teachers=False
            )

        elif user.is_teacher:
            queryset = Olympiad.objects.filter(is_for_teachers=True)

        else:
            queryset = Olympiad.objects.all()

        serializer = self.serializer_class(
            queryset, many=True, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        serializer = self.serializer_class(data=data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
