from rest_framework import status, viewsets
from rest_framework.response import Response

from account.models import Child
from account.permissions import IsParent, IsSuperUser
from account.serializers import ChildSerializer


class ChildrenViewSet(viewsets.ModelViewSet):
    serializer_class = ChildSerializer
    permission_classes = [IsParent | IsSuperUser]

    def create(self, request):
        parent = request.user.parent
        if parent.children.count() >= 3:
            return Response(
                {"message": "You can't add more than 3 children"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        data = request.data.copy()
        data["parent"] = parent.pk
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self):
        if self.request.user.is_parent:
            parent = self.request.user.parent
            return Child.objects.filter(parent=parent)
        if self.request.user.is_superuser:
            return Child.objects.all()
