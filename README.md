# 🌟 Summer School Backend - JLUG

Welcome to the **Summer School Backend** - a comprehensive workshop management system built with modern Python and FastAPI! 🎓

## 🚀 Features

### ✅ Current Features
- **🔐 JWT Authentication**: Secure user login and role-based access control
- **📚 Workshop Management**: Complete CRUD operations for workshops
- **👥 User Roles**: Support for Guest, Learner, and Admin roles
- **🔍 Smart Search**: Search workshops by technology and filters
- **📊 Dashboard Stats**: Workshop statistics and upcoming events
- **🏥 Health Monitoring**: Comprehensive health check endpoints
- **🌐 CORS Support**: Configured for GitHub Codespaces and development
- **📝 Smart Logging**: Structured logging with debug and production modes
- **🎯 Clean Architecture**: Modular design with separated concerns

### 🛠️ Tech Stack
- **FastAPI** - Modern, fast web framework
- **Pydantic v2** - Data validation and serialization
- **Supabase** - Backend-as-a-Service database
- **JWT** - JSON Web Token authentication
- **UV** - Fast Python package manager
- **Python 3.12** - Latest Python features

## 🏃‍♂️ Quick Start

### Prerequisites
- Python 3.12+
- UV package manager
- Supabase account

### Installation

1. **Clone & Navigate**
   ```bash
   git clone <repo-url>
   cd summer-school-backend-jlug
   ```

2. **Install Dependencies**
   ```bash
   uv sync
   ```

3. **Environment Setup**
   ```bash
   cp .env.example .env
   # Add your Supabase credentials
   ```

4. **Run the Server**
   ```bash
   python -m app.main
   # or
   uvicorn app.main:app --reload
   ```

5. **Visit API Docs**
   - Swagger UI: `http://localhost:8000/docs` 📖
   - ReDoc: `http://localhost:8000/redoc` 📚

## 📁 Project Structure

```
app/
├── core/           # Core configurations
│   ├── config.py   # Settings and environment
│   ├── db.py       # Database connection
│   └── logger.py   # Logging setup
├── routers/        # API endpoints
│   ├── auth.py     # Authentication routes
│   ├── workshops.py # Workshop CRUD
│   └── health.py   # Health checks
├── services/       # Business logic
│   ├── auth.py     # Auth services
│   └── workshop.py # Workshop services
├── schemas/        # Pydantic models
├── dependencies/   # FastAPI dependencies
└── middlewares/    # Custom middlewares
```

## 🎯 API Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/register` - User registration

### Workshops
- `GET /workshops` - List workshops with filters
- `POST /workshops` - Create workshop (Admin)
- `GET /workshops/{id}` - Get workshop details
- `PUT /workshops/{id}` - Update workshop (Admin)
- `DELETE /workshops/{id}` - Delete workshop (Admin)

### Health & Stats
- `GET /` - API information
- `GET /health` - Basic health check
- `GET /health/status` - Detailed system status
- `GET /workshops/stats` - Workshop statistics

## 🔧 Configuration

Key environment variables:
```env
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_key
SECRET_KEY=your_jwt_secret
LOG_LEVEL=INFO  # or DEBUG for development
```

## 📝 Logging

The application uses structured logging with:
- **Console Output**: Colored logs for development
- **File Logging**: Persistent logs in `app.log`
- **Debug Mode**: Verbose logging for troubleshooting
- **Production Mode**: Clean, essential logs only

## 🔜 Upcoming Features

### 🚧 In Development
- **👤 User Profiles**: Enhanced user management with profiles
- **📋 Assignments**: Workshop assignments and submissions
- **⭐ Reviews & Ratings**: User feedback system for workshops
- **🏆 Certificates**: Automated certificate generation
- **📧 Notifications**: Email and in-app notifications
- **🔍 Advanced Search**: Full-text search with Elasticsearch
- **📱 Real-time Updates**: WebSocket support for live updates

### 🎨 Planned Enhancements
- **📊 Advanced Analytics**: Detailed workshop and user analytics
- **🎯 Recommendation Engine**: Personalized workshop recommendations
- **🌍 Multi-language Support**: Internationalization (i18n)
- **📤 Export Features**: PDF reports and data exports
- **🔒 Advanced Security**: Rate limiting, CAPTCHA integration
- **☁️ Cloud Storage**: File uploads and media management
- **🎨 Themes**: Customizable UI themes and branding

### 🏗️ Technical Roadmap
- **🧪 Testing Suite**: Comprehensive unit and integration tests
- **🐳 Docker Support**: Containerization for easy deployment
- **🚀 CI/CD Pipeline**: Automated testing and deployment
- **📚 API Versioning**: Backward compatibility support
- **🔄 Database Migrations**: Automated schema management
- **📈 Performance Monitoring**: APM integration
- **🛡️ Security Auditing**: Regular security assessments

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **JLUG Community** for the inspiration
- **FastAPI Team** for the amazing framework
- **Supabase** for the excellent backend services

---

<div align="center">
  <b>Built with ❤️ for the JLUG Summer School Program</b><br>
  <sub>Ready to learn, grow, and build amazing things together! 🚀</sub>
</div>
