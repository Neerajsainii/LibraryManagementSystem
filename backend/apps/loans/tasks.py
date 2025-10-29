from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from apps.loans.models import BookLoan, Reservation
from apps.fines.models import Fine

@shared_task
def check_overdue_books():
    # Find all active loans that are overdue
    overdue_loans = BookLoan.objects.filter(
        status='ACTIVE',
        due_date__lt=timezone.now()
    )

    for loan in overdue_loans:
        # Update loan status
        loan.status = 'OVERDUE'
        loan.save()

        # Create fine if not already created
        if not Fine.objects.filter(loan=loan).exists():
            days_overdue = (timezone.now() - loan.due_date).days
            fine_amount = days_overdue * 1.0  # $1 per day

            Fine.objects.create(
                user=loan.user,
                loan=loan,
                amount=fine_amount,
                reason=f"Book overdue by {days_overdue} days",
                due_date=timezone.now() + timedelta(days=7)
            )

        # Send email notification
        send_mail(
            'Book Overdue Notice',
            f'Dear {loan.user.get_full_name()},\n\n'
            f'The book "{loan.book.title}" is overdue. '
            f'Please return it as soon as possible to avoid additional fines.',
            settings.DEFAULT_FROM_EMAIL,
            [loan.user.email],
            fail_silently=True
        )

@shared_task
def send_due_date_reminders():
    # Find loans due in 2 days
    upcoming_due = BookLoan.objects.filter(
        status='ACTIVE',
        due_date__date=timezone.now().date() + timedelta(days=2)
    )

    for loan in upcoming_due:
        send_mail(
            'Book Due Date Reminder',
            f'Dear {loan.user.get_full_name()},\n\n'
            f'The book "{loan.book.title}" is due in 2 days. '
            f'Please return it on time to avoid fines.',
            settings.DEFAULT_FROM_EMAIL,
            [loan.user.email],
            fail_silently=True
        )

@shared_task
def process_reservations():
    # Find books with available copies
    available_books = set(
        BookLoan.objects.filter(
            return_date__date=timezone.now().date()
        ).values_list('book_id', flat=True)
    )

    for book_id in available_books:
        # Find oldest pending reservation for this book
        reservation = Reservation.objects.filter(
            book_id=book_id,
            status='PENDING'
        ).order_by('reservation_date').first()

        if reservation:
            # Send notification
            send_mail(
                'Book Available for Pickup',
                f'Dear {reservation.user.get_full_name()},\n\n'
                f'The book "{reservation.book.title}" is now available. '
                f'Please visit the library to check it out within 48 hours.',
                settings.DEFAULT_FROM_EMAIL,
                [reservation.user.email],
                fail_silently=True
            )

            reservation.notification_sent = True
            reservation.save()

@shared_task
def cleanup_expired_reservations():
    # Find reservations that were notified 48+ hours ago but not fulfilled
    expired = Reservation.objects.filter(
        notification_sent=True,
        status='PENDING',
        updated_at__lt=timezone.now() - timedelta(hours=48)
    )

    for reservation in expired:
        # Cancel the reservation
        reservation.status = 'CANCELLED'
        reservation.save()

        # Notify the next person in line
        next_reservation = Reservation.objects.filter(
            book=reservation.book,
            status='PENDING'
        ).order_by('reservation_date').first()

        if next_reservation:
            send_mail(
                'Book Available for Pickup',
                f'Dear {next_reservation.user.get_full_name()},\n\n'
                f'The book "{next_reservation.book.title}" is now available. '
                f'Please visit the library to check it out within 48 hours.',
                settings.DEFAULT_FROM_EMAIL,
                [next_reservation.user.email],
                fail_silently=True
            )

            next_reservation.notification_sent = True
            next_reservation.save()