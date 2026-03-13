# Agniveer Sentinel - API Endpoints

## Complete API Documentation

This document lists all API endpoints for the Agniveer Military Training & Recruitment Platform.

---

## Base URL
```
Production: https://api.agniveer.mil.in
Development: http://localhost
```

## Authentication

### Auth Service (Port 8001)

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| POST | `/api/v1/auth/register` | Register new user | Public |
| POST | `/api/v1/auth/login` | User login | Public |
| POST | `/api/v1/auth/refresh` | Refresh access token | Public |
| POST | `/api/v1/auth/logout` | Logout user | Auth |
| GET | `/api/v1/auth/me` | Get current user | Auth |
| PUT | `/api/v1/auth/me` | Update current user | Auth |
| POST | `/api/v1/auth/password/change` | Change password | Auth |

---

## Phase 1: Recruitment System

### Recruitment Service (Port 8002)

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| POST | `/api/v1/recruitment/apply` | Submit recruitment application | Candidate |
| GET | `/api/v1/recruitment/status` | Get application status | Candidate |
| PUT | `/api/v1/recruitment/profile` | Update application | Candidate |
| POST | `/api/v1/recruitment/documents` | Upload documents | Candidate |
| GET | `/api/v1/recruitment/exam-centers` | List exam centers | Public |
| GET | `/api/v1/recruitment/exams` | List available exams | Public |
| GET | `/api/v1/recruitment/exams/{id}` | Get exam details | Public |
| POST | `/api/v1/recruitment/exams/register` | Register for exam | Candidate |
| GET | `/api/v1/recruitment/admit-card` | Get admit card | Candidate |
| POST | `/api/v1/recruitment/verify/{id}` | Verify application | Admin |

---

## Phase 2: Soldier Management LMS

### Soldier Service (Port 8004)

#### Profile Management
| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| POST | `/api/v1/soldiers/profile` | Create soldier profile | Admin |
| GET | `/api/v1/soldiers/profile` | Get own profile | Soldier |
| GET | `/api/v1/soldiers/profile/{id}` | Get soldier profile | Admin/Trainer |
| PUT | `/api/v1/soldiers/profile` | Update own profile | Soldier |
| POST | `/api/v1/soldiers/documents` | Upload document | Soldier |

#### Medical Records
| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| POST | `/api/v1/soldiers/medical-records` | Add medical record | Doctor |
| GET | `/api/v1/soldiers/medical-records` | List medical records | Soldier/Doctor |
| GET | `/api/v1/soldiers/medical-records/{id}` | Get record details | Soldier/Doctor |
| PUT | `/api/v1/soldiers/medical-records/{id}` | Update record | Doctor |

#### Training Records
| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/v1/soldiers/training-records` | List training records | Soldier/Trainer |
| GET | `/api/v1/soldiers/training-records/{id}` | Get record details | Soldier/Trainer |

#### Schedule
| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/v1/soldiers/schedule` | Get daily schedule | Soldier |
| GET | `/api/v1/soldiers/schedule/{date}` | Get schedule for date | Soldier |

#### Equipment
| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/v1/soldiers/equipment` | List equipment | Soldier |
| POST | `/api/v1/soldiers/equipment` | Issue equipment | Admin |
| PUT | `/api/v1/soldiers/equipment/{id}` | Update equipment | Admin |

#### Events
| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/v1/soldiers/events` | List events/achievements | Soldier |
| POST | `/api/v1/soldiers/events` | Add event | Admin |

#### Stipend
| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/v1/soldiers/stipends` | List stipend records | Soldier |
| POST | `/api/v1/soldiers/stipends` | Add stipend record | Admin |

#### Battalion
| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/v1/soldiers/battalions` | List battalions | Public |
| POST | `/api/v1/soldiers/battalions` | Create battalion | Admin |
| GET | `/api/v1/soldiers/battalions/{id}` | Get battalion details | Public |
| PUT | `/api/v1/soldiers/battalions/{id}` | Update battalion | Admin |

#### Ranking
| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/v1/soldiers/rankings` | Get performance rankings | Public |
| GET | `/api/v1/soldiers/rankings/battalion/{id}` | Battalion rankings | Public |

#### SOS
| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| POST | `/api/v1/soldiers/sos` | Trigger SOS alert | Admin |
| GET | `/api/v1/soldiers/sos/active` | Get active SOS alerts | All |
| POST | `/api/v1/soldiers/sos/{id}/resolve` | Resolve SOS alert | Admin |

---

### Training Service (Port 8006)

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| POST | `/api/v1/training/upload` | Upload Excel sheet | Trainer |
| POST | `/api/v1/training/records` | Create training record | Trainer |
| GET | `/api/v1/training/records` | Get training records | All |
| GET | `/api/v1/training/stats/{soldier_id}` | Get soldier stats | Soldier/Trainer |
| GET | `/api/v1/training/battalion/{id}/stats` | Get battalion stats | Admin |

---

### Report Service (Port 8008)

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/v1/reports/soldier/{id}/daily` | Daily performance PDF | Soldier |
| GET | `/api/v1/reports/soldier/{id}/monthly` | Monthly progress PDF | Soldier |
| GET | `/api/v1/reports/soldier/{id}/medical` | Medical report PDF | Soldier/Doctor |
| GET | `/api/v1/reports/soldier/{id}/stipend` | Stipend report PDF | Soldier |

---

### Weather Service (Port 8011)

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/v1/weather/current` | Current weather | Public |
| GET | `/api/v1/weather/forecast` | Weather forecast | Public |
| POST | `/api/v1/weather/recommendation` | Training recommendation | Public |
| POST | `/api/v1/weather/adjust-schedule` | Adjust schedule | Trainer |
| POST | `/api/v1/weather/schedule/auto-adjust` | Auto-adjust schedule | System |

---

### Notification Service (Port 8009)

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| WS | `/ws/notifications` | WebSocket endpoint | Auth |
| POST | `/api/v1/notifications/send` | Send notification | Admin |
| POST | `/api/v1/notifications/broadcast` | Broadcast notification | Admin |
| POST | `/api/v1/notifications/sos/trigger` | Trigger SOS | Admin |
| GET | `/api/v1/notifications/sos/active` | Get active SOS | All |
| POST | `/api/v1/notifications/sos/{id}/resolve` | Resolve SOS | Admin |
| GET | `/api/v1/notifications/sos/history` | SOS history | Admin |

---

## Common Response Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 422 | Validation Error |
| 500 | Internal Server Error |

## Authentication

All protected endpoints require Bearer token in the Authorization header:
```
Authorization: Bearer <access_token>
```

## Role-Based Access

| Role | Permissions |
|------|-------------|
| super_admin | Full system access |
| admin | Battalion management, reports |
| trainer | Training data upload |
| doctor | Medical records |
| soldier | Own profile, training |
| candidate | Application only |
