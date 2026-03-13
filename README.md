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
│   ├── auth-service/       # Authentication service
│   ├── recruitment-service/ # Phase 1: Recruitment
│   ├── soldier-service/    # Phase 2: Soldier Management
│   ├── training-service/   # Training Excel processing
│   ├── document-service/  # OCR document processing
│   ├── report-service/    # PDF report generation
