from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'check-overdue-books': {
        'task': 'apps.loans.tasks.check_overdue_books',
        'schedule': crontab(hour='0', minute='0'),  # Run daily at midnight
    },
    'send-due-date-reminders': {
        'task': 'apps.loans.tasks.send_due_date_reminders',
        'schedule': crontab(hour='9', minute='0'),  # Run daily at 9 AM
    },
    'process-reservations': {
        'task': 'apps.loans.tasks.process_reservations',
        'schedule': crontab(minute='*/15'),  # Run every 15 minutes
    },
    'cleanup-expired-reservations': {
        'task': 'apps.loans.tasks.cleanup_expired_reservations',
        'schedule': crontab(hour='*/1', minute='0'),  # Run hourly
    },
}