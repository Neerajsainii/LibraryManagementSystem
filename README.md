# Library Management System

A comprehensive Django-based Library Management System with RESTful APIs.

## Features

- Book cataloging with full metadata support
- User management with role-based access control
- Book issuing and returning system
- Reservation and waiting list management
- Fine calculation and payment integration (Razorpay)
- Email notifications for due dates and reservations
- Admin dashboard with detailed statistics
- Bulk import/export functionality
- E-book/PDF support

## Tech Stack

- Backend: Django + Django REST Framework
- Database: PostgreSQL
- Task Queue: Celery + Redis
- Payment Gateway: Razorpay
- Authentication: Django AllAuth

## Setup Instructions

1. Clone the repository:
```bash
git clone <repository-url>
cd library_management_system
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements/dev.txt
```

4. Create a `.env` file in the backend directory with the following content:
```env
DJANGO_SECRET_KEY=your-secret-key
DB_NAME=library_db
DB_USER=your-db-user
DB_PASSWORD=your-db-password
DB_HOST=localhost
DB_PORT=5432
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-email-password
RAZORPAY_KEY_ID=your-razorpay-key
RAZORPAY_KEY_SECRET=your-razorpay-secret
```

5. Create the database:
```bash
createdb library_db
```

6. Run migrations:
```bash
cd backend
python manage.py migrate
```

7. Create a superuser:
```bash
python manage.py createsuperuser
```

8. Start Redis server:
```bash
redis-server
```

9. Start Celery worker:
```bash
celery -A library_system worker -l info
```

10. Start Celery beat:
```bash
celery -A library_system beat -l info
```

11. Run the development server:
```bash
python manage.py runserver
```

## API Documentation

The API documentation is available at `/api/docs/` when the server is running.

## Testing

To run tests:
```bash
python manage.py test
```

## Production Deployment

For production deployment:

1. Update settings:
```bash
export DJANGO_SETTINGS_MODULE=library_system.settings.prod
```

2. Install production dependencies:
```bash
pip install -r requirements/prod.txt
```

3. Configure your web server (e.g., Nginx) to serve static and media files.

4. Use Gunicorn as the production server:
```bash
gunicorn library_system.wsgi:application
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License.