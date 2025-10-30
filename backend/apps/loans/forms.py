from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import BookLoan, Reservation


class BookLoanForm(forms.ModelForm):
    class Meta:
        model = BookLoan
        fields = ['book']
        
    def clean_book(self):
        book = self.cleaned_data['book']
        if book.available_copies <= 0:
            raise ValidationError('This book is currently unavailable for borrowing.')
            
        # Check if user has any overdue books
        user = self.instance.user
        overdue_loans = BookLoan.objects.filter(
            user=user,
            return_date__isnull=True,
            due_date__lt=timezone.now().date()
        )
        if overdue_loans.exists():
            raise ValidationError(
                'You have overdue books. Please return them before borrowing more books.'
            )
            
        # Check if user has reached maximum allowed loans
        active_loans = BookLoan.objects.filter(
            user=user,
            return_date__isnull=True
        ).count()
        if active_loans >= 5:  # Maximum 5 books at a time
            raise ValidationError('You have reached the maximum number of allowed loans (5).')
            
        return book
        
    def save(self, commit=True):
        loan = super().save(commit=False)
        # Set due date to 14 days from now
        loan.due_date = timezone.now().date() + timezone.timedelta(days=14)
        
        if commit:
            # Update book availability
            book = loan.book
            book.available_copies -= 1
            book.save()
            
            loan.save()
            
            # Check and fulfill any reservations
            reservation = Reservation.objects.filter(
                book=book,
                fulfilled_date__isnull=True,
                cancelled_date__isnull=True
            ).first()
            if reservation:
                reservation.fulfilled_date = timezone.now()
                reservation.save()
        
        return loan


class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['book']
        
    def clean_book(self):
        book = self.cleaned_data['book']
        user = self.instance.user
        
        # Check if book is already available
        if book.available_copies > 0:
            raise ValidationError(
                'This book is currently available. No need to reserve.'
            )
            
        # Check if user already has an active reservation for this book
        existing_reservation = Reservation.objects.filter(
            user=user,
            book=book,
            fulfilled_date__isnull=True,
            cancelled_date__isnull=True
        )
        if existing_reservation.exists():
            raise ValidationError('You already have an active reservation for this book.')
            
        # Check if user has borrowed this book
        active_loan = BookLoan.objects.filter(
            user=user,
            book=book,
            return_date__isnull=True
        )
        if active_loan.exists():
            raise ValidationError('You currently have this book checked out.')
            
        return book