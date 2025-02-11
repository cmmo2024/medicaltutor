from django.contrib import admin
from .models import Plan, Payment, Voucher

# Register your models here.
@admin.register(Plan)
class PlansAdmin(admin.ModelAdmin):
    list_display = ('plan_name', 'price', 'max_queries', 'max_quizzes')
    list_editable = ('price', 'max_queries', 'max_quizzes',)
    
@admin.register(Payment)
class PaymentsAdmin(admin.ModelAdmin):
    list_display = ('payment_id', 'user','transaction_id' , 'RECEIVER_ID_CARD','amount', 'payment_date')
    readonly_fields = ('payment_id', 'user','transaction_id', 'RECEIVER_ID_CARD','amount', 'payment_date')
    search_fields = ('user','transaction_id',)
    
@admin.register(Voucher)
class VouchersAdmin(admin.ModelAdmin):
    list_display = ('voucher_id', 'transaction_id', 'card_id','amount', 'created_at','used')
    readonly_fields = ('voucher_id', 'transaction_id', 'card_id', 'amount', 'created_at', 'used')
    search_fields = ('transaction_id',)

