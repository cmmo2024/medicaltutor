from django.contrib import admin
from .models import Plan, Payment

# Register your models here.
@admin.register(Plan)
class PlansAdmin(admin.ModelAdmin):
    list_display = ('plan_name', 'price', 'max_queries_per_month', 'max_quizzes_per_month')
    list_editable = ('price',)
    
@admin.register(Payment)
class PaymentsAdmin(admin.ModelAdmin):
    list_display = ('payment_id', 'transaction_id', 'user', 'amount', 'payment_date')
    readonly_fields = ('payment_date',)