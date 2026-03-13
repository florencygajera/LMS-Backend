# Agniveer Military Training & Recruitment Platform - Architecture Documentation

## 1. SYSTEM OVERVIEW

### 1.1 Project Name
**AGNIVEER SENTINEL** - National Military Training & Recruitment Platform

### 1.2 Project Type
Enterprise-grade Government Web Application

### 1.3 Core Functionality
A comprehensive two-phase platform for:
- **Phase 1**: Recruitment and Examination System (Online application, CET, Admit Card generation)
- **Phase 2**: Agniveer Soldier Management LMS (Training, Medical, Performance tracking)

### 1.4 Technology Stack
| Component | Technology |
|-----------|------------|
| Backend Framework | Python FastAPI |
| Database | PostgreSQL 15+ |
| ORM | SQLAlchemy 2.0 |
| Authentication | JWT + OAuth2 |
| File Storage | AWS S3 / MinIO |
| OCR Processing | pytesseract + OpenCV |
| Excel Processing | pandas + openpyxl |
| PDF Generation | ReportLab |
| Notifications | WebSockets + Firebase |
| Weather API | OpenWeatherMap |
| Containerization | Docker + Kubernetes |

---

## 2. SYSTEM ARCHITECTURE

### 2.1 High-Level Architecture Diagram
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   Web App    │  │ Mobile App   │  │  Admin Desk  │  │  Trainer UI  │   │
│  │   (React)    │  │   (Flutter)  │  │   (React)    │  │   (React)    │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           API GATEWAY LAYER                                  │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                     NGINX Reverse Proxy                               │   │
│  │         (SSL/TLS Termination, Load Balancing, Caching)              │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        MICROSERVICE LAYER                                   │
│                                                                             │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐                 │
│  │   Auth Svc    │  │ Recruitment   │  │   Exam Svc    │                 │
│  │   (Port 8001) │  │    Svc        │  │   (Port 8003) │                 │
│  │               │  │ (Port 8002)   │  │               │                 │
│  └────────────────┘  └────────────────┘  └────────────────┘                 │
│                                                                             │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐                 │
│  │   Soldier     │  │   Medical      │  │   Training     │                 │
│  │   Svc         │  │    Svc         │  │    Svc         │                 │
│  │  (Port 8004)  │  │  (Port 8005)   │  │  (Port 8006)   │                 │
│  └────────────────┘  └────────────────┘  └────────────────┘                 │
│                                                                             │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐                 │
│  │   Document    │  │   Report       │  │   Notification │                 │
│  │    Svc        │  │    Svc         │  │     Svc        │                 │
│  │  (Port 8007)  │  │  (Port 8008)   │  │  (Port 8009)   │                 │
│  └────────────────┘  └────────────────┘  └────────────────┘                 │
│                                                                             │
│  ┌────────────────┐  ┌────────────────┐                                    │
│  │   Battalion   │  │   Weather      │                                    │
│  │    Svc        │  │    Svc         │                                    │
│  │  (Port 8010)  │  │  (Port 8011)   │                                    │
│  └────────────────┘  └────────────────┘                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATA LAYER                                          │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ PostgreSQL   │  │     Redis     │  │     S3/      │  │  Elasticsearch│   │
│  │   Primary    │  │    Cache      │  │   MinIO      │  │     Logs      │   │
│  │  (Port 5432) │  │  (Port 6379)  │  │              │  │               │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Modular Service Architecture

Each microservice is:
- Independently deployable
- Has its own database schema
- Communicates via REST APIs and message queues
- Handles specific business domain

---

## 3. DATABASE SCHEMA DESIGN

### 3.1 Database Architecture
- **Primary Database**: PostgreSQL with read replicas
- **Caching Layer**: Redis for session management and caching
- **Search**: Elasticsearch for full-text search on documents
- **File Storage**: S3/MinIO for secure document vault

### 3.2 Core Entities

#### Phase 1: Recruitment
1. **Candidates** - Applicant information
2. **Applications** - Application forms
3. **Documents** - Uploaded files
4. **ExamCenters** - Test centers
5. **Exams** - Scheduled exams
6. **Questions** - Question bank
7. **AdmitCards** - Generated admit cards
8. **Results** - Exam results

#### Phase 2: Soldier Management
1. **Soldiers** - Soldier profiles
2. **MedicalRecords** - Health history
3. **TrainingRecords** - Performance data
4. **Battalions** - Unit management
5. **Schedules** - Training schedules
6. **Equipment** - Uniform/equipment
7. **Events** - Achievements/events
8. **Stipends** - Payment records
9. **Rankings** - Performance rankings

---

## 4. AUTHENTICATION FLOW

### 4.1 JWT + OAuth2 Implementation
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│  Auth Svc   │────▶│  PostgreSQL │
│             │◀────│  (FastAPI)  │◀────│              │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │
       │                   ▼
       │            ┌─────────────┐
       │            │    Redis    │
       │            │  (Tokens)   │
       │            └─────────────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│              Access Token Flow               │
