# Agniveer Sentinel - Enterprise Production Architecture

## Complete Enterprise Architecture

This document describes the complete production-grade architecture for the Agniveer Military Training & Recruitment Platform.

---

## 1. PRODUCTION ARCHITECTURE DIAGRAM

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                    FRONTEND                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │   React      │  │   Mobile    │  │   Admin      │  │   Trainer    │        │
│  │   Web App    │  │   App       │  │   Portal     │  │   Portal     │        │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘        │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              CDN (CloudFront)                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           LOAD BALANCER (ALB)                                     │
│                         SSL Termination, WAF, DDoS Protection                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           API GATEWAY (NGINX)                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  Rate Limiting │ Authentication │ Request Routing │ Load Balancing          │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                         │
        ┌───────────────────────┬─────────┴─────────┬───────────────────────┐
        ▼                       ▼                   ▼                       ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│ Auth Service  │     │Recruitment    │     │ Soldier       │     │Training      │
│   (8001)      │     │Service        │     │Service        │     │Service        │
│               │     │  (8002)      │     │  (8004)       │     │  (8006)       │
└───────────────┘     └───────────────┘     └───────────────┘     └───────────────┘
        │                       │                   │                       │
        └───────────────────────┴─────────┬─────────┴───────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                          MESSAGE QUEUE (RABBITMQ)                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ auth_events  │  │recruitment  │  │ training     │  │ notification │          │
│  │              │  │_events       │  │_events       │  │_events       │          │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────────────────────────┘
                    │                    │                    │
        ┌───────────┴────┐    ┌─────────┴─────┐    ┌────────┴────────┐
        ▼                ▼    ▼               ▼    ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ Celery Workers│ │ OCR Workers   │ │ Report Workers│ │ Notification  │
│ (Main Queue)  │ │ (OCR Queue)   │ │(Reports Queue)│ │ Workers       │
└───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘
        │                │                 │                │
        └────────────────┴────────┬────────┴────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              DATA LAYER                                            │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐     │
│  │  PostgreSQL   │  │   Redis        │  │    S3/MinIO   │  │ Elasticsearch  │     │
│  │  Primary      │  │   Cache        │  │   Documents   │  │   Logs         │     │
│  │  (Read/Write) │  │   Sessions     │  │   Vault       │  │   Audit        │     │
│  └───────┬────────┘  └───────┬────────┘  └───────┬────────┘  └────────────────┘     │
│          │                    │                   │                                 │
│          ▼                    │                   ▼                                 │
│  ┌────────────────┐           │            ┌────────────────┐                         │
│  │  PostgreSQL   │           │            │  CloudFront   │                         │
│  │  Read Replica │           │            │  CDN          │                         │
│  └────────────────┘           │            └────────────────┘                         │
└───────────────────────────────┼─────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                          MONITORING STACK                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │ Prometheus   │  │  Grafana     │  │ AlertManager│  │   ELK        │            │
│  │ Metrics      │  │  Dashboards │  │ Alerts       │  │   Stack      │            │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘            │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. BACKGROUND TASK PROCESSING (CELERY)

### Task Queues
| Queue | Purpose | Workers |
|-------|---------|---------|
| main | General tasks | 2-4 |
| ocr | OCR processing | 4 |
| reports | PDF generation | 2 |
| notifications | Email/SMS | 2 |
| training | Excel processing | 2 |
| maintenance | Backups | 1 |

### Scheduled Tasks (Celery Beat)
- **Daily Reports** - 8:00 PM
- **Monthly Reports** - 1st of month, 2:00 AM
- **Leaderboard Update** - Daily 6:00 AM
- **Database Backup** - Daily 2:00 AM
- **Cleanup** - Weekly Sunday 3:00 AM
- **Storage Sync** - Hourly

---

## 3. EVENT-DRIVEN ARCHITECTURE (RABBITMQ)

### Event Types
```json
{
  "event_type": "soldier_created",
  "timestamp": "2026-03-13T10:00:00Z",
  "payload": {
    "soldier_id": 123,
    "user_id": 456,
    "battalion_id": 1
  }
}
```

### Events
| Event | Publisher | Consumer |
|-------|-----------|----------|
| soldier_created | Soldier Service | Notification, Training |
| training_uploaded | Training Service | Report, Leaderboard |
| medical_record_added | Soldier Service | Notification |
| report_generated | Report Service | Notification |
| sos_triggered | Notification Service | All Services |
| admit_card_generated | Recruitment Service | Notification |

