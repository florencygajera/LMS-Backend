# Agniveer Sentinel - Database Schema

## Complete Database Schema

This document describes all database tables and their relationships for the Agniveer Military Training & Recruitment Platform.

---

## Phase 1: Recruitment System

### users
| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY |
| uuid | UUID | UNIQUE, NOT NULL |
| email | VARCHAR(255) | UNIQUE, NOT NULL |
| username | VARCHAR(100) | UNIQUE, NOT NULL |
| hashed_password | VARCHAR(255) | NOT NULL |
| full_name | VARCHAR(255) | NOT NULL |
| role | ENUM | NOT NULL (super_admin, admin, trainer, doctor, soldier, candidate) |
| is_active | BOOLEAN | DEFAULT TRUE |
| is_verified | BOOLEAN | DEFAULT FALSE |
| phone_number | VARCHAR(20) | |
| profile_photo_url | VARCHAR(500) | |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

### candidates
| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY |
| uuid | UUID | UNIQUE, NOT NULL |
| user_id | INTEGER | FOREIGN KEY (users.id), UNIQUE |
| registration_id | VARCHAR(50) | UNIQUE, NOT NULL |
| date_of_birth | DATE | NOT NULL |
| gender | VARCHAR(20) | NOT NULL |
| blood_group | VARCHAR(10) | |
| aadhaar_number | VARCHAR(12) | UNIQUE |
| pan_number | VARCHAR(10) | |
| address | TEXT | |
| city | VARCHAR(100) | |
| state | VARCHAR(100) | |
| pincode | VARCHAR(10) | |
| father_name | VARCHAR(255) | |
| mother_name | VARCHAR(255) | |
| emergency_contact_name | VARCHAR(255) | |
| emergency_contact_phone | VARCHAR(20) | |
| education_qualification | VARCHAR(100) | |
| passing_year | INTEGER | |
| marks_percentage | FLOAT | |
| height_cm | INTEGER | |
| weight_kg | FLOAT | |
| chest_cm | INTEGER | |
| application_status | ENUM | DEFAULT 'draft' |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

### candidate_documents
| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY |
| uuid | UUID | UNIQUE, NOT NULL |
| candidate_id | INTEGER | FOREIGN KEY (candidates.id) |
| document_type | VARCHAR(50) | NOT NULL |
| file_url | VARCHAR(500) | NOT NULL |
| file_name | VARCHAR(255) | NOT NULL |
| file_size | INTEGER | |
| mime_type | VARCHAR(50) | |
| ocr_processed | BOOLEAN | DEFAULT FALSE |
| ocr_text | TEXT | |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

### applications
| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY |
| uuid | UUID | UNIQUE, NOT NULL |
| candidate_id | INTEGER | FOREIGN KEY (candidates.id), UNIQUE |
| recruitment_batch | VARCHAR(50) | NOT NULL |
| force_type | VARCHAR(50) | |
| trade_category | VARCHAR(100) | |
| age_eligible | BOOLEAN | DEFAULT FALSE |
| education_eligible | BOOLEAN | DEFAULT FALSE |
| physical_eligible | BOOLEAN | DEFAULT FALSE |
| documents_verified | BOOLEAN | DEFAULT FALSE |
| overall_eligible | BOOLEAN | DEFAULT FALSE |
| verification_notes | TEXT | |
| verified_by | INTEGER | FOREIGN KEY (users.id) |
| verified_at | TIMESTAMP | |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

### exam_centers
| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY |
| uuid | UUID | UNIQUE, NOT NULL |
| center_code | VARCHAR(20) | UNIQUE, NOT NULL |
| center_name | VARCHAR(255) | NOT NULL |
| address | TEXT | NOT NULL |
| city | VARCHAR(100) | NOT NULL |
| state | VARCHAR(100) | NOT NULL |
| pincode | VARCHAR(10) | NOT NULL |
| capacity | INTEGER | NOT NULL |
| current_booked | INTEGER | DEFAULT 0 |
| is_active | BOOLEAN | DEFAULT TRUE |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

