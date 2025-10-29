from rest_framework import serializers
from .models import Book, Category, BookLoan

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class BookSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    current_loan = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            'id', 'title', 'author', 'isbn', 'description', 'category',
            'publisher', 'publication_year', 'cover_image', 'available_copies',
            'total_copies', 'is_available', 'current_loan'
        ]

    def get_current_loan(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            loan = obj.loans.filter(
                user=request.user,
                returned_date__isnull=True
            ).first()
            if loan:
                return {
                    'id': loan.id,
                    'borrowed_date': loan.borrowed_date,
                    'due_date': loan.due_date,
                    'is_overdue': loan.is_overdue
                }
        return None

class BookLoanSerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)
    user = serializers.StringRelatedField()
    is_overdue = serializers.BooleanField(read_only=True)
    days_overdue = serializers.IntegerField(read_only=True)
    was_returned_late = serializers.BooleanField(read_only=True)

    class Meta:
        model = BookLoan
        fields = [
            'id', 'book', 'user', 'borrowed_date', 'due_date',
            'returned_date', 'is_overdue', 'days_overdue', 'was_returned_late'
        ]