│  1. User Login with Credentials              │
│  2. Auth Service Validates                   │
│  3. Generate JWT (Access + Refresh)          │
│  4. Store Refresh Token in Redis             │
│  5. Return Access Token to Client            │
│  6. Client includes in Authorization Header │
└─────────────────────────────────────────────┘
```

### 4.2 Role-Based Access Control (RBAC)
| Role | Permissions |
|------|-------------|
| Super Admin | Full system access |
| Admin | Battalion management, reports |
| Trainer | Training data upload |
| Doctor | Medical records |
| Soldier | Own profile, training |
| Candidate | Application only |

---

## 5. API ENDPOINTS STRUCTURE

### 5.1 Authentication Service (Port 8001)
- `POST /auth/register` - Register new user
- `POST /auth/login` - User login
- `POST /auth/refresh` - Refresh token
- `POST /auth/logout` - Logout
- `GET /auth/me` - Current user info
- `PUT /auth/password` - Change password

### 5.2 Recruitment Service (Port 8002)
- `POST /recruitment/apply` - Submit application
- `GET /recruitment/status` - Application status
- `POST /recruitment/documents` - Upload documents
- `GET /recruitment/admit-card` - Download admit card
- `POST /recruitment/verify` - Verify eligibility

### 5.3 Exam Service (Port 8003)
- `POST /exams/schedule` - Schedule exam
- `GET /exams/centers` - List exam centers
- `POST /exams/register` - Exam registration
- `GET /exams/question-bank` - Get questions
- `POST /exams/submit` - Submit exam
- `GET /exams/results` - View results

### 5.4 Soldier Service (Port 8004)
- `GET /soldiers/profile` - Get profile
- `PUT /soldiers/profile` - Update profile
- `POST /soldiers/documents` - Upload documents
- `GET /soldiers/ranking` - Performance ranking
- `GET /soldiers/schedule` - Daily schedule

### 5.5 Medical Service (Port 8005)
- `GET /medical/records` - Get medical history
- `POST /medical/records` - Add medical record
- `GET /medical/record/{id}` - Get specific record
- `PUT /medical/record/{id}` - Update record

### 5.6 Training Service (Port 8006)
- `POST /training/upload` - Upload Excel sheet
- `GET /training/records` - Get training data
- `GET /training/report/daily` - Daily report
- `GET /training/report/monthly` - Monthly report
- `POST /training/schedule` - Create schedule

### 5.7 Document Service (Port 8007)
- `POST /documents/upload` - Upload document
- `GET /documents/{id}` - Download document
- `POST /documents/ocr` - Process OCR
- `DELETE /documents/{id}` - Delete document

### 5.8 Report Service (Port 8008)
- `GET /reports/soldier/{id}` - Soldier report
- `GET /reports/battalion/{id}` - Battalion report
- `GET /reports/performance` - Performance report
- `POST /reports/generate` - Generate PDF

### 5.9 Notification Service (Port 8009)
- `POST /notifications/send` - Send notification
- `GET /notifications` - Get notifications
- `POST /notifications/sos` - Trigger SOS
- `WS /ws/notifications` - WebSocket endpoint

### 5.10 Battalion Service (Port 8010)
- `GET /battalions` - List battalions
- `POST /battalions` - Create battalion
- `GET /battalions/{id}` - Get battalion
- `PUT /battalions/{id}` - Update battalion
- `POST /battalions/{id}/assign` - Assign soldier

### 5.11 Weather Service (Port 8011)
- `GET /weather/current` - Current weather
- `GET /weather/forecast` - Weather forecast
- `POST /weather/adjust-schedule` - Auto-adjust

---

## 6. OCR PIPELINE

### 6.1 Document Processing Flow
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Upload    │────▶│   Preproc   │────▶│   OCR       │
│   Document  │     │   (OpenCV)  │     │  (Tesseract)│
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                                              ▼
                   ┌─────────────┐     ┌─────────────┐
                   │   Extract   │◀────│   Parse     │
                   │   Data      │     │   Text      │
                   └─────────────┘     └─────────────┘
                          │
                          ▼
                   ┌─────────────┐
                   │   Update    │
                   │   Profile   │
                   └─────────────┘
```

### 6.2 OCR Processing Steps
1. Image preprocessing (denoising, contrast adjustment)
2. Text extraction using pytesseract
3. Data parsing and validation
4. Auto-populate profile fields
5. Store extracted text for audit

---

## 7. EXCEL PROCESSING WORKFLOW

### 7.1 Training Data Upload Flow
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Upload    │────▶│   Parse     │────▶│   Validate  │
│   Excel     │     │   (pandas)  │     │   Data      │
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                                              ▼
                   ┌─────────────┐     ┌─────────────┐
                   │   Store     │◀────│   Transform │
                   │   Records   │     │   Data      │
                   └─────────────┘     └─────────────┘
                          │
                          ▼
                   ┌─────────────┐
                   │   Generate  │
                   │   Report    │
                   └─────────────┘
