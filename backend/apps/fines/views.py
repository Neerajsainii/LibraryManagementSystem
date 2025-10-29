from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.conf import settings
from django.urls import reverse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
import razorpay
from .models import Fine, Payment
from .serializers import (
    FineSerializer, PaymentSerializer,
    RazorpayOrderSerializer, RazorpayCallbackSerializer
)

# Web Views
@login_required
def fine_list_view(request):
    fines = Fine.objects.filter(user=request.user)
    total_unpaid = fines.filter(status='PENDING').aggregate(total=Sum('amount'))['total'] or 0

    context = {
        'fines': fines,
        'total_unpaid': total_unpaid,
        'razorpay_key': settings.RAZORPAY_KEY_ID
    }
    return render(request, 'fines/fine_list.html', context)

@login_required
def fine_detail_view(request, pk):
    fine = get_object_or_404(Fine, pk=pk, user=request.user)
    payments = Payment.objects.filter(fine=fine)

    context = {
        'fine': fine,
        'payments': payments,
        'razorpay_key': settings.RAZORPAY_KEY_ID
    }
    return render(request, 'fines/fine_detail.html', context)

@login_required
def process_payment_view(request, pk):
    fine = get_object_or_404(Fine, pk=pk, user=request.user)
    
    if fine.status == 'PAID':
        messages.error(request, 'This fine has already been paid.')
        return redirect('fines:fine_detail', pk=pk)
    
    try:
        # Create Razorpay Order
        order_amount = int(fine.amount * 100)  # Convert to paisa
        order_currency = 'INR'
        order_receipt = f'fine_{fine.pk}'
        
        payment_order = razorpay_client.order.create({
            'amount': order_amount,
            'currency': order_currency,
            'receipt': order_receipt,
            'payment_capture': 1
        })
        
        # Create a payment record
        payment = Payment.objects.create(
            fine=fine,
            amount=fine.amount,
            razorpay_order_id=payment_order['id']
        )
        
        context = {
            'fine': fine,
            'razorpay_order_id': payment_order['id'],
            'razorpay_key': settings.RAZORPAY_KEY_ID,
            'callback_url': request.build_absolute_uri(
                reverse('fines:payment_success')
            ),
            'cancel_url': request.build_absolute_uri(
                reverse('fines:payment_cancel')
            )
        }
        return render(request, 'fines/process_payment.html', context)
        
    except Exception as e:
        messages.error(request, 'Unable to initiate payment. Please try again.')
        return redirect('fines:fine_detail', pk=pk)

@login_required
def payment_success_view(request):
    payment_id = request.GET.get('payment_id')
    if payment_id:
        payment = get_object_or_404(Payment, razorpay_payment_id=payment_id)
        payment.status = 'SUCCESS'
        payment.save()
        
        fine = payment.fine
        fine.status = 'PAID'
        fine.save()
        
        messages.success(request, 'Payment completed successfully!')
    return redirect('fines:fine_list')

@login_required
def payment_cancel_view(request):
    payment_id = request.GET.get('payment_id')
    if payment_id:
        payment = get_object_or_404(Payment, razorpay_payment_id=payment_id)
        payment.status = 'FAILED'
        payment.save()
        
        messages.error(request, 'Payment was cancelled. Please try again.')
    return redirect('fines:fine_list')

# Initialize Razorpay client
razorpay_client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)

class FineViewSet(viewsets.ModelViewSet):
    queryset = Fine.objects.all()
    serializer_class = FineSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'user']

    def get_queryset(self):
        user = self.request.user
        if user.role in ['ADMIN', 'LIBRARIAN']:
            return Fine.objects.all()
        return Fine.objects.filter(user=user)

    @action(detail=True, methods=['post'])
    def create_payment(self, request, pk=None):
        fine = self.get_object()
        
        if fine.status == 'PAID':
            return Response(
                {"detail": "Fine is already paid"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create Razorpay Order
        payment_order = razorpay_client.order.create({
            'amount': int(fine.amount * 100),  # Convert to paisa
            'currency': 'INR',
            'payment_capture': 1
        })

        # Create a payment record
        payment = Payment.objects.create(
            fine=fine,
            amount=fine.amount,
            payment_method='RAZORPAY',
            transaction_id=payment_order['id'],
            status='PENDING',
            razorpay_order_id=payment_order['id']
        )

        return Response({
            'payment_id': payment.id,
            'razorpay_order_id': payment_order['id'],
            'razorpay_key_id': settings.RAZORPAY_KEY_ID,
            'amount': fine.amount
        })

    @action(detail=True, methods=['post'])
    def verify_payment(self, request, pk=None):
        fine = self.get_object()
        serializer = RazorpayCallbackSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        payment = Payment.objects.get(
            razorpay_order_id=serializer.validated_data['razorpay_order_id']
        )

        # Verify signature
        params_dict = {
            'razorpay_payment_id': serializer.validated_data['razorpay_payment_id'],
            'razorpay_order_id': serializer.validated_data['razorpay_order_id'],
            'razorpay_signature': serializer.validated_data['razorpay_signature']
        }

        try:
            razorpay_client.utility.verify_payment_signature(params_dict)
            
            # Update payment status
            payment.status = 'SUCCESS'
            payment.razorpay_payment_id = serializer.validated_data['razorpay_payment_id']
            payment.razorpay_signature = serializer.validated_data['razorpay_signature']
            payment.save()

            # Update fine status
            fine.status = 'PAID'
            fine.payment_date = payment.payment_date
            fine.save()

            return Response({'status': 'Payment successful'})

        except Exception as e:
            payment.status = 'FAILED'
            payment.save()
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'payment_method']

    def get_queryset(self):
        user = self.request.user
        if user.role in ['ADMIN', 'LIBRARIAN']:
            return Payment.objects.all()
        return Payment.objects.filter(fine__user=user)
