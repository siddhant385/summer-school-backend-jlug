# Summer School Backend - JLUG

A production-ready workshop management API built with FastAPI and PostgreSQL.

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-blue.svg)](https://postgresql.org)

## Overview

A comprehensive backend system for managing educational workshops with features including user authentication, workshop registration, automated notifications, and analytics.

## Features

### Core Functionality
- **User Management** - Registration, authentication, and profile management
- **Workshop System** - Create, manage, and track workshops with timezone support
- **Registration** - Handle both registered users and guest enrollments
- **Notifications** - Automated email reminders (1-day and 15-minute)
- **Analytics** - Leaderboards, statistics, and reporting

### Technical Features
- **JWT Authentication** with role-based access control
- **Real-time Database** integration with Supabase
- **Email Service** integration with Brevo
- **Content Moderation** with spam detection
- **IST Timezone** support for accurate scheduling
- **Comprehensive Logging** and error handling

## Tech Stack

- **Framework**: FastAPI (Async Python web framework)
- **Database**: Supabase (PostgreSQL with real-time features)
- **Authentication**: JWT with python-jose
- **Email**: Brevo (SendInBlue) for transactional emails
- **Validation**: Pydantic v2 for data validation
- **Package Management**: UV for fast dependency management

## Installation

### Prerequisites
- Python 3.12+
- UV package manager
- Supabase account
- Brevo account for email services

### Setup

```bash
# Clone repository
git clone <repository-url>
cd summer-school-backend-jlug

# Install dependencies
uv sync

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Run application
python main.py
```

### Environment Variables

Create a `.env` file with the following required variables:

```env
# Database Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_key

# Security
SECRET_KEY=your_jwt_secret

# Email Service
BREVO_API_KEY=your_brevo_key
BREVO_SENDER_EMAIL=your_verified_email

# Optional
LOG_LEVEL=INFO
DEBUG=false
ENABLE_CONTENT_MODERATION=true
```

## API Documentation

Once running, access the interactive API documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Project Structure

```
app/
├── core/               # Core configurations and utilities
├── routers/            # API route handlers
├── services/           # Business logic layer
├── schemas/            # Pydantic data models
├── dependencies/       # FastAPI dependencies
├── middlewares/        # Custom middleware
└── main.py            # Application entry point
```

## Key Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User authentication
- `GET /auth/me` - Get current user

### Workshops
- `GET /workshops` - List workshops
- `POST /workshops` - Create workshop (Admin)
- `GET /workshops/{id}` - Workshop details

### Registration
- `POST /user-workshop/register/registered-user` - Enroll registered user
- `POST /user-workshop/register/guest` - Guest enrollment

### Notifications
- `POST /api/notifications/send-1day-reminders` - Send 1-day reminders
- `POST /api/notifications/send-15min-reminders` - Send 15-minute reminders

## Security

- JWT-based authentication with secure token handling
- Role-based access control (Guest, Learner, Admin)
- Input validation with Pydantic schemas
- Content moderation and spam detection
- Environment-based configuration management

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - For the excellent async web framework
- [Supabase](https://supabase.com/) - For the powerful PostgreSQL backend-as-a-service
- JLUG Community - For the educational platform

---

**Built for JLUG Summer School Program**
