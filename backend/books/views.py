from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
from datetime import datetime, timedelta
from .models import Book, Category, BookLoan
from .forms import BookFilterForm

@login_required
def book_list(request):
    # Get all books
    books = Book.objects.all().select_related('category')
    
    # Apply search filter
    search_query = request.GET.get('q')
    if search_query:
        books = books.filter(
            Q(title__icontains=search_query) |
            Q(author__icontains=search_query) |
            Q(isbn__icontains=search_query)
        )
    
    # Apply category filter
    categories = request.GET.getlist('category')
    if categories:
        books = books.filter(category__id__in=categories)
    
    # Apply availability filter
    if request.GET.get('available') == 'true':
        books = books.filter(available_copies__gt=0)
    
    # Pagination
    paginator = Paginator(books, 12)  # Show 12 books per page
    page = request.GET.get('page')
    books = paginator.get_page(page)
    
    # Get all categories for filter
    categories = Category.objects.all()
    
    context = {
        'books': books,
        'categories': categories,
    }
    return render(request, 'books/book_list.html', context)

@login_required
def book_detail(request, pk):
    book = get_object_or_404(Book.objects.select_related('category'), pk=pk)
    
    # Calculate expected due date (14 days from now)
    expected_due_date = datetime.now() + timedelta(days=14)
    
    context = {
        'book': book,
        'expected_due_date': expected_due_date,
    }
    return render(request, 'books/book_detail.html', context)

@login_required
def borrow_book(request, pk):
    if request.method == 'POST':
        book = get_object_or_404(Book, pk=pk)
        
        # Check if book is available
        if book.available_copies <= 0:
            messages.error(request, 'Sorry, this book is not available for borrowing.')
            return redirect('book_detail', pk=pk)
        
        # Check if user already has an active loan for this book
        if BookLoan.objects.filter(book=book, user=request.user, returned_date__isnull=True).exists():
            messages.error(request, 'You already have an active loan for this book.')
            return redirect('book_detail', pk=pk)
        
        # Create new loan
        due_date = datetime.now() + timedelta(days=14)
        BookLoan.objects.create(
            book=book,
            user=request.user,
            due_date=due_date
        )
        
        # Update book available copies
        book.available_copies -= 1
        book.save()
        
        messages.success(request, f'You have successfully borrowed "{book.title}". Please return it by {due_date.strftime("%B %d, %Y")}.')
        return redirect('my_loans')
    
    return redirect('book_detail', pk=pk)

@login_required
def return_book(request, loan_id):
    loan = get_object_or_404(BookLoan, id=loan_id, user=request.user, returned_date__isnull=True)
    
    loan.returned_date = datetime.now()
    loan.save()
    
    # Update book available copies
    loan.book.available_copies += 1
    loan.book.save()
    
    messages.success(request, f'You have successfully returned "{loan.book.title}".')
    return redirect('my_loans')

@login_required
def my_loans(request):
    # Get user's active loans
    active_loans = BookLoan.objects.filter(
        user=request.user,
        returned_date__isnull=True
    ).select_related('book')
    
    # Get user's loan history
    loan_history = BookLoan.objects.filter(
        user=request.user,
        returned_date__isnull=False
    ).select_related('book')
    
    context = {
        'active_loans': active_loans,
        'loan_history': loan_history,
    }
    return render(request, 'books/my_loans.html', context)