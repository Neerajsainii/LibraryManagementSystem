from django.contrib import admin
from .models import BookLoan, Reservation

@admin.register(BookLoan)
class BookLoanAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'issue_date', 'due_date', 'return_date', 'status')
    list_filter = ('status', 'issue_date', 'due_date')
    search_fields = ('user__username', 'book__title', 'book__isbn')
    raw_id_fields = ('user', 'book', 'book_copy')
    date_hierarchy = 'issue_date'

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'reservation_date', 'status', 'notification_sent')
    list_filter = ('status', 'notification_sent', 'reservation_date')
    search_fields = ('user__username', 'book__title', 'book__isbn')
    raw_id_fields = ('user', 'book')
