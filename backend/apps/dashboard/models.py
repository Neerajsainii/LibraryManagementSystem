from django.db import models
from django.conf import settings
from apps.books.models import Book

class DailyStats(models.Model):
    date = models.DateField(unique=True)
    total_loans = models.PositiveIntegerField(default=0)
    total_returns = models.PositiveIntegerField(default=0)
    total_reservations = models.PositiveIntegerField(default=0)
    total_fines_collected = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_overdue_books = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Daily stats'

    def __str__(self):
        return f"Stats for {self.date}"

class BookActivity(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='activities')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50)  # e.g., 'view', 'loan', 'return', 'reserve'
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(default=dict)

    class Meta:
        verbose_name_plural = 'Book activities'

    def __str__(self):
        return f"{self.book.title} - {self.action} by {self.user.username}"
