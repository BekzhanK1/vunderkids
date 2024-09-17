from django.shortcuts import get_list_or_404
from rest_framework import serializers

from olympiad.models import Olympiad


class OlympiadSerializer(serializers.ModelSerializer):

    class Meta:
        model = Olympiad
        fields = "__all__"
