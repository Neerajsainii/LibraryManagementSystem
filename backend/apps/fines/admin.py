from django.contrib import admin
from .models import Fine, Payment

@admin.register(Fine)
class FineAdmin(admin.ModelAdmin):
    list_display = ('user', 'loan', 'amount', 'status', 'due_date', 'payment_date')
    list_filter = ('status', 'due_date', 'payment_date')
    search_fields = ('user__username', 'loan__book__title')
    raw_id_fields = ('user', 'loan')
    date_hierarchy = 'due_date'

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('fine', 'amount', 'payment_method', 'status', 'payment_date')
    list_filter = ('status', 'payment_method', 'payment_date')
    search_fields = ('transaction_id', 'razorpay_order_id', 'razorpay_payment_id')
    raw_id_fields = ('fine',)
