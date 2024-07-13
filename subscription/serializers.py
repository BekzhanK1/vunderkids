from rest_framework import serializers
from .models import Plan, Subscription

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ['id', 'price', 'duration', 'is_enabled']

class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ['id', 'user', 'plan', 'start_date', 'end_date', 'is_active']
        read_only_fields = ['id', 'start_date', 'end_date', 'is_active']


class SubscriptionCreateSerializer(serializers.Serializer):
    plan_name = serializers.CharField(max_length=20)

    def validate(self, data):
        plan_name = data.get('plan_name')
        try:
            plan = Plan.objects.get(duration=plan_name)
        except Plan.DoesNotExist:
            raise serializers.ValidationError("Invalid plan name.")
        data['plan'] = plan
        return data
    
    def create(self, validated_data):
        user = self.context['request'].user
        plan = validated_data['plan']
        subscription = Subscription.objects.create(user=user, plan=plan)
        return subscription
