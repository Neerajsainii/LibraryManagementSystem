from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta, datetime
import random
from faker import Faker

def make_aware(dt):
    if timezone.is_naive(dt):
        return timezone.make_aware(dt, timezone.get_current_timezone())
    return dt

# Import models
from apps.books.models import Author, Category, Book, BookCopy
from apps.loans.models import BookLoan, Reservation
from apps.fines.models import Fine, Payment

User = get_user_model()
fake = Faker()

class Command(BaseCommand):
    help = 'Populate the database with sample data for demonstration purposes.'

    def handle(self, *args, **options):
        self.stdout.write('Starting to populate database...')
        
        # Create superuser if not exists
        if not User.objects.filter(is_superuser=True).exists():
            self.stdout.write('Creating superuser...')
            User.objects.create_superuser(
                username='admin',
                email='admin@library.com',
                password='admin123',
                first_name='Admin',
                last_name='User'
            )

        # Create regular users
        self.stdout.write('Creating users...')
        users = []
        for i in range(1, 11):
            username = f'user{i}'
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    email=f'user{i}@example.com',
                    password='password123',
                    first_name=fake.first_name(),
                    last_name=fake.last_name()
                )
                users.append(user)
            else:
                # If user exists, get the existing user
                users.append(User.objects.get(username=username))

        # Create authors
        self.stdout.write('Creating authors...')
        authors = []
        for _ in range(10):
            author = Author.objects.create(
                name=fake.name(),
                bio=fake.paragraph()
            )
            authors.append(author)

        # Create categories
        self.stdout.write('Creating categories...')
        categories = []
        category_names = ['Fiction', 'Non-Fiction', 'Science', 'History', 'Biography', 'Technology', 'Fantasy', 'Mystery', 'Romance', 'Science Fiction']
        for name in category_names:
            category = Category.objects.create(
                name=name,
                description=fake.paragraph()
            )
            categories.append(category)

        # Create books with copies
        self.stdout.write('Creating books...')
        books = []
        for i in range(1, 31):
            book = Book.objects.create(
                title=fake.catch_phrase(),
                isbn=fake.isbn13(separator=''),
                publication_date=fake.date_between(start_date='-20y', end_date='today'),
                description='\n\n'.join(fake.paragraphs(nb=3)),
                total_copies=random.randint(1, 5),
                available_copies=0  # Will be updated after creating copies
            )
            
            # Add authors and categories
            book.authors.set(random.sample(authors, k=random.randint(1, 3)))
            book.categories.set(random.sample(categories, k=random.randint(1, 3)))
            
            # Create copies
            for copy_num in range(1, book.total_copies + 1):
                BookCopy.objects.create(
                    book=book,
                    copy_number=copy_num,
                    condition=random.choice(['NEW', 'GOOD', 'FAIR', 'POOR']),
                    acquisition_date=fake.date_between(start_date='-5y', end_date='today')
                )
            
            book.available_copies = book.total_copies  # Initially all copies are available
            book.save()
            books.append(book)

        # Create book loans
        self.stdout.write('Creating book loans...')
        for _ in range(50):
            book = random.choice(books)
            available_copies = book.copies.all()
            
            if available_copies.exists():
                book_copy = random.choice(list(available_copies))
                user = random.choice(users)
                issue_date = make_aware(fake.date_time_between(start_date='-60d', end_date='now'))
                due_date = issue_date + timedelta(days=14)
                
                # 80% chance the book is returned
                if random.random() < 0.8:
                    return_date = make_aware(fake.date_time_between(start_date=issue_date, end_date='now'))
                    status = 'RETURNED'
                else:
                    return_date = None
                    status = 'OVERDUE' if timezone.now() > due_date else 'ACTIVE'
                
                loan = BookLoan.objects.create(
                    user=user,
                    book=book,
                    book_copy=book_copy,
                    issue_date=issue_date,
                    due_date=due_date,
                    return_date=return_date,
                    status=status,
                    notes=fake.sentence() if random.random() > 0.7 else ''
                )
                
                # Update book copy status
                book_copy.status = 'ON_LOAN' if status != 'RETURNED' else 'AVAILABLE'
                book_copy.save()
                
                # Create fines for some overdue loans
                if status == 'OVERDUE' and random.random() > 0.3:
                    Fine.objects.create(
                        user=user,
                        loan=loan,
                        amount=round(random.uniform(5.0, 50.0), 2),
                        reason='Late return',
                        status=random.choice(['PENDING', 'PAID']),
                        due_date=make_aware(due_date + timedelta(days=14)),
                        payment_date=make_aware(fake.date_time_between(start_date=due_date, end_date='now')) if random.random() > 0.5 else None
                    )
        
        # Create some reservations
        self.stdout.write('Creating reservations...')
        for _ in range(20):
            book = random.choice(books)
            user = random.choice(users)
            
            # Only reserve books that are currently on loan
            if book.available_copies < book.total_copies:
                Reservation.objects.create(
                    user=user,
                    book=book,
                    status=random.choices(
                        ['PENDING', 'FULFILLED', 'CANCELLED'],
                        weights=[0.6, 0.3, 0.1]
                    )[0],
                    notification_sent=random.choice([True, False])
                )

        self.stdout.write(self.style.SUCCESS('Successfully populated database with sample data!'))
        self.stdout.write('\nAdmin login details:')
        self.stdout.write('Username: admin')
        self.stdout.write('Password: admin123')
        self.stdout.write('\nRegular user login (user1 through user10):')
        self.stdout.write('Username: user1 (through user10)')
        self.stdout.write('Password: password123')
