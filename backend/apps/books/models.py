from django.db import models
from django.core.validators import MinValueValidator

class Author(models.Model):
    name = models.CharField(max_length=200)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

class Book(models.Model):
    title = models.CharField(max_length=200)
    isbn = models.CharField(max_length=13, unique=True)
    authors = models.ManyToManyField(Author, related_name='books')
    categories = models.ManyToManyField(Category, related_name='books')
    publication_date = models.DateField()
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to='book_covers/', null=True, blank=True)
    total_copies = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    available_copies = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    ebook_file = models.FileField(upload_to='ebooks/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.isbn})"

    def update_available_copies(self):
        """Update available copies based on current loans"""
        from apps.loans.models import BookLoan
        active_loans = BookLoan.objects.filter(book=self, return_date__isnull=True).count()
        self.available_copies = self.total_copies - active_loans
        self.save()

class BookCopy(models.Model):
    CONDITION_CHOICES = (
        ('NEW', 'New'),
        ('GOOD', 'Good'),
        ('FAIR', 'Fair'),
        ('POOR', 'Poor'),
    )
    
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='copies')
    copy_number = models.PositiveIntegerField()
    condition = models.CharField(max_length=4, choices=CONDITION_CHOICES, default='NEW')
    acquisition_date = models.DateField(auto_now_add=True)
    last_maintenance = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('book', 'copy_number')
        verbose_name_plural = 'Book copies'

    def __str__(self):
        return f"{self.book.title} - Copy #{self.copy_number}"
