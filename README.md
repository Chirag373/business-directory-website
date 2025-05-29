# Business Directory Website

A Django-based platform for connecting customers with local handyman services.

## Installation

1. Clone the repository
   ```
   git clone https://github.com/yourusername/business-directory-website.git
   cd business-directory-website
   ```

2. Create and activate virtual environment
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies
   ```
   pip install -r requirements.txt
   ```

4. Setup database
   ```
   python manage.py migrate
   ```

5. Create superuser
   ```
   python manage.py createsuperuser
   ```

## Running the Application

```
python manage.py runserver
```

Access the site at http://127.0.0.1:8000/

Admin dashboard: http://127.0.0.1:8000/admin/

## Features

- User registration and authentication
- Handyman service listings with detailed profiles
- Search functionality by service type and location
- Business dashboards for service providers
- Customer reviews and ratings

## Technologies

- Django
- PostgreSQL
- HTML/CSS/JavaScript
- Bootstrap