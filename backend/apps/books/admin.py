from django.contrib import admin
from .models import Author, Category, Book, BookCopy

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)

class BookCopyInline(admin.TabularInline):
    model = BookCopy
    extra = 1

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'isbn', 'publication_date', 'total_copies', 'available_copies')
    list_filter = ('categories', 'publication_date')
    search_fields = ('title', 'isbn', 'authors__name')
    filter_horizontal = ('authors', 'categories')
    inlines = [BookCopyInline]

@admin.register(BookCopy)
class BookCopyAdmin(admin.ModelAdmin):
    list_display = ('book', 'copy_number', 'condition', 'acquisition_date')
    list_filter = ('condition', 'acquisition_date')
    search_fields = ('book__title', 'book__isbn')
