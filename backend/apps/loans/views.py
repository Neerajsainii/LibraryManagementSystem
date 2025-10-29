from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta
from rest_framework import viewsets, status, filters, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import BookLoan, Reservation
from .serializers import BookLoanSerializer, ReservationSerializer
from .forms import BookLoanForm, ReservationForm
from apps.books.models import Book, BookCopy
from apps.fines.models import Fine

# Web Views
@login_required
def loan_list_view(request):
    active_loans = BookLoan.objects.filter(
        user=request.user,
        returned_date__isnull=True
    ).select_related('book')
    
    past_loans = BookLoan.objects.filter(
        user=request.user,
        returned_date__isnull=False
    ).select_related('book').order_by('-returned_date')
    
    context = {
        'active_loans': active_loans,
        'past_loans': past_loans,
    }
    return render(request, 'loans/loan_list.html', context)

@login_required
def loan_detail_view(request, pk):
    loan = get_object_or_404(
        BookLoan.objects.select_related('book', 'user'),
        pk=pk,
        user=request.user
    )
    return render(request, 'loans/loan_detail.html', {'loan': loan})

@login_required
def create_loan_view(request):
    if request.method == 'POST':
        form = BookLoanForm(request.POST)
        if form.is_valid():
            loan = form.save(commit=False)
            loan.user = request.user
            loan.save()
            messages.success(request, f'Successfully borrowed {loan.book.title}')
            return redirect('loans:loan_detail', pk=loan.pk)
    else:
        form = BookLoanForm()
    
    return render(request, 'loans/loan_form.html', {'form': form})

@login_required
def return_loan_view(request, pk):
    loan = get_object_or_404(
        BookLoan.objects.select_related('book'),
        pk=pk,
        user=request.user,
        returned_date__isnull=True
    )
    
    if request.method == 'POST':
        loan.returned_date = timezone.now()
        loan.save()
        
        # Update book availability
        book = loan.book
        book.available_copies += 1
        book.save()
        
        # Calculate and create fine if overdue
        if loan.is_overdue:
            days_overdue = (timezone.now().date() - loan.due_date).days
            fine_amount = days_overdue * 1.00  # $1 per day
            Fine.objects.create(
                loan=loan,
                user=request.user,
                amount=fine_amount,
                reason=f'Book returned {days_overdue} days late'
            )
            messages.warning(
                request,
                f'Book returned late. A fine of ${fine_amount:.2f} has been added to your account.'
            )
        else:
            messages.success(request, 'Book returned successfully!')
        
        return redirect('loans:loan_list')
    
    return render(request, 'loans/return_confirm.html', {'loan': loan})

@login_required
def reservation_list_view(request):
    active_reservations = Reservation.objects.filter(
        user=request.user,
        fulfilled_date__isnull=True,
        cancelled_date__isnull=True
    ).select_related('book')
    
    past_reservations = Reservation.objects.filter(
        user=request.user
    ).exclude(
        fulfilled_date__isnull=True,
        cancelled_date__isnull=True
    ).select_related('book').order_by('-created_date')
    
    context = {
        'active_reservations': active_reservations,
        'past_reservations': past_reservations,
    }
    return render(request, 'loans/reservation_list.html', context)

@login_required
def create_reservation_view(request):
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.user = request.user
            reservation.save()
            messages.success(request, f'Successfully reserved {reservation.book.title}')
            return redirect('loans:reservation_list')
    else:
        form = ReservationForm()
    
    return render(request, 'loans/reservation_form.html', {'form': form})

@login_required
def cancel_reservation_view(request, pk):
    reservation = get_object_or_404(
        Reservation,
        pk=pk,
        user=request.user,
        fulfilled_date__isnull=True,
        cancelled_date__isnull=True
    )
    
    if request.method == 'POST':
        reservation.cancelled_date = timezone.now()
        reservation.save()
        messages.success(request, 'Reservation cancelled successfully!')
        return redirect('loans:reservation_list')
    
    return render(request, 'loans/cancel_reservation_confirm.html', {'reservation': reservation})

class BookLoanViewSet(viewsets.ModelViewSet):
    queryset = BookLoan.objects.all()
    serializer_class = BookLoanSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status', 'book']
    search_fields = ['book__title', 'user__username']

    def get_queryset(self):
        user = self.request.user
        if user.role in ['ADMIN', 'LIBRARIAN']:
            return BookLoan.objects.all()
        return BookLoan.objects.filter(user=user)

    def perform_create(self, serializer):
        book = serializer.validated_data['book']
        
        # Check if user has any overdue books
        has_overdue = BookLoan.objects.filter(
            user=self.request.user,
            status='OVERDUE'
        ).exists()
        
        if has_overdue:
            raise serializers.ValidationError(
                "Cannot borrow books while you have overdue items"
            )

        # Check if book is available
        if book.available_copies <= 0:
            raise serializers.ValidationError("Book is not available")

        # Get available copy
        book_copy = BookCopy.objects.filter(
            book=book,
            loans__isnull=True
        ).first()

        if not book_copy:
            raise serializers.ValidationError("No copies available")

        # Set due date (e.g., 14 days from now)
        due_date = timezone.now() + timedelta(days=14)

        serializer.save(
            user=self.request.user,
            book_copy=book_copy,
            due_date=due_date,
            status='ACTIVE'
        )

    @action(detail=True, methods=['post'])
    def return_book(self, request, pk=None):
        loan = self.get_object()
        if loan.status not in ['ACTIVE', 'OVERDUE']:
            return Response(
                {"detail": "Book is not currently borrowed"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Calculate any fines
        if loan.status == 'OVERDUE' or timezone.now() > loan.due_date:
            days_overdue = (timezone.now() - loan.due_date).days
            fine_amount = days_overdue * 1.0  # $1 per day
            
            Fine.objects.create(
                user=loan.user,
                loan=loan,
                amount=fine_amount,
                reason=f"Book returned {days_overdue} days late",
                due_date=timezone.now() + timedelta(days=7)
            )

        # Update loan status
        loan.return_date = timezone.now()
        loan.status = 'RETURNED'
        loan.save()

        # Update book availability
        loan.book.update_available_copies()

        # Check for reservations
        reservation = Reservation.objects.filter(
            book=loan.book,
            status='PENDING'
        ).first()

        if reservation:
            reservation.status = 'FULFILLED'
            reservation.fulfillment_date = timezone.now()
            reservation.notification_sent = True
            reservation.save()

        return Response({"status": "Book returned successfully"})

class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status', 'book']
    search_fields = ['book__title', 'user__username']

    def get_queryset(self):
        user = self.request.user
        if user.role in ['ADMIN', 'LIBRARIAN']:
            return Reservation.objects.all()
        return Reservation.objects.filter(user=user)

    def perform_create(self, serializer):
        book = serializer.validated_data['book']
        
        # Check if book is already available
        if book.available_copies > 0:
            raise serializers.ValidationError(
                "Book is currently available. No need to reserve."
            )

        # Check if user already has an active reservation for this book
        existing_reservation = Reservation.objects.filter(
            user=self.request.user,
            book=book,
            status='PENDING'
        ).exists()

        if existing_reservation:
            raise serializers.ValidationError(
                "You already have an active reservation for this book"
            )

        serializer.save(user=self.request.user)