### exams
| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY |
| uuid | UUID | UNIQUE, NOT NULL |
| exam_name | VARCHAR(255) | NOT NULL |
| exam_code | VARCHAR(20) | UNIQUE, NOT NULL |
| description | TEXT | |
| exam_date | DATE | NOT NULL |
| start_time | TIMESTAMP | NOT NULL |
| end_time | TIMESTAMP | NOT NULL |
| duration_minutes | INTEGER | NOT NULL |
| exam_center_id | INTEGER | FOREIGN KEY (exam_centers.id) |
| is_published | BOOLEAN | DEFAULT FALSE |
| total_questions | INTEGER | DEFAULT 100 |
| total_marks | INTEGER | DEFAULT 100 |
| passing_marks | INTEGER | DEFAULT 40 |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

### exam_questions
| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY |
| uuid | UUID | UNIQUE, NOT NULL |
| exam_id | INTEGER | FOREIGN KEY (exams.id) |
| question_text | TEXT | NOT NULL |
| question_type | VARCHAR(20) | DEFAULT 'multiple_choice' |
| options | TEXT | NOT NULL (JSON) |
| correct_answer | VARCHAR(500) | NOT NULL |
| marks | INTEGER | DEFAULT 1 |
| negative_marks | FLOAT | DEFAULT 0.25 |
| category | VARCHAR(100) | |
| difficulty | VARCHAR(20) | DEFAULT 'medium' |
| is_active | BOOLEAN | DEFAULT TRUE |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

### exam_registrations
| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY |
| uuid | UUID | UNIQUE, NOT NULL |
| candidate_id | INTEGER | FOREIGN KEY (candidates.id) |
| exam_id | INTEGER | FOREIGN KEY (exams.id) |
| registration_number | VARCHAR(50) | UNIQUE, NOT NULL |
| status | VARCHAR(20) | DEFAULT 'registered' |
| check_in_time | TIMESTAMP | |
| check_out_time | TIMESTAMP | |
| is_present | BOOLEAN | DEFAULT FALSE |
| marks_obtained | FLOAT | |
| total_marks | FLOAT | |
| percentile | FLOAT | |
| result_status | VARCHAR(20) | |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

### admit_cards
| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY |
| uuid | UUID | UNIQUE, NOT NULL |
| candidate_id | INTEGER | FOREIGN KEY (candidates.id), UNIQUE |
| exam_id | INTEGER | FOREIGN KEY (exams.id) |
| exam_registration_id | INTEGER | FOREIGN KEY (exam_registrations.id) |
| admit_card_number | VARCHAR(50) | UNIQUE, NOT NULL |
| exam_venue | VARCHAR(255) | NOT NULL |
| exam_date | DATE | NOT NULL |
| exam_start_time | VARCHAR(20) | NOT NULL |
| exam_end_time | VARCHAR(20) | NOT NULL |
| qr_code_url | VARCHAR(500) | |
| candidate_photo_url | VARCHAR(500) | |
| pdf_url | VARCHAR(500) | |
| generated_at | TIMESTAMP | DEFAULT NOW() |
| email_sent | BOOLEAN | DEFAULT FALSE |
| email_sent_at | TIMESTAMP | |
| sms_sent | BOOLEAN | DEFAULT FALSE |
| sms_sent_at | TIMESTAMP | |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

---

## Phase 2: Soldier Management LMS

### soldiers
| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY |
| uuid | UUID | UNIQUE, NOT NULL |
| user_id | INTEGER | FOREIGN KEY (users.id), UNIQUE |
| soldier_id | VARCHAR(50) | UNIQUE, NOT NULL |
| full_name | VARCHAR(255) | NOT NULL |
| date_of_birth | DATE | NOT NULL |
| gender | VARCHAR(20) | NOT NULL |
| blood_group | VARCHAR(10) | |
| phone_number | VARCHAR(20) | |
| email | VARCHAR(255) | |
| emergency_contact_name | VARCHAR(255) | |
| emergency_contact_phone | VARCHAR(20) | |
| emergency_contact_relation | VARCHAR(50) | |
| permanent_address | TEXT | |
| city | VARCHAR(100) | |
| state | VARCHAR(100) | |
| pincode | VARCHAR(10) | |
| joining_date | DATE | NOT NULL |
| rank | VARCHAR(50) | |
| battalion_id | INTEGER | FOREIGN KEY (battalions.id) |
| profile_photo_url | VARCHAR(500) | |
| is_active | BOOLEAN | DEFAULT TRUE |
| service_status | VARCHAR(20) | DEFAULT 'active' |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

