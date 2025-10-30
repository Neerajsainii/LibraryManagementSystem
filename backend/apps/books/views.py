from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from .models import Author, Category, Book, BookCopy
from .serializers import (
    AuthorSerializer, CategorySerializer,
    BookSerializer, BookCopySerializer,
    BookBulkUploadSerializer)
from django import forms
from .models import Book, BookCopy

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'isbn', 'authors', 'categories', 'publication_date', 
                 'description', 'cover_image', 'total_copies']
        widgets = {
            'publication_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class BookCopyForm(forms.ModelForm):
    class Meta:
        model = BookCopy
        fields = ['book', 'copy_number', 'condition']

# Web Views
@login_required
def book_list_view(request):
    books = Book.objects.all().prefetch_related('authors', 'categories')
    
    # Search functionality
    query = request.GET.get('q')
    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(authors__name__icontains=query) |
            Q(isbn__icontains=query) |
            Q(category__name__icontains=query)
        ).distinct()
    
    # Category filter
    category_id = request.GET.get('category')
    if category_id:
        books = books.filter(category_id=category_id)
    
    # Availability filter
    availability = request.GET.get('available')
    if availability:
        if availability == 'true':
            books = books.filter(available_copies__gt=0)
        elif availability == 'false':
            books = books.filter(available_copies=0)
    
    # Pagination
    paginator = Paginator(books, 12)  # Show 12 books per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all categories for filter
    categories = Category.objects.annotate(book_count=Count('books'))
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'query': query,
        'selected_category': category_id,
        'selected_availability': availability,
    }
    return render(request, 'books/book_list.html', context)

@login_required
def book_detail_view(request, pk):
    book = get_object_or_404(
        Book.objects.prefetch_related('authors', 'categories', 'copies'),
        pk=pk
    )
    
    # Get book statistics
    book_stats = {
        'rating': 0,  # Reviews not implemented yet
        'review_count': 0,  # Reviews not implemented yet
        'loan_count': book.loans.count() if hasattr(book, 'loans') else 0,
    }
    
    # Get similar books (by shared categories or same authors)
    similar_books = Book.objects.filter(
        Q(categories__in=book.categories.all()) |
        Q(authors__in=book.authors.all())
    ).exclude(pk=book.pk).distinct()[:4]
    
    context = {
        'book': book,
        'book_stats': book_stats,
        'similar_books': similar_books,
    }
    return render(request, 'books/book_detail.html', context)

@login_required
def category_list_view(request):
    categories = Category.objects.annotate(
        book_count=Count('books'),
        available_books=Count('books', filter=Q(books__available_copies__gt=0))
    )
    return render(request, 'books/category_list.html', {'categories': categories})

@login_required
def author_list_view(request):
    authors = Author.objects.annotate(
        book_count=Count('books'),
        avg_rating=Avg('books__reviews__rating')
    )
    return render(request, 'books/author_list.html', {'authors': authors})

@login_required
def book_search_view(request):
    query = request.GET.get('q', '')
    results = []
    
    if query:
        results = Book.objects.filter(
            Q(title__icontains=query) |
            Q(authors__name__icontains=query) |
            Q(isbn__icontains=query) |
            Q(category__name__icontains=query)
        ).distinct()
    
    context = {
        'query': query,
        'results': results,
    }
    return render(request, 'books/search_results.html', context)

# Staff only views
@user_passes_test(lambda u: u.is_staff)
def manage_books_view(request):
    books = Book.objects.all().prefetch_related('authors', 'categories')
    return render(request, 'books/manage_books.html', {'books': books})

@user_passes_test(lambda u: u.is_staff)
def book_create_view(request):
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save()
            messages.success(request, f'Book "{book.title}" was created successfully.')
            return redirect('books:book_detail', pk=book.pk)
    else:
        form = BookForm()
    
    return render(request, 'books/book_form.html', {'form': form, 'action': 'Create'})

@user_passes_test(lambda u: u.is_staff)
def book_edit_view(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            book = form.save()
            messages.success(request, f'Book "{book.title}" was updated successfully.')
            return redirect('books:book_detail', pk=book.pk)
    else:
        form = BookForm(instance=book)
    
    return render(request, 'books/book_form.html', {'form': form, 'action': 'Edit'})

@user_passes_test(lambda u: u.is_staff)
def book_delete_view(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        book.delete()
        messages.success(request, f'Book "{book.title}" was deleted successfully.')
        return redirect('books:manage_books')
    
    return render(request, 'books/book_confirm_delete.html', {'book': book})

import pandas as pd

class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    parser_classes = (MultiPartParser, FormParser)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['categories', 'authors', 'publication_date']
    search_fields = ['title', 'isbn', 'authors__name', 'categories__name']
    ordering_fields = ['title', 'publication_date', 'available_copies']

    @action(detail=False, methods=['post'])
    def bulk_upload(self, request):
        serializer = BookBulkUploadSerializer(data=request.data)
        if serializer.is_valid():
            file = serializer.validated_data['file']
            
            try:
                if file.name.endswith('.csv'):
                    df = pd.read_csv(file)
                else:  # Excel file
                    df = pd.read_excel(file)

                books_created = 0
                for _, row in df.iterrows():
                    try:
                        # Create or get authors
                        author_names = row['authors'].split(',')
                        authors = [
                            Author.objects.get_or_create(name=name.strip())[0]
                            for name in author_names
                        ]

                        # Create or get categories
                        category_names = row['categories'].split(',')
                        categories = [
                            Category.objects.get_or_create(name=name.strip())[0]
                            for name in category_names
                        ]

                        # Create book
                        book = Book.objects.create(
                            title=row['title'],
                            isbn=row['isbn'],
                            publication_date=row['publication_date'],
                            description=row.get('description', ''),
                            total_copies=row['total_copies'],
                            available_copies=row['total_copies']
                        )

                        # Add relationships
                        book.authors.add(*authors)
                        book.categories.add(*categories)

                        # Create book copies
                        for i in range(int(row['total_copies'])):
                            BookCopy.objects.create(
                                book=book,
                                copy_number=i + 1,
                                condition='NEW'
                            )

                        books_created += 1

                    except Exception as e:
                        continue

                return Response({
                    'status': 'success',
                    'books_created': books_created
                })

            except Exception as e:
                return Response({
                    'status': 'error',
                    'message': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BookCopyViewSet(viewsets.ModelViewSet):
    queryset = BookCopy.objects.all()
    serializer_class = BookCopySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['book', 'condition']
