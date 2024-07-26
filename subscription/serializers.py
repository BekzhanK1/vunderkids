from rest_framework import serializers
from .models import Plan, Subscription, DURATION_CHOICES


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ['price', 'duration', 'is_enabled']


class SubscriptionModelSerializer(serializers.ModelSerializer):
    plan = serializers.CharField(source='plan.duration', read_only=True)

    class Meta:
        model = Subscription
        fields = ['user', 'plan', 'start_date', 'end_date', 'is_active']


class SubscriptionCreateSerializer(serializers.Serializer):
    plan_name = serializers.CharField(max_length=20)

    def validate(self, data):
        plan_name = data.get('plan_name')

        if plan_name not in dict(DURATION_CHOICES) or plan_name == "free-trial":
            raise serializers.ValidationError("Invalid plan name.")
        
        plan = Plan.objects.filter(duration=plan_name, is_enabled=True).first()
        if not plan:
            raise serializers.ValidationError("Invalid plan name.")

        data['plan'] = plan
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        plan = validated_data['plan']
        active_subscription = Subscription.objects.filter(user=user).first()

        if active_subscription:
            if active_subscription.plan.duration == "free-trial":
                active_subscription.delete()
                return self._create_subscription(user, plan)
            elif active_subscription.is_active:
                raise serializers.ValidationError("You already have an active subscription.")
        return self._create_subscription(user, plan)

    def _create_subscription(self, user, plan):
        return Subscription.objects.create(user=user, plan=plan)