```

### 7.2 Excel Validation Rules
- Soldier_ID must exist in database
- Date must be valid format
- Numeric fields within acceptable ranges
- No duplicate entries for same soldier/date

---

## 8. PDF REPORT GENERATION

### 8.1 Report Types
1. **Admit Card** - Candidate exam entry
2. **Daily Performance Report** - Individual soldier
3. **Monthly Progress Report** - Battalion summary
4. **Medical Report** - Health records
5. **Stipend Report** - Payment details

### 8.2 PDF Generation Flow
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Request   │────▶│   Fetch     │────▶│   Generate  │
│   Report    │     │   Data      │     │   PDF       │
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                                              ▼
                   ┌─────────────┐
                   │   Deliver   │
                   │   (Email/    │
                   │   Download) │
                   └─────────────┘
```

---

## 9. WEATHER INTEGRATION

### 9.1 Weather-Based Schedule Adjustment
```python
# Adjustment Rules
IF temperature > 40°C:
    - Cancel outdoor training
    - Move to indoor activities
    
IF temperature < 5°C:
    - Reduce exposure time
    - Add warm-up periods
    
IF rain_intensity > 50mm:
    - Cancel field exercises
    - Shift to classroom training
    
IF wind_speed > 50 km/h:
    - Cancel parachute/aviation training
```

---

## 10. SECURITY REQUIREMENTS

### 10.1 Security Measures
| Layer | Implementation |
|-------|----------------|
| Transport | HTTPS/TLS 1.3 |
| Authentication | JWT with short expiry |
| Authorization | RBAC + Permissions |
| Data | AES-256 encryption at rest |
| Files | Secure S3 vault with presigned URLs |
| Audit | Comprehensive logging |
| API | Rate limiting, IP whitelist |

### 10.2 Audit Log Fields
- User ID
- Action performed
- Timestamp
- IP address
- Request details
- Response status

---

## 11. DEPLOYMENT ARCHITECTURE

### 11.1 Production Environment
```
┌─────────────────────────────────────────────────────────────────┐
│                        AWS / Cloud Infrastructure                │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   Kubernetes Cluster                      │   │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐  │   │
│  │  │ Auth   │ │Recruit │ │Soldier │ │Medical │ │Training│  │   │
│  │  │ Pod    │ │ Pod    │ │ Pod    │ │ Pod    │ │ Pod    │  │   │
│  │  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│  ┌────────────┐  ┌───────────┴───────────┐  ┌────────────┐   │
│  │   RDS      │  │    EFS/S3 Storage    │  │   ElastiCache│  │
│  │ PostgreSQL │  │    (Documents)        │  │   Redis     │   │
│  └────────────┘  └───────────────────────┘  └────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 11.2 Docker Compose (Development)
```yaml
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: dev_password
    ports:
      - "5432:5432"
  
  redis:
    image: redis:7
    ports:
      - "6379:6379"
  
  minio:
    image: minio/minio
    command: server /data
    ports:
      - "9000:9000"
  
  auth-service:
    build: ./services/auth
    ports:
      - "8001:8001"
```

---

## 12. PROJECT FOLDER STRUCTURE

```
agniveer-sentinel/
├── services/
│   ├── auth-service/
│   │   ├── app/
│   │   │   ├── api/
│   │   │   │   └── endpoints/
│   │   │   ├── core/
│   │   │   ├── models/
│   │   │   ├── schemas/
│   │   │   └── main.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   ├── recruitment-service/
│   ├── exam-service/
│   ├── soldier-service/
│   ├── medical-service/
│   ├── training-service/
│   ├── document-service/
│   ├── report-service/
│   ├── notification-service/
│   ├── battalion-service/
│   └── weather-service/
│
├── common/
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── database.py
│   ├── models/
│   │   └── base.py
│   └── utils/
│
├── docker-compose.yml
├── nginx.conf
└── README.md
```

---

## 13. IMPLEMENTATION PRIORITY

### Phase 1 (Weeks 1-4)
1. Auth Service + Database Setup
2. Recruitment Service
3. Document Upload + OCR
4. Admit Card Generation

### Phase 2 (Weeks 5-12)
5. Soldier Management
6. Medical Records
7. Training System + Excel Upload
8. Reports + PDF Generation

### Phase 3 (Weeks 13-16)
9. Weather Integration
10. SOS System + WebSockets
11. Performance Rankings
12. Security Hardening

---

## 14. COMPLIANCE REQUIREMENTS

- [ ] Data Protection (Encryption at Rest)
- [ ] Audit Trail (All Actions Logged)
- [ ] Backup & Recovery (Daily Backups)
- [ ] Disaster Recovery (Multi-AZ)
- [ ] 99.9% Uptime SLA
- [ ] GDPR-like Data Handling
- [ ] Government Security Standards

---

*Document Version: 1.0*
*Last Updated: 2026-03-13*
