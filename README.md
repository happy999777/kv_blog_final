# KV Blog — Premium Django Blogging Platform

A premium, professional blogging platform with white & orange theme, built with Django + MySQL + Bootstrap 5.

## Features
- Premium white & orange UI/UX design
- Glassmorphism navbar, smooth animations
- Hero slider, featured posts, trending posts
- Category cards with hover effects
- Blog submission with approval workflow
- User registration, login, forgot password
- Author profiles and dashboards
- Admin panel with analytics charts
- Comment system with nested replies
- Like & bookmark system
- Reading progress bar
- Newsletter subscription
- Live search suggestions
- Toast notifications
- Mobile responsive with bottom nav
- SEO-friendly with dynamic meta tags
- 404/500 error pages

## Quick Start

```bash
# 1. Copy .env.example to .env and fill in values
cp .env.example .env

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create MySQL database
mysql -u root -p -e "CREATE DATABASE kvblog CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 4. Run migrations
python manage.py migrate

# 5. Collect static files
python manage.py collectstatic --noinput

# 6. Create superuser
python manage.py createsuperuser

# 7. Run server
python manage.py runserver
```

## Admin Login
- URL: `/dashboard/`
- After creating superuser above

## Deployment (Render/VPS)
```bash
# Production run
gunicorn blogplatform.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

## Credentials (local test)
- Admin: `admin` / `admin123`

## Tech Stack
- **Backend**: Django 4.2, MySQL
- **Frontend**: Bootstrap 5, Font Awesome 6, Chart.js
- **Fonts**: Plus Jakarta Sans, Inter
- **Icons**: Font Awesome 6.5
