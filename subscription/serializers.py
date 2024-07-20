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
        if plan_name not in [duration[0] for duration in DURATION_CHOICES] or plan_name == "free-trial":
            raise serializers.ValidationError("Invalid plan name.")
    
        try:
            plan = Plan.objects.get(duration=plan_name, is_enabled=True)
        except Plan.DoesNotExist:
            raise serializers.ValidationError("Invalid plan name.")
        
        data['plan'] = plan
        print(data)
        return data
    
    def create(self, validated_data):
        user = self.context['request'].user
        plan = validated_data['plan']

        try:
            active_subscription = Subscription.objects.get(
                user=user
            )
            if active_subscription.plan.duration == "free-trial":
                print(active_subscription.plan.duration)
                active_subscription.delete()
                subscription = Subscription.objects.create(user=user, plan=plan)
                return subscription
            elif active_subscription.is_active:
                raise serializers.ValidationError("You already have an active subscription.")
        except Subscription.DoesNotExist:
            subscription = Subscription.objects.create(user=user, plan=plan)
            return subscription
