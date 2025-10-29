from rest_framework import serializers
from .models import Author, Category, Book, BookCopy

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ('id', 'name', 'bio', 'created_at')
        read_only_fields = ('created_at',)

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'description', 'created_at')
        read_only_fields = ('created_at',)

class BookCopySerializer(serializers.ModelSerializer):
    class Meta:
        model = BookCopy
        fields = ('id', 'copy_number', 'condition', 'acquisition_date',
                 'last_maintenance', 'notes')
        read_only_fields = ('acquisition_date',)

class BookSerializer(serializers.ModelSerializer):
    authors = AuthorSerializer(many=True, read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    copies = BookCopySerializer(many=True, read_only=True)
    author_ids = serializers.PrimaryKeyRelatedField(
        queryset=Author.objects.all(),
        many=True,
        write_only=True,
        source='authors'
    )
    category_ids = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        many=True,
        write_only=True,
        source='categories'
    )

    class Meta:
        model = Book
        fields = ('id', 'title', 'isbn', 'authors', 'categories', 'publication_date',
                 'description', 'cover_image', 'total_copies', 'available_copies',
                 'ebook_file', 'created_at', 'copies', 'author_ids', 'category_ids')
        read_only_fields = ('created_at', 'available_copies')

    def validate_isbn(self, value):
        """Validate ISBN format"""
        if not value.isdigit() or len(value) not in [10, 13]:
            raise serializers.ValidationError("ISBN must be 10 or 13 digits")
        return value

class BookBulkUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

    def validate_file(self, value):
        """Validate file extension"""
        if not value.name.endswith(('.csv', '.xlsx')):
            raise serializers.ValidationError("Only CSV and Excel files are supported")
        return value