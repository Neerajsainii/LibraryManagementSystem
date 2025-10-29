from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from .models import Book, Category, BookLoan
from .serializers import BookSerializer, CategorySerializer, BookLoanSerializer

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Book.objects.all().select_related('category')
        
        # Search filter
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(author__icontains=search) |
                Q(isbn__icontains=search)
            )
        
        # Category filter
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category_id=category)
        
        # Availability filter
        available = self.request.query_params.get('available', None)
        if available:
            if available.lower() == 'true':
                queryset = queryset.filter(available_copies__gt=0)
            elif available.lower() == 'false':
                queryset = queryset.filter(available_copies=0)
        
        return queryset

    def get_permissions(self):
        """
        Only staff members can modify books.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    @action(detail=True, methods=['post'])
    def borrow(self, request, pk=None):
        book = self.get_object()
        user = request.user

        # Check if book is available
        if book.available_copies <= 0:
            return Response(
                {'detail': 'This book is not available for borrowing.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if user already has an active loan for this book
        if BookLoan.objects.filter(book=book, user=user, returned_date__isnull=True).exists():
            return Response(
                {'detail': 'You already have an active loan for this book.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create new loan
        due_date = timezone.now() + timedelta(days=14)
        loan = BookLoan.objects.create(
            book=book,
            user=user,
            due_date=due_date
        )

        # Update book available copies
        book.available_copies -= 1
        book.save()

        serializer = BookLoanSerializer(loan)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class BookLoanViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = BookLoanSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Users can only see their own loans.
        Staff can see all loans.
        """
        if self.request.user.is_staff:
            return BookLoan.objects.all().select_related('book', 'user')
        return BookLoan.objects.filter(user=self.request.user).select_related('book')

    @action(detail=True, methods=['post'])
    def return_book(self, request, pk=None):
        loan = self.get_object()
        
        # Check if loan belongs to user
        if loan.user != request.user and not request.user.is_staff:
            return Response(
                {'detail': 'You do not have permission to return this book.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if book is already returned
        if loan.returned_date:
            return Response(
                {'detail': 'This book has already been returned.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Return the book
        loan.returned_date = timezone.now()
        loan.save()
        
        # Update book available copies
        loan.book.available_copies += 1
        loan.book.save()
        
        serializer = BookLoanSerializer(loan)
        return Response(serializer.data)