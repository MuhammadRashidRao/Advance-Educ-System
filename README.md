# Education System - Authentication & Authorization

A complete Django-based authentication and authorization system with modern UI design and comprehensive user management features.

## Features

### 🔐 Authentication Features
- **User Registration**: Complete registration form with validation
- **User Login**: Secure login with username/email
- **User Logout**: Secure logout functionality
- **Password Reset**: Complete forgot password workflow via email
- **Password Change**: Change password while logged in
- **Profile Management**: Edit user profile information

### 🎨 UI/UX Features
- **Modern Design**: Bootstrap 5 with custom styling
- **Responsive Layout**: Mobile-friendly design
- **Interactive Elements**: Hover effects and animations
- **Form Validation**: Real-time validation with helpful messages
- **Password Strength Indicator**: Visual password strength feedback
- **Profile Picture Upload**: Image upload with preview

### 🔒 Security Features
- **CSRF Protection**: Built-in Django CSRF protection
- **Password Validation**: Strong password requirements
- **Session Management**: Secure session handling
- **Email Verification**: Password reset via email
- **Login Required Decorators**: Protected views

## Installation & Setup

### Prerequisites
- Python 3.8+
- Django 5.2+
- Virtual environment (recommended)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd educ
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install django
   ```

4. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server**
   ```bash
   python manage.py runserver
   ```

7. **Access the application**
   - Main site: http://127.0.0.1:8000/
   - Admin panel: http://127.0.0.1:8000/admin/
   - Login: http://127.0.0.1:8000/auth/login/

## Default Admin Credentials
- **Username**: admin
- **Password**: admin123
- **Email**: admin@example.com

## URL Structure

### Public URLs
- `/` - Home page
- `/auth/register/` - User registration
- `/auth/login/` - User login
- `/auth/password-reset/` - Password reset request
- `/auth/password-reset/done/` - Password reset email sent
- `/auth/password-reset-confirm/<uidb64>/<token>/` - Set new password
- `/auth/password-reset-complete/` - Password reset complete

### Protected URLs (Login Required)
- `/auth/dashboard/` - User dashboard
- `/auth/profile/` - Profile management
- `/auth/change-password/` - Change password

### Admin URLs
- `/admin/` - Django admin interface

## Features in Detail

### 1. User Registration
- Comprehensive registration form
- Real-time validation
- Password strength indicator
- Email verification ready
- Automatic profile creation

### 2. User Login
- Username or email login
- Remember me functionality
- Secure session management
- Redirect to dashboard after login

### 3. Password Reset
- Email-based password reset
- Secure token generation
- Time-limited reset links
- Beautiful email templates

### 4. Profile Management
- Edit personal information
- Upload profile pictures
- Update contact details
- Bio and address fields

### 5. Dashboard
- Welcome message with user info
- Quick stats display
- Recent activity section
- Quick action buttons

## Customization

### Email Configuration
For production, update email settings in `settings.py`:

```python
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
```

### Styling
- Custom CSS in `static/css/style.css`
- Bootstrap 5 framework
- Font Awesome icons
- Responsive design

### Models
- `UserProfile`: Extended user model with additional fields
- Automatic profile creation on user registration
- One-to-one relationship with Django User model

## Security Considerations

1. **Password Security**
   - Minimum 8 characters
   - Cannot be entirely numeric
   - Cannot be too similar to personal info
   - Cannot be commonly used

2. **Session Security**
   - CSRF protection enabled
   - Secure session handling
   - Automatic logout on password change

3. **Email Security**
   - Token-based password reset
   - Time-limited reset links
   - Secure email templates

## File Structure

```
educ/
├── authentication/          # Authentication app
│   ├── models.py           # UserProfile model
│   ├── views.py            # Authentication views
│   ├── forms.py            # Custom forms
│   ├── urls.py             # URL patterns
│   └── admin.py            # Admin interface
├── educ_system/            # Project settings
│   ├── settings.py         # Django settings
│   └── urls.py             # Main URL configuration
├── templates/              # HTML templates
│   ├── base.html           # Base template
│   └── authentication/     # Auth templates
├── static/                 # Static files
│   ├── css/style.css       # Custom styles
│   └── js/script.js        # Custom JavaScript
└── manage.py              # Django management script
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions, please open an issue on the repository.

---

**Note**: This is a development setup. For production deployment, ensure to:
- Change the `SECRET_KEY`
- Set `DEBUG = False`
- Configure proper email settings
- Use HTTPS
- Set up proper database (PostgreSQL recommended)
- Configure static file serving
