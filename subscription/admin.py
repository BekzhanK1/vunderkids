from django.contrib import admin
from .models import Plan, Subscription

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('duration', 'price', 'is_enabled')
    search_fields = ('duration',)
    list_filter = ('is_enabled',)

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'start_date', 'end_date', 'is_active')
    search_fields = ('user__email', 'plan__duration')
    list_filter = ('plan__duration', 'start_date', 'end_date')
    raw_id_fields = ('user', 'plan')

    def is_active(self, obj):
        return obj.is_active
    is_active.boolean = True
    is_active.short_description = 'Is Active'

