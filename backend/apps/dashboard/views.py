from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Sum, Avg
from django.utils import timezone
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from datetime import timedelta
from .models import DailyStats, BookActivity
from .serializers import DailyStatsSerializer, BookActivitySerializer
from apps.books.models import Book
from apps.loans.models import BookLoan
from apps.fines.models import Fine

# Web Views
@login_required
def dashboard_view(request):
    # Get basic statistics
    total_books = Book.objects.count()
    available_books = Book.objects.filter(available_copies__gt=0).count()
    total_loans = BookLoan.objects.filter(user=request.user).count()
    active_loans = BookLoan.objects.filter(user=request.user, return_date__isnull=True).count()
    
    # Get overdue books
    overdue_loans = BookLoan.objects.filter(
        user=request.user,
        return_date__isnull=True,
        due_date__lt=timezone.now()
    ).select_related('book')
    
    # Get recent loans
    recent_loans = BookLoan.objects.filter(
        user=request.user
    ).select_related('book').order_by('-issue_date')[:5]
    
    # Get outstanding fines
    outstanding_fines = Fine.objects.filter(
        user=request.user,
        payment_date__isnull=True
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    context = {
        'total_books': total_books,
        'available_books': available_books,
        'total_loans': total_loans,
        'active_loans': active_loans,
        'overdue_loans': overdue_loans,
        'recent_loans': recent_loans,
        'outstanding_fines': outstanding_fines,
    }
    
    return render(request, 'dashboard/dashboard.html', context)

@login_required
def statistics_view(request):
    # Get loans statistics
    today = timezone.now()
    thirty_days_ago = today - timedelta(days=30)
    
    monthly_loans = BookLoan.objects.filter(
        issue_date__gte=thirty_days_ago
    ).count()
    
    popular_books = Book.objects.annotate(
        loan_count=Count('loans')
    ).order_by('-loan_count')[:10]
    
    # Category distribution
    category_distribution = Book.objects.values(
        'categories__name'
    ).annotate(count=Count('id')).order_by('-count')
    
    context = {
        'monthly_loans': monthly_loans,
        'popular_books': popular_books,
        'category_distribution': category_distribution,
    }
    
    return render(request, 'dashboard/statistics.html', context)

@login_required
def book_activities_view(request):
    # Get recent activities
    recent_activities = BookLoan.objects.select_related(
        'book', 'user'
    ).order_by('-issue_date')[:20]
    
    context = {
        'recent_activities': recent_activities,
    }
    
    return render(request, 'dashboard/book_activities.html', context)

@login_required
def popular_books_view(request):
    # Get popular books based on loan count
    popular_books = Book.objects.annotate(
        loan_count=Count('loans')
    ).order_by('-loan_count')[:20]
    
    context = {
        'popular_books': popular_books,
    }
    
    return render(request, 'dashboard/popular_books.html', context)

@login_required
def overdue_loans_view(request):
    # Get all overdue loans
    overdue_loans = BookLoan.objects.filter(
        return_date__isnull=True,
        due_date__lt=timezone.now()
    ).select_related('book', 'user').order_by('due_date')
    
    context = {
        'overdue_loans': overdue_loans,
    }
    
    return render(request, 'dashboard/overdue_loans.html', context)

# API ViewSets
class DailyStatsViewSet(viewsets.ModelViewSet):
    queryset = DailyStats.objects.all()
    serializer_class = DailyStatsSerializer
    permission_classes = [permissions.IsAdminUser]

class BookActivityViewSet(viewsets.ModelViewSet):
    queryset = BookActivity.objects.all()
    serializer_class = BookActivitySerializer
    permission_classes = [permissions.IsAuthenticated]

class DailyStatsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DailyStats.objects.all()
    serializer_class = DailyStatsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role not in ['ADMIN', 'LIBRARIAN']:
            return DailyStats.objects.none()
        return DailyStats.objects.all()

    @action(detail=False)
    def current_stats(self, request):
        if request.user.role not in ['ADMIN', 'LIBRARIAN']:
            return Response({'detail': 'Not authorized'}, status=403)

        today = timezone.now().date()
        stats, _ = DailyStats.objects.get_or_create(date=today)

        # Update stats
        stats.total_loans = BookLoan.objects.filter(
            issue_date__date=today
        ).count()
        
        stats.total_returns = BookLoan.objects.filter(
            return_date__date=today
        ).count()
        
        stats.total_fines_collected = Fine.objects.filter(
            payment_date__date=today,
            status='PAID'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        stats.total_overdue_books = BookLoan.objects.filter(
            status='OVERDUE'
        ).count()
        
        stats.save()

        return Response(self.get_serializer(stats).data)

    @action(detail=False)
    def summary(self, request):
        if request.user.role not in ['ADMIN', 'LIBRARIAN']:
            return Response({'detail': 'Not authorized'}, status=403)

        # Most borrowed books
        most_borrowed = Book.objects.annotate(
            loan_count=Count('loans')
        ).order_by('-loan_count')[:5]

        # Most active users
        most_active_users = BookLoan.objects.values(
            'user__username'
        ).annotate(
            loan_count=Count('id')
        ).order_by('-loan_count')[:5]

        # Total fines collected
        total_fines = Fine.objects.filter(
            status='PAID'
        ).aggregate(total=Sum('amount'))['total'] or 0

        # Overdue books
        overdue_books = BookLoan.objects.filter(
            status='OVERDUE'
        ).count()

        return Response({
            'most_borrowed_books': [
                {
                    'title': book.title,
                    'loan_count': book.loan_count
                } for book in most_borrowed
            ],
            'most_active_users': list(most_active_users),
            'total_fines_collected': total_fines,
            'overdue_books': overdue_books
        })

class BookActivityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BookActivity.objects.all()
    serializer_class = BookActivitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role not in ['ADMIN', 'LIBRARIAN']:
            return BookActivity.objects.none()
        return BookActivity.objects.all()

    @action(detail=False)
    def recent_activities(self, request):
        activities = self.get_queryset().order_by('-timestamp')[:20]
        return Response(self.get_serializer(activities, many=True).data)
