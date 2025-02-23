from rest_framework import status, viewsets
from rest_framework.response import Response

from account.models import Class
from account.permissions import IsSuperUser
from account.serializers import ClassSerializer


class ClassViewSet(viewsets.ModelViewSet):
    serializer_class = ClassSerializer
    permission_classes = [IsSuperUser]

    def get_queryset(self):
        return Class.objects.filter(school_id=self.kwargs["school_pk"]).order_by(
            "grade"
        )

    def create(self, request, *args, **kwargs):
        school_id = self.kwargs["school_pk"]
        data = request.data.copy()
        data["school"] = school_id

        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            school_class = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
