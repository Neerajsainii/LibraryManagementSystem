from rest_framework import serializers
from .models import BookLoan, Reservation
from apps.books.serializers import BookSerializer
from apps.books.models import Book
from apps.accounts.serializers import UserSerializer

class BookLoanSerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    book_id = serializers.PrimaryKeyRelatedField(
        source='book',
        queryset=Book.objects.all(),
        write_only=True
    )

    class Meta:
        model = BookLoan
        fields = ('id', 'user', 'book', 'book_id', 'book_copy', 'issue_date',
                 'due_date', 'return_date', 'status', 'notes', 'created_at')
        read_only_fields = ('issue_date', 'created_at', 'status')

class ReservationSerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    book_id = serializers.PrimaryKeyRelatedField(
        source='book',
        queryset=Book.objects.all(),
        write_only=True
    )

    class Meta:
        model = Reservation
        fields = ('id', 'user', 'book', 'book_id', 'reservation_date',
                 'status', 'notification_sent', 'fulfillment_date', 'created_at')
        read_only_fields = ('reservation_date', 'created_at', 'notification_sent',
                           'fulfillment_date')