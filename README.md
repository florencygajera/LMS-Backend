# Agniveer Sentinel - Military Training & Recruitment Platform

A comprehensive national-level military training and recruitment platform for Agniveer soldiers, built with Python FastAPI, PostgreSQL, and a modular service architecture.

## 📋 Overview

This platform consists of two main phases:

### Phase 1: Recruitment System
- Online application submission
- Document upload and verification
- Admit card generation with QR code
- Email and SMS notifications
- Common Entrance Test (CET) management
- Question bank and exam scheduling
- Result generation

### Phase 2: Soldier Management LMS
- Soldier profile management
- Medical record tracking
- Training performance tracking
- Equipment management
- Daily schedule management
- Weather-based training adjustment
- Battalion management
- Stipend/payment tracking
- Performance rankings
- SOS emergency alerts

## 🏗️ Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   Web App    │  │ Mobile App   │  │  Admin Desk  │  │  Trainer UI  │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           API GATEWAY (NGINX)                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        MICROSERVICE LAYER                                   │
│                                                                             │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐                 │
│  │   Auth Svc    │  │ Recruitment   │  │   Soldier     │                 │
│  │   (Port 8001) │  │    Svc        │  │    Svc        │                 │
│  │               │  │ (Port 8002)   │  │  (Port 8004)   │                 │
│  └────────────────┘  └────────────────┘  └────────────────┘                 │
│                                                                             │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐                 │
│  │   Medical     │  │   Training    │  │  Notification │                 │
│  │    Svc        │  │    Svc        │  │     Svc       │                 │
│  │  (Port 8005)  │  │  (Port 8006)  │  │  (Port 8009)   │                 │
│  └────────────────┘  └────────────────┘  └────────────────┘                 │
│                                                                             │
│  ┌────────────────┐  ┌────────────────┐                                    │
│  │   Weather     │  │    Report     │                                    │
│  │    Svc        │  │    Svc        │                                    │
│  │  (Port 8011)  │  │  (Port 8008)   │                                    │
│  └────────────────┘  └────────────────┘                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATA LAYER                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ PostgreSQL   │  │     Redis     │  │     S3/      │  │               │   │
│  │              │  │               │  │   MinIO      │  │               │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 🛠️ Technology Stack

| Component | Technology |
|-----------|------------|
| Backend Framework | Python FastAPI |
| Database | PostgreSQL 15 |
| ORM | SQLAlchemy 2.0 |
| Authentication | JWT + OAuth2 |
| File Storage | AWS S3 / MinIO |
| OCR Processing | pytesseract + OpenCV |
| Excel Processing | pandas + openpyxl |
| PDF Generation | ReportLab |
| Notifications | WebSockets |
| Weather API | OpenWeatherMap |
| Containerization | Docker + Kubernetes |

## 📁 Project Structure

```
agniveer-sentinel/
├── common/
│   ├── core/
│   │   ├── config.py       # Configuration settings
│   │   ├── database.py     # Database connection
│   │   └── security.py     # JWT & authentication
│   └── models/
│       └── base.py         # Base models & enums
│
├── services/
│   ├── auth_service/       # Authentication service
│   ├── recruitment_service/ # Phase 1: Recruitment
│   ├── soldier_service/    # Phase 2: Soldier Management
│   ├── training_service/   # Training Excel processing
│   ├── document-service/  # OCR document processing
│   ├── report-service/    # PDF report generation
│   ├── notification_service/ # WebSocket notifications
│   └── weather_service/   # Weather integration
│
├── architecture/
│   └── SYSTEM_ARCHITECTURE.md
│
├── docker-compose.yml
├── nginx.conf
├── requirements.txt
└── README.md
```

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- PostgreSQL 15
- Redis 7
- MinIO (or AWS S3)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/your-repo/agniveer-sentinel.git
cd agniveer-sentinel
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your settings
```

5. **Run with Docker Compose**
```bash
docker-compose up -d
```

6. **Access the services**
- Auth Service: http://localhost:8001
- Recruitment Service: http://localhost:8002
- Soldier Service: http://localhost:8004
- Training Service: http://localhost:8006
- API Gateway: http://localhost

## 📡 API Endpoints

### Authentication Service
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh token
- `GET /api/v1/auth/me` - Get current user

### Recruitment Service
- `POST /api/v1/recruitment/apply` - Submit application
- `GET /api/v1/recruitment/status` - Application status
- `POST /api/v1/recruitment/documents` - Upload documents
- `GET /api/v1/recruitment/admit-card` - Download admit card
- `POST /api/v1/recruitment/exams/register` - Register for exam

### Soldier Service
- `GET /api/v1/soldiers/profile` - Get soldier profile
- `PUT /api/v1/soldiers/profile` - Update profile
- `POST /api/v1/soldiers/documents` - Upload documents
- `GET /api/v1/soldiers/medical-records` - Get medical history
- `POST /api/v1/soldiers/training-records` - Add training record
- `GET /api/v1/soldiers/schedule` - Get daily schedule
- `POST /api/v1/soldiers/sos` - Trigger SOS alert
- `GET /api/v1/soldiers/battalions` - List battalions

### Training Service
- `POST /api/v1/training/upload` - Upload Excel sheet
- `GET /api/v1/training/records` - Get training data
- `GET /api/v1/training/report/daily` - Daily report

### Weather Service
- `GET /api/v1/weather/current` - Current weather
- `POST /api/v1/weather/adjust-schedule` - Adjust schedule

## 🔐 Security Features

- JWT-based authentication with refresh tokens
- Role-based access control (RBAC)
- Encrypted file storage (S3/MinIO vault)
- Comprehensive audit logging
- HTTPS only (TLS 1.3)
- Rate limiting and IP whitelisting

## 📊 Key Features

### Phase 1: Recruitment System
1. **Online Application** - Comprehensive application form
2. **Document Upload** - Aadhaar, education, certificates
3. **OCR Processing** - Auto-extract data from documents
4. **Admit Card Generation** - PDF with QR code
5. **Email/SMS Notifications** - Automated delivery

### Phase 2: Soldier Management LMS
1. **Profile Management** - Complete soldier profiles
2. **Medical Records** - Health history tracking
3. **Training Tracking** - Fitness, mental, weapons
4. **Excel Upload** - Bulk training data import
5. **PDF Reports** - Daily/monthly performance
6. **Weather Integration** - Auto-adjust schedules
7. **SOS Alerts** - Emergency notifications via WebSocket
8. **Performance Rankings** - Monthly battalion rankings
9. **Equipment Tracking** - Uniform and gear management

## 🔧 Development

### Running Services Locally

```bash
# Auth Service
cd services/auth_service
uvicorn main:app --reload --port 8001

# Recruitment Service
cd services/recruitment_service
uvicorn main:app --reload --port 8002

# Soldier Service
cd services/soldier_service
uvicorn main:app --reload --port 8004
```

### Running Tests

```bash
pytest tests/
```

## 📝 License

This project is proprietary and confidential. All rights reserved.

## 👥 Support

For technical support, please contact the development team.

---

*Document Version: 1.0*
*Last Updated: 2026-03-13*
