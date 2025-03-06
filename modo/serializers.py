from rest_framework import serializers
from .models import Test, Question, Content, AnswerOption


class TestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Test
        fields = "__all__"


class AnswerOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerOption
        fields = "__all__"


class ContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Content
        fields = "__all__"

    def validate(self, data):
        if data["content_type"] == "text":
            if not data.get("text"):
                raise serializers.ValidationError(
                    "Text must be filled when content_type is 'text'."
                )
            if data.get("image"):
                raise serializers.ValidationError(
                    "Image must be empty when content_type is 'text'."
                )
        else:
            if not data.get("image"):
                raise serializers.ValidationError(
                    "Image must be filled when content_type is not 'text'."
                )
            if data.get("text"):
                raise serializers.ValidationError(
                    "Text must be empty when content_type is not 'text'."
                )
        return data


class QuestionSerializer(serializers.ModelSerializer):
    answer_options = AnswerOptionSerializer(many=True, read_only=True)
    contents = ContentSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = "__all__"
