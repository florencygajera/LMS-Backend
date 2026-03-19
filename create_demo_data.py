"""
Demo Data Generator for Agniveer LMS
Creates users, candidates, soldiers, and related data
"""
import os
os.environ['USE_SQLITE'] = 'true'

import asyncio
from datetime import datetime, date, timedelta
import random
from common.core.database import import_models, get_async_session_local, get_db_engine, Base
from common.models.base import UserRole, ApplicationStatus, TrainingType, PaymentStatus


async def create_demo_data():
    """Create comprehensive demo data"""
    
    import_models()
    session_factory = get_async_session_local()
    
    async with session_factory() as session:
        # Import all models
        from services.auth_service.models.user import User
        from services.recruitment_service.models.recruitment import (
            Candidate, CandidateDocument, Application, ExamCenter, Exam, 
            ExamQuestion, ExamRegistration, AdmitCard
        )
        from services.soldier_service.models.soldier import (
            Soldier, SoldierDocument, Battalion, BattalionPosting, 
            MedicalRecord, MedicalAttachment, TrainingRecord, DailySchedule,
            Equipment, SoldierEvent, Stipend, PerformanceRanking, SOSAlert
        )
        
        print("Creating demo data...")
        
        # ========== ADMINS ==========
        admins = [
            User(
                email="admin@agniveer.gov.in",
                username="admin",
                hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqKx8pKvGm",  # password: admin123
                full_name="Major General Rajesh Kumar",
                role=UserRole.ADMIN,
                is_active=True,
                is_verified=True,
                phone_number="+919999999991"
            ),
            User(
                email="superadmin@agniveer.gov.in",
                username="superadmin",
                hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqKx8pKvGm",
                full_name="Lt. General Vikram Singh",
                role=UserRole.SUPER_ADMIN,
                is_active=True,
                is_verified=True,
                phone_number="+919999999992"
            ),
        ]
        session.add_all(admins)
        await session.flush()
        print(f"Created {len(admins)} admin users")
        
        # ========== TRAINERS ==========
        trainers = [
            User(
                email="trainer1@agniveer.gov.in",
                username="trainer_nature",
                hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqKx8pKvGm",
                full_name="Captain Amit Sharma",
                role=UserRole.TRAINER,
                is_active=True,
                is_verified=True,
                phone_number="+919999999101"
            ),
            User(
                email="trainer2@agniveer.gov.in",
                username="trainer_combat",
                hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqKx8pKvGm",
                full_name="Major Suresh Patil",
                role=UserRole.TRAINER,
                is_active=True,
                is_verified=True,
                phone_number="+919999999102"
            ),
            User(
                email="trainer3@agniveer.gov.in",
                username="trainer_mental",
                hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqKx8pKvGm",
                full_name="Wing Commander Ramesh Iyer",
                role=UserRole.TRAINER,
                is_active=True,
                is_verified=True,
                phone_number="+919999999103"
            ),
        ]
        session.add_all(trainers)
        await session.flush()
        print(f"Created {len(trainers)} trainer users")
        
        # ========== DOCTORS ==========
        doctors = [
            User(
                email="doctor1@agniveer.gov.in",
                username="doctor_medical",
                hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqKx8pKvGm",
                full_name="Colonel Dr. Anil Gupta",
                role=UserRole.DOCTOR,
                is_active=True,
                is_verified=True,
                phone_number="+919999999201"
            ),
            User(
                email="doctor2@agniveer.gov.in",
                username="doctor_dental",
                hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqKx8pKvGm",
                full_name="Lt. Colonel Dr. Priya Mishra",
                role=UserRole.DOCTOR,
                is_active=True,
                is_verified=True,
                phone_number="+919999999202"
            ),
        ]
        session.add_all(doctors)
        await session.flush()
        print(f"Created {len(doctors)} doctor users")
        
        # ========== CANDIDATES ==========
        candidate_names = [
            "Rahul Verma", "Priya Singh", "Amit Kumar", "Sneha Reddy", "Vijay Malhotra",
            "Anjali Pandey", "Sanjay Yadav", "Pooja Sharma", "Ravi Shankar", "Kavita Devi",
            "Deepak Chopra", "Meera Nair", "Arjun Menon", "Divya Joshi", "Karan Singh"
        ]
        
        candidates = []
        candidate_users = []
        
        for i, name in enumerate(candidate_names):
            user = User(
                email=f"candidate{i+1}@email.com",
                username=f"candidate{i+1}",
                hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqKx8pKvGm",  # password: admin123
                full_name=name,
                role=UserRole.CANDIDATE,
                is_active=True,
                is_verified=random.choice([True, False]),
                phone_number=f"+9199{random.randint(10000000, 99999999)}"
            )
            candidate_users.append(user)
        
        session.add_all(candidate_users)
        await session.flush()
        
        # Create candidate profiles
        states = ["Uttar Pradesh", "Maharashtra", "Rajasthan", "Madhya Pradesh", "Kerala", "Punjab", "Haryana"]
        blood_groups = ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]
        
        for i, user in enumerate(candidate_users):
            candidate = Candidate(
                user_id=user.id,
                date_of_birth=date(1998 + random.randint(0, 5), random.randint(1, 12), random.randint(1, 28)),
                gender=random.choice(["Male", "Female"]),
                blood_group=random.choice(blood_groups),
                aadhaar_number=f"{random.randint(1000, 9999)}{random.randint(1000, 9999)}{random.randint(1000, 9999)}",
                address=f"{random.randint(1, 999)}, {random.choice(['Main Road', 'Lane 5', 'Sector 15'])}",
                city=random.choice(["Lucknow", "Delhi", "Jaipur", "Mumbai", "Bhopal"]),
                state=random.choice(states),
                pincode=f"{random.randint(100000, 999999)}",
                father_name=f"{name.split()[0]} Father",
                mother_name=f"{name.split()[0]} Mother",
                education_qualification=random.choice(["12th Pass", "Graduate", "Post Graduate"]),
                passing_year=random.randint(2015, 2024),
                marks_percentage=random.uniform(60, 95),
                height_cm=random.randint(165, 185),
                weight_kg=random.uniform(60, 85),
                chest_cm=random.randint(76, 102),
                application_status=random.choice([ApplicationStatus.DRAFT, ApplicationStatus.SUBMITTED, ApplicationStatus.VERIFIED]),
                registration_id=f"AGN{2024}{1000+i}"
            )
            candidates.append(candidate)
        
        session.add_all(candidates)
        await session.flush()
        print(f"Created {len(candidates)} candidate users with profiles")
        
        # Create applications for candidates
        applications = []
        for candidate in candidates:
            if candidate.application_status in [ApplicationStatus.SUBMITTED, ApplicationStatus.VERIFIED]:
                app = Application(
                    candidate_id=candidate.id,
                    recruitment_batch="AGN-2024",
                    force_type=random.choice(["Army", "Navy", "Air Force"]),
                    trade_category=random.choice(["General Duty", "Technical", "Clerk"]),
                    age_eligible=True,
                    education_eligible=True,
                    physical_eligible=True,
                    documents_verified=candidate.application_status == ApplicationStatus.VERIFIED,
                    overall_eligible=True
                )
                applications.append(app)
        
        session.add_all(applications)
        await session.flush()
        print(f"Created {len(applications)} applications")
        
        # ========== SOLDIERS ==========
        soldier_names = [
            "Lance Naik Ram Singh", "Sepoy Vijay Kumar", "Havildar Major Sunil Yadav",
            "Naib Subedar Rakesh Sharma", "Subedar Major Pratap Singh",
            "Captain Manoj Kumar", "Major Deepak Rao", "Lieutenant Colonel Ajay Singh",
            "Wing Commander Suresh Kumar", "Squadron Leader Vikram Singh"
        ]
        
        soldier_users = []
        soldiers = []
        
        for i, name in enumerate(soldier_names):
            user = User(
                email=f"soldier{i+1}@agniveer.gov.in",
                username=f"soldier{i+1}",
                hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqKx8pKvGm",
                full_name=name,
                role=UserRole.SOLDIER,
                is_active=True,
                is_verified=True,
                phone_number=f"+9199{random.randint(10000000, 99999999)}"
            )
            soldier_users.append(user)
        
        session.add_all(soldier_users)
        await session.flush()
        
        # Create battalions first
        battalions = [
            Battalion(
                battalion_name="1st Battalion, 9th Para (SF)",
                battalion_code="1/9 PARA(SF)",
                location="Jammu",
                city="Jammu",
                state="Jammu & Kashmir",
                commander_name="Colonel Rajesh Kumar",
                commander_phone="+919999990001",
                mission_details="Special Forces Operations",
                total_strength=150
            ),
            Battalion(
                battalion_name="2nd Battalion, 3rd Gorkha Rifles",
                battalion_code="2/3 GR",
                location="Leh",
                city="Leh",
                state="Ladakh",
                commander_name="Colonel Amit Singh",
                commander_phone="+919999990002",
                mission_details="High Altitude Warfare",
                total_strength=200
            ),
            Battalion(
                battalion_name="1st Battalion, 5th Gorkha Rifles",
                battalion_code="1/5 GR",
                location="Kashmir",
                city="Srinagar",
                state="Jammu & Kashmir",
                commander_name="Colonel Vikram Malhotra",
                commander_phone="+919999990003",
                mission_details="Counter Insurgency",
                total_strength=180
            ),
        ]
        session.add_all(battalions)
        await session.flush()
        print(f"Created {len(battalions)} battalions")
        
        # Create soldier profiles
        ranks = ["Sepoy", "Lance Naik", "Havildar", "Naib Subedar", "Subedar", "Major", "Captain"]
        
        for i, user in enumerate(soldier_users):
            soldier = Soldier(
                user_id=user.id,
                soldier_id=f"JS{10000+i}",
                full_name=soldier_names[i],
                date_of_birth=date(1990 + random.randint(0, 8), random.randint(1, 12), random.randint(1, 28)),
                gender="Male",
                blood_group=random.choice(blood_groups),
                phone_number=user.phone_number,
                email=user.email,
                emergency_contact_name=f"{soldier_names[i].split()[-1]} Family",
                emergency_contact_phone=f"+9199{random.randint(10000000, 99999999)}",
                permanent_address=f"Unit Location, {random.choice(['Jammu', 'Leh', 'Srinagar', 'Punjab'])}",
                city=random.choice(["Jammu", "Leh", "Srinagar"]),
                state=random.choice(["Jammu & Kashmir", "Ladakh", "Punjab"]),
                pincode=f"{random.randint(100000, 999999)}",
                joining_date=date(2015 + random.randint(0, 8), random.randint(1, 12), 1),
                rank=random.choice(ranks),
                battalion_id=random.choice(battalions).id if i < len(battalions) else battalions[0].id,
                is_active=True,
                service_status="active"
            )
            soldiers.append(soldier)
        
        session.add_all(soldiers)
        await session.flush()
        print(f"Created {len(soldiers)} soldiers with profiles")
        
        # Create training records for soldiers
        training_records = []
        for soldier in soldiers:
            for _ in range(random.randint(3, 10)):
                training = TrainingRecord(
                    soldier_id=soldier.id,
                    trainer_id=random.choice(trainers).id,
                    training_date=date(2024, random.randint(1, 12), random.randint(1, 28)),
                    training_type=random.choice([TrainingType.FITNESS, TrainingType.MENTAL, TrainingType.WEAPONS]),
                    running_time_minutes=random.uniform(15, 35),
                    pushups_count=random.randint(15, 50),
                    pullups_count=random.randint(5, 25),
                    endurance_score=random.uniform(70, 100),
                    bmi=random.uniform(20, 28),
                    strategy_exercises=random.uniform(70, 100),
                    decision_score=random.uniform(70, 100),
                    shooting_accuracy=random.uniform(70, 100),
                    weapon_handling_score=random.uniform(70, 100),
                    combat_drill_score=random.uniform(70, 100),
                    overall_score=random.uniform(70, 100),
                    remarks="Good progress"
                )
                training_records.append(training)
        
        session.add_all(training_records)
        await session.flush()
        print(f"Created {len(training_records)} training records")
        
        # Create medical records for soldiers
        medical_records = []
        for soldier in soldiers[:5]:  # Only some soldiers
            for _ in range(random.randint(1, 3)):
                record = MedicalRecord(
                    soldier_id=soldier.id,
                    record_type=random.choice(["checkup", "treatment"]),
                    doctor_name=random.choice(["Dr. Anil Gupta", "Dr. Priya Mishra"]),
                    hospital_name=random.choice(["Military Hospital", "Base Hospital"]),
                    diagnosis=random.choice(["Normal", "Viral Fever", "Minor Injury", "Fitness Assessment"]),
                    visit_date=date(2024, random.randint(1, 12), random.randint(1, 28)),
                    is_active=True
                )
                medical_records.append(record)
        
        session.add_all(medical_records)
        await session.flush()
        print(f"Created {len(medical_records)} medical records")
        
        # Create daily schedules
        schedules = []
        for soldier in soldiers[:5]:
            for days in range(7):
                schedule = DailySchedule(
                    soldier_id=soldier.id,
                    schedule_date=date(2024, 3, 1) + timedelta(days=days),
                    day_of_week=("Monday Tuesday Wednesday Thursday Friday Saturday Sunday".split())[days % 7],
                    activities='[{"time": "05:00", "activity": "PT", "location": "Ground"}, {"time": "07:00", "activity": "Breakfast", "location": "Mess"}, {"time": "09:00", "activity": "Training", "location": "Field"}, {"time": "13:00", "activity": "Lunch", "location": "Mess"}, {"time": "14:00", "activity": "Weapon Training", "location": "Range"}, {"time": "17:00", "activity": "Sports", "location": "Ground"}, {"time": "20:00", "activity": "Dinner", "location": "Mess"}]',
                    is_completed=days < 3,
                    is_adjusted=False
                )
                schedules.append(schedule)
        
        session.add_all(schedules)
        await session.flush()
        print(f"Created {len(schedules)} daily schedules")
        
        # Create equipment
        equipment = []
        for soldier in soldiers[:5]:
            for eq_type in ["uniform", "weapon", "gear"]:
                eq = Equipment(
                    soldier_id=soldier.id,
                    equipment_type=eq_type,
                    equipment_id=f"EQ{random.randint(10000, 99999)}",
                    equipment_name=random.choice(["Combat Uniform", "AK-47", "Boots", "Helmet", "Backpack"]),
                    serial_number=f"SN{random.randint(100000, 999999)}",
                    issue_date=date(2024, random.randint(1, 6), 1),
                    condition="good"
                )
                equipment.append(eq)
        
        session.add_all(equipment)
        await session.flush()
        print(f"Created {len(equipment)} equipment records")
        
        # Create stipends
        stipends = []
        for soldier in soldiers:
            for month in range(1, 4):
                stipend = Stipend(
                    soldier_id=soldier.id,
                    month=month,
                    year=2024,
                    base_amount=random.uniform(30000, 50000),
                    allowances=random.uniform(5000, 15000),
                    deductions=random.uniform(1000, 5000),
                    net_amount=random.uniform(35000, 60000),
                    payment_status=random.choice([PaymentStatus.PENDING, PaymentStatus.COMPLETED]),
                    payment_date=datetime.now() if month < 3 else None
                )
                stipends.append(stipend)
        
        session.add_all(stipends)
        await session.flush()
        print(f"Created {len(stipends)} stipend records")
        
        # Create performance rankings
        rankings = []
        for soldier in soldiers:
            for month in range(1, 4):
                ranking = PerformanceRanking(
                    soldier_id=soldier.id,
                    battalion_id=soldier.battalion_id,
                    month=month,
                    year=2024,
                    fitness_score=random.uniform(70, 100),
                    weapon_score=random.uniform(70, 100),
                    mental_score=random.uniform(70, 100),
                    attendance_score=random.uniform(80, 100),
                    discipline_score=random.uniform(80, 100),
                    overall_score=random.uniform(75, 100),
                    rank=random.randint(1, 10)
                )
                rankings.append(ranking)
        
        session.add_all(rankings)
        await session.flush()
        print(f"Created {len(rankings)} performance rankings")
        
        # Create exam centers
        exam_centers = [
            ExamCenter(
                center_code="DELHI001",
                center_name="Delhi Examination Center",
                address="Rajinder Nagar, Delhi",
                city="Delhi",
                state="Delhi",
                pincode="110060",
                capacity=500,
                current_booked=250,
                is_active=True
            ),
            ExamCenter(
                center_code="MUMBAI001",
                center_name="Mumbai Examination Center",
                address="Dadar, Mumbai",
                city="Mumbai",
                state="Maharashtra",
                pincode="400028",
                capacity=400,
                current_booked=200,
                is_active=True
            ),
            ExamCenter(
                center_code="LUCKNOW001",
                center_name="Lucknow Examination Center",
                address="Gomti Nagar, Lucknow",
                city="Lucknow",
                state="Uttar Pradesh",
                pincode="226010",
                capacity=300,
                current_booked=150,
                is_active=True
            ),
        ]
        session.add_all(exam_centers)
        await session.flush()
        print(f"Created {len(exam_centers)} exam centers")
        
        # Create exams
        exams = []
        for i, center in enumerate(exam_centers):
            exam = Exam(
                exam_name=f"Agniveer Selection Exam {2024-i}",
                exam_code=f"ASE{2024-i}",
                description="Written examination for Agniveer recruitment",
                exam_date=date(2024, 6 + i, 15),
                start_time=datetime(2024, 6 + i, 15, 9, 0),
                end_time=datetime(2024, 6 + i, 15, 12, 0),
                duration_minutes=180,
                exam_center_id=center.id,
                is_published=True,
                total_questions=100,
                total_marks=100,
                passing_marks=40
            )
            exams.append(exam)
        
        session.add_all(exams)
        await session.flush()
        print(f"Created {len(exams)} exams")
        
        # Create exam questions
        questions = []
        for exam in exams:
            for i in range(20):
                question = ExamQuestion(
                    exam_id=exam.id,
                    question_text=f"Sample question {i+1}: What is the capital of India?",
                    question_type="multiple_choice",
                    options='["Delhi", "Mumbai", "Chennai", "Kolkata"]',
                    correct_answer="Delhi",
                    marks=1,
                    negative_marks=0.25,
                    category=random.choice(["General Knowledge", "Math", "Reasoning", "English"]),
                    difficulty=random.choice(["easy", "medium", "hard"]),
                    is_active=True
                )
                questions.append(question)
        
        session.add_all(questions)
        await session.flush()
        print(f"Created {len(questions)} exam questions")
        
        # Create exam registrations
        registrations = []
        for i, candidate in enumerate(candidates[:10]):
            if i < len(exams):
                reg = ExamRegistration(
                    candidate_id=candidate.id,
                    exam_id=exams[i % len(exams)].id,
                    registration_number=f"REG{2024}{1000+i}",
                    status=random.choice(["registered", "appeared"]),
                    is_present=random.choice([True, False]),
                    marks_obtained=random.uniform(40, 90) if random.random() > 0.3 else None,
                    total_marks=100,
                    result_status=random.choice(["qualified", "not_qualified"])
                )
                registrations.append(reg)
        
        session.add_all(registrations)
        await session.flush()
        print(f"Created {len(registrations)} exam registrations")
        
        # Create admit cards
        admit_cards = []
        for reg in registrations:
            if reg.status == "registered":
                admit = AdmitCard(
                    candidate_id=reg.candidate_id,
                    exam_id=reg.exam_id,
                    exam_registration_id=reg.id,
                    admit_card_number=f"ADMIT{reg.registration_number}",
                    exam_venue="Examination Center Hall A",
                    exam_date=date(2024, 6, 15),
                    exam_start_time="09:00 AM",
                    exam_end_time="12:00 PM",
                    generated_at=datetime.now()
                )
                admit_cards.append(admit)
        
        session.add_all(admit_cards)
        await session.flush()
        print(f"Created {len(admit_cards)} admit cards")
        
        await session.commit()
        
        print("\n" + "="*50)
        print("Demo data created successfully!")
        print("="*50)
        print("\nLogin credentials (password: admin123):")
        print("  Admin: admin@agniveer.gov.in / admin")
        print("  Super Admin: superadmin@agniveer.gov.in / superadmin")
        print("  Trainer: trainer1@agniveer.gov.in / trainer_nature")
        print("  Doctor: doctor1@agniveer.gov.in / doctor_medical")
        print("  Candidate: candidate1@email.com / candidate1")
        print("  Soldier: soldier1@agniveer.gov.in / soldier1")


if __name__ == "__main__":
    asyncio.run(create_demo_data())
