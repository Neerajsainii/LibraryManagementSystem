from rest_framework import serializers
from .models import Fine, Payment
from apps.loans.serializers import BookLoanSerializer

class FineSerializer(serializers.ModelSerializer):
    loan = BookLoanSerializer(read_only=True)

    class Meta:
        model = Fine
        fields = ('id', 'user', 'loan', 'amount', 'reason', 'status',
                 'due_date', 'payment_date', 'created_at')
        read_only_fields = ('created_at', 'payment_date')

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ('id', 'fine', 'amount', 'payment_method', 'transaction_id',
                 'status', 'payment_date', 'razorpay_order_id',
                 'razorpay_payment_id', 'razorpay_signature', 'created_at')
        read_only_fields = ('created_at', 'payment_date', 'status',
                           'razorpay_order_id', 'razorpay_payment_id',
                           'razorpay_signature')

class RazorpayOrderSerializer(serializers.Serializer):
    fine_id = serializers.IntegerField()

class RazorpayCallbackSerializer(serializers.Serializer):
    razorpay_payment_id = serializers.CharField()
    razorpay_order_id = serializers.CharField()
    razorpay_signature = serializers.CharField()