### soldier_documents
| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY |
| uuid | UUID | UNIQUE, NOT NULL |
| soldier_id | INTEGER | FOREIGN KEY (soldiers.id) |
| document_type | VARCHAR(50) | NOT NULL |
| document_name | VARCHAR(255) | NOT NULL |
| file_url | VARCHAR(500) | NOT NULL |
| file_name | VARCHAR(255) | NOT NULL |
| expiry_date | DATE | |
| ocr_processed | BOOLEAN | DEFAULT FALSE |
| ocr_text | TEXT | |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

### battalions
| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY |
| uuid | UUID | UNIQUE, NOT NULL |
| battalion_name | VARCHAR(255) | NOT NULL |
| battalion_code | VARCHAR(20) | UNIQUE, NOT NULL |
| location | VARCHAR(255) | NOT NULL |
| city | VARCHAR(100) | NOT NULL |
| state | VARCHAR(100) | NOT NULL |
| commander_name | VARCHAR(255) | |
| commander_phone | VARCHAR(20) | |
| mission_details | TEXT | |
| total_strength | INTEGER | DEFAULT 0 |
| is_active | BOOLEAN | DEFAULT TRUE |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

### battalion_postings
| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY |
| uuid | UUID | UNIQUE, NOT NULL |
| soldier_id | INTEGER | FOREIGN KEY (soldiers.id) |
| battalion_id | INTEGER | FOREIGN KEY (battalions.id) |
| start_date | DATE | NOT NULL |
| end_date | DATE | |
| posting_type | VARCHAR(50) | DEFAULT 'permanent' |
| remarks | TEXT | |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

### medical_records
| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY |
| uuid | UUID | UNIQUE, NOT NULL |
| soldier_id | INTEGER | FOREIGN KEY (soldiers.id) |
| record_type | VARCHAR(50) | NOT NULL |
| doctor_name | VARCHAR(255) | NOT NULL |
| hospital_name | VARCHAR(255) | |
| diagnosis | TEXT | |
| symptoms | TEXT | |
| treatment | TEXT | |
| medicines | TEXT | |
| visit_date | DATE | NOT NULL |
| follow_up_date | DATE | |
| is_active | BOOLEAN | DEFAULT TRUE |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

### medical_attachments
| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY |
| uuid | UUID | UNIQUE, NOT NULL |
| medical_record_id | INTEGER | FOREIGN KEY (medical_records.id) |
| file_url | VARCHAR(500) | NOT NULL |
| file_name | VARCHAR(255) | NOT NULL |
| file_type | VARCHAR(50) | NOT NULL |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

### training_records
| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY |
| uuid | UUID | UNIQUE, NOT NULL |
| soldier_id | INTEGER | FOREIGN KEY (soldiers.id) |
| trainer_id | INTEGER | FOREIGN KEY (users.id) |
| training_date | DATE | NOT NULL |
| training_type | ENUM | NOT NULL (fitness, mental, weapons) |
| running_time_minutes | FLOAT | |
| pushups_count | INTEGER | |
| pullups_count | INTEGER | |
| endurance_score | FLOAT | |
| bmi | FLOAT | |
| strategy_exercises | FLOAT | |
| decision_score | FLOAT | |
| psychological_score | FLOAT | |
| shooting_accuracy | FLOAT | |
| weapon_handling_score | FLOAT | |
| combat_drill_score | FLOAT | |
| overall_score | FLOAT | |
| remarks | TEXT | |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

### daily_schedules
| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY |
| uuid | UUID | UNIQUE, NOT NULL |
| soldier_id | INTEGER | FOREIGN KEY (soldiers.id) |
| schedule_date | DATE | NOT NULL |
| day_of_week | VARCHAR(20) | NOT NULL |
| activities | TEXT | NOT NULL (JSON array) |
| is_adjusted | BOOLEAN | DEFAULT FALSE |
| adjustment_reason | VARCHAR(255) | |
| is_completed | BOOLEAN | DEFAULT FALSE |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

