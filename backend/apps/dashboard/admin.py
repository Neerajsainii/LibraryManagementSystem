from django.contrib import admin
from .models import DailyStats, BookActivity

@admin.register(DailyStats)
class DailyStatsAdmin(admin.ModelAdmin):
    list_display = ('date', 'total_loans', 'total_returns', 'total_reservations', 'total_fines_collected', 'total_overdue_books')
    list_filter = ('date',)
    date_hierarchy = 'date'

@admin.register(BookActivity)
class BookActivityAdmin(admin.ModelAdmin):
    list_display = ('book', 'user', 'action', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('book__title', 'user__username', 'action')
    raw_id_fields = ('book', 'user')