---

## 4. MONITORING & METRICS

### Prometheus Metrics
- API response time (p50, p95, p99)
- Request count by endpoint
- Error rate
- CPU/Memory usage
- Database connection pool
- Celery queue length
- Background task duration

### Grafana Dashboards
1. **Service Health Dashboard** - All services status
2. **Training Activity** - Upload stats, processing time
3. **System Performance** - CPU, Memory, Network
4. **Database Performance** - Queries, connections
5. **Background Jobs** - Queue length, task success rate

### Alert Rules
- Service down > 1 minute
- Error rate > 5%
- Response time p95 > 2 seconds
- Disk usage > 80%
- Memory usage > 85%
- Queue backlog > 1000 tasks

---

## 5. SECURITY ARCHITECTURE

### API Security
- JWT + OAuth2 authentication
- Rate limiting (60 req/min)
- Login attempt tracking (5 attempts → lockout)
- Account lockout (30 min)
- CORS protection
- Secure HTTP headers
- API audit logging

### Data Security
- TLS 1.3 in transit
- AES-256 at rest
- Encrypted document vault
- Signed URL for file access (15 min expiry)
- Database encryption

### Network Security
- VPC isolation
- Security groups
- WAF rules
- DDoS protection

---

## 6. DATABASE BACKUP STRATEGY

### Backup Schedule
| Type | Frequency | Retention |
|------|-----------|-----------|
| Full backup | Daily 2:00 AM | 30 days |
| Incremental | Every 6 hours | 7 days |
| WAL archiving | Continuous | 7 days |

### Backup Storage
- Local: `/backups`
- Remote: S3 bucket (encrypted)
- Cross-region: DR site

### Recovery
- Point-in-time recovery (PITR)
- RTO: 1 hour
- RPO: 15 minutes

---

## 7. CI/CD PIPELINE

### GitHub Actions Workflow
1. **Test** - Unit tests, linting, coverage
2. **Build** - Docker image build, security scan
3. **Staging** - Auto-deploy to staging
4. **Production** - Manual approval required

### Environments
- Development → Automatic
- Staging → Automatic on develop branch
- Production → Manual approval

---

## 8. HEALTH CHECKS

### Endpoints
| Endpoint | Purpose | Check |
|----------|---------|-------|
| `/health` | Basic health | Service running |
| `/health/readiness` | Can serve traffic | DB + Redis + Storage |
| `/health/liveness` | Needs restart | Service crashed |
| `/health/deep` | Full diagnostics | All dependencies |

---

## 9. SCALING STRATEGY

### Horizontal Scaling
- Auto-scaling based on CPU (>70%)
- Min: 2 replicas per service
- Max: 10 replicas per service

### Database
- Read replica for queries
- Connection pooling (100 max)
- Query optimization

### Caching
- Redis for sessions
- Redis for frequently accessed data
- CDN for static assets

---

## 10. DISASTER RECOVERY

### RTO/RPO
- RTO: 1 hour
- RPO: 15 minutes

### Multi-AZ Deployment
- Primary region: eu-west-1
- DR region: eu-central-1
- Database replication: Active-passive

### Failover
- DNS failover (Route53)
- Database failover: < 5 minutes
- Application failover: < 1 hour

---

## 11. SERVICE ENDPOINTS

| Service | Port | Internal URL |
|---------|------|--------------|
| Auth | 8001 | auth-service:8001 |
| Recruitment | 8002 | recruitment-service:8002 |
| Soldier | 8004 | soldier-service:8004 |
| Training | 8006 | training-service:8006 |
| Report | 8008 | report-service:8008 |
| Notification | 8009 | notification-service:8009 |
| Weather | 8011 | weather-service:8011 |

---

## 12. DEPLOYMENT COMMANDS

```bash
# Start all services
docker-compose up -d

# Scale a service
docker-compose up -d --scale auth-service=3

# View logs
docker-compose logs -f auth-service

# Run migrations
docker-compose exec auth-service alembic upgrade head

# Execute Celery task
docker-compose exec celery celery -A infrastructure.celery_config worker -Q main

# Run Celery beat
docker-compose exec celery celery -A infrastructure.celery_config beat
```

---

*Document Version: 1.0*
*Last Updated: 2026-03-13*