### equipment
| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY |
| uuid | UUID | UNIQUE, NOT NULL |
| soldier_id | INTEGER | FOREIGN KEY (soldiers.id) |
| equipment_type | VARCHAR(50) | NOT NULL |
| equipment_id | VARCHAR(50) | UNIQUE, NOT NULL |
| equipment_name | VARCHAR(255) | NOT NULL |
| serial_number | VARCHAR(100) | |
| issue_date | DATE | NOT NULL |
| return_date | DATE | |
| condition | VARCHAR(50) | DEFAULT 'good' |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

### soldier_events
| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY |
| uuid | UUID | UNIQUE, NOT NULL |
| soldier_id | INTEGER | FOREIGN KEY (soldiers.id) |
| event_type | VARCHAR(50) | NOT NULL |
| event_name | VARCHAR(255) | NOT NULL |
| event_date | DATE | NOT NULL |
| location | VARCHAR(255) | |
| description | TEXT | |
| position | VARCHAR(50) | |
| award_name | VARCHAR(255) | |
| certificate_url | VARCHAR(500) | |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

### stipends
| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY |
| uuid | UUID | UNIQUE, NOT NULL |
| soldier_id | INTEGER | FOREIGN KEY (soldiers.id) |
| month | INTEGER | NOT NULL (1-12) |
| year | INTEGER | NOT NULL |
| base_amount | FLOAT | NOT NULL |
| allowances | FLOAT | DEFAULT 0 |
| deductions | FLOAT | DEFAULT 0 |
| net_amount | FLOAT | NOT NULL |
| payment_status | ENUM | DEFAULT 'pending' |
| payment_date | TIMESTAMP | |
| transaction_id | VARCHAR(100) | |
| bank_reference | VARCHAR(100) | |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

### performance_rankings
| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY |
| uuid | UUID | UNIQUE, NOT NULL |
| soldier_id | INTEGER | FOREIGN KEY (soldiers.id) |
| battalion_id | INTEGER | FOREIGN KEY (battalions.id) |
| month | INTEGER | NOT NULL |
| year | INTEGER | NOT NULL |
| fitness_score | FLOAT | NOT NULL |
| weapon_score | FLOAT | NOT NULL |
| mental_score | FLOAT | NOT NULL |
| attendance_score | FLOAT | NOT NULL |
| discipline_score | FLOAT | NOT NULL |
| overall_score | FLOAT | NOT NULL |
| rank | INTEGER | NOT NULL |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

### sos_alerts
| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY |
| uuid | UUID | UNIQUE, NOT NULL |
| alert_message | TEXT | NOT NULL |
| alert_type | VARCHAR(50) | DEFAULT 'emergency' |
| is_active | BOOLEAN | DEFAULT TRUE |
| triggered_by | INTEGER | FOREIGN KEY (users.id) |
| triggered_at | TIMESTAMP | DEFAULT NOW() |
| resolved_at | TIMESTAMP | |
| battalion_id | INTEGER | FOREIGN KEY (battalions.id) |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

---

## Entity Relationships

```
users
├── candidates (1:1)
├── soldiers (1:1)
├── audit_logs (1:N)
├── refresh_tokens (1:N)
├── training_records (1:N)
└── sos_alerts (1:N)

candidates
├── candidate_documents (1:N)
├── application (1:1)
└── exam_registrations (1:N)

exams
├── exam_questions (1:N)
└── exam_registrations (1:N)

soldiers
├── soldier_documents (1:N)
├── medical_records (1:N)
├── training_records (1:N)
├── daily_schedules (1:N)
├── equipment (1:N)
├── soldier_events (1:N)
├── stipends (1:N)
├── battalion_postings (1:N)
└── performance_rankings (1:N)

battalions
├── soldiers (1:N)
├── battalion_postings (1:N)
└── performance_rankings (1:N)

medical_records
└── medical_attachments (1:N)
```
