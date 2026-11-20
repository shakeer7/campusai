import logging
from datetime import date, timedelta
from app.core.database import SessionLocal, init_db
from app.auth.security import get_password_hash
from app.models.user import User, RoleEnum
from app.models.academic import Department, Course, Subject, SyllabusTopic, Enrollment, Timetable
from app.models.profile import Student, Faculty
from app.models.records import AttendanceRecord, AttendanceStatusEnum, ExamSchedule, ExamResult, Fee, FeeStatusEnum
from app.models.rag import Document, DocumentChunk, DocumentTypeEnum
from app.rag.embedder import generate_embedding

logger = logging.getLogger("campusai.seed")


def seed_database():
    logger.info("Verifying seed data...")
    init_db()
    db = SessionLocal()

    try:
        # Check if already seeded
        if db.query(User).filter(User.email == "student@cbit.ac.in").first():
            logger.info("Database already contains seed data. Skipping.")
            return

        logger.info("Creating Departments and Courses...")
        dept_cse = Department(code="CSE", name="Computer Science and Engineering", description="Department of Computer Science & Engineering, CBIT")
        dept_it = Department(code="IT", name="Information Technology", description="Department of Information Technology, CBIT")
        dept_ece = Department(code="ECE", name="Electronics & Communication", description="Department of ECE, CBIT")
        dept_aids = Department(code="AIDS", name="Artificial Intelligence & Data Science", description="Department of AI & DS, CBIT")
        db.add_all([dept_cse, dept_it, dept_ece, dept_aids])
        db.flush()

        course_cse = Course(department_id=dept_cse.id, name="B.E. Computer Science & Engineering", degree="B.E.", duration_years=4, total_semesters=8)
        course_it = Course(department_id=dept_it.id, name="B.Tech Information Technology", degree="B.Tech", duration_years=4, total_semesters=8)
        db.add_all([course_cse, course_it])
        db.flush()

        logger.info("Creating Academic Subjects...")
        sub_ds = Subject(code="20CSC01", name="Data Structures and Algorithms", department_id=dept_cse.id, semester=6, credits=4, syllabus_overview="Linear & non-linear structures, graphs, trees, hashing, and complexity analysis.")
        sub_cloud = Subject(code="20ITC08", name="Cloud Computing and DevOps", department_id=dept_cse.id, semester=6, credits=3, syllabus_overview="Virtualization, AWS cloud architecture, containerization with Docker and Kubernetes.")
        sub_mgmt = Subject(code="20MBAC02", name="Strategic Management", department_id=dept_cse.id, semester=6, credits=3, syllabus_overview="Corporate strategy, SWOT analysis, business model innovation, and competitive advantage.")
        sub_dbms = Subject(code="20CSC05", name="Database Management Systems", department_id=dept_cse.id, semester=6, credits=4, syllabus_overview="Relational algebra, normalization, transactions, ACID properties, and PostgreSQL indexing.")
        sub_ml = Subject(code="20AIDSC03", name="Applied Machine Learning", department_id=dept_cse.id, semester=6, credits=3, syllabus_overview="Supervised and unsupervised models, neural networks, evaluation metrics, and embeddings.")
        db.add_all([sub_ds, sub_cloud, sub_mgmt, sub_dbms, sub_ml])
        db.flush()

        logger.info("Creating Syllabus Topics...")
        topics_data = [
            (sub_cloud.id, 1, "Cloud Architectural Fundamentals", "Virtualization, Hypervisors, IaaS, PaaS, SaaS, and Shared Responsibility Model"),
            (sub_cloud.id, 2, "AWS Core Services", "Amazon EC2, VPC Networking, Subnets, Route Tables, and Internet Gateways"),
            (sub_cloud.id, 3, "Cloud Storage and Databases", "Amazon S3, Amazon RDS PostgreSQL, DynamoDB, and Backup Lifecycle"),
            (sub_cloud.id, 4, "Containers and Kubernetes", "Docker architecture, Dockerfiles, EKS Managed Clusters, and Pod Orchestration"),
            (sub_cloud.id, 5, "DevOps, CI/CD, and Serverless", "AWS Lambda, API Gateway, GitHub Actions, and Infrastructure as Code using Terraform"),
            (sub_mgmt.id, 1, "Introduction to Strategic Management", "Strategic intent, Vision, Mission, and Core Competencies"),
            (sub_mgmt.id, 2, "Environmental and Industry Analysis", "Porter's 5 Forces Model, PESTLE analysis, and Competitor Intelligence"),
            (sub_mgmt.id, 3, "Strategy Formulation", "Generic competitive strategies, Cost Leadership, and Product Differentiation"),
            (sub_mgmt.id, 4, "Strategy Implementation", "Organizational structures, leadership styles, and change management"),
            (sub_mgmt.id, 5, "Strategic Evaluation and Control", "Balanced Scorecard, KPIs, and corporate governance compliance")
        ]
        for sid, unum, utitle, tname in topics_data:
            db.add(SyllabusTopic(subject_id=sid, unit_number=unum, unit_title=utitle, topic_name=tname, hours_allocated=8, learning_outcomes=f"Mastery of {utitle}"))
        db.flush()

        logger.info("Creating Demo Accounts...")
        user_admin = User(
            email="admin@cbit.ac.in",
            hashed_password=get_password_hash("Admin@123"),
            full_name="CBIT Systems Administrator",
            role=RoleEnum.ADMIN,
            phone="+91-9848011223"
        )
        user_fac = User(
            email="faculty@cbit.ac.in",
            hashed_password=get_password_hash("Faculty@123"),
            full_name="Dr. K. Srinivas",
            role=RoleEnum.FACULTY,
            phone="+91-9848022334"
        )
        db.add_all([user_admin, user_fac])
        db.flush()

        fac_profile = Faculty(
            user_id=user_fac.id,
            employee_id="CBIT-FAC-0104",
            department_id=dept_cse.id,
            designation="Professor & Head of Department",
            cabin_location="CSE Block, Room 302"
        )
        db.add(fac_profile)
        db.flush()

        user_stud1 = User(
            email="student@cbit.ac.in",
            hashed_password=get_password_hash("Student@123"),
            full_name="Rohan Reddy",
            role=RoleEnum.STUDENT,
            phone="+91-9848033445"
        )
        user_stud2 = User(
            email="ananya@cbit.ac.in",
            hashed_password=get_password_hash("Student@123"),
            full_name="Ananya Sharma",
            role=RoleEnum.STUDENT,
            phone="+91-9848044556"
        )
        db.add_all([user_stud1, user_stud2])
        db.flush()

        stud_profile1 = Student(
            user_id=user_stud1.id,
            roll_number="160121733001",
            department_id=dept_cse.id,
            course_id=course_cse.id,
            current_semester=6,
            academic_year="2025-2026",
            section="A",
            batch="2022-2026",
            cgpa=8.72
        )
        stud_profile2 = Student(
            user_id=user_stud2.id,
            roll_number="160121733045",
            department_id=dept_cse.id,
            course_id=course_cse.id,
            current_semester=6,
            academic_year="2025-2026",
            section="A",
            batch="2022-2026",
            cgpa=7.95
        )
        db.add_all([stud_profile1, stud_profile2])
        db.flush()

        subjects_list = [sub_ds, sub_cloud, sub_mgmt, sub_dbms, sub_ml]
        for s in [stud_profile1, stud_profile2]:
            for sub in subjects_list:
                db.add(Enrollment(student_id=s.id, subject_id=sub.id, semester=6, academic_year="2025-2026", status="active"))
        db.flush()

        base_date = date.today() - timedelta(days=35)
        for sub_idx, sub in enumerate(subjects_list):
            for day_offset in range(25):
                cur_date = base_date + timedelta(days=day_offset + (day_offset // 5) * 2)
                period = (sub_idx % 4) + 1
                status_rohan = AttendanceStatusEnum.PRESENT if (day_offset % 5 != 0) else AttendanceStatusEnum.ABSENT
                db.add(AttendanceRecord(
                    student_id=stud_profile1.id,
                    subject_id=sub.id,
                    faculty_id=fac_profile.id,
                    date=cur_date,
                    period_number=period,
                    status=status_rohan
                ))
                status_ananya = AttendanceStatusEnum.PRESENT if (day_offset % 3 != 0) else AttendanceStatusEnum.ABSENT
                db.add(AttendanceRecord(
                    student_id=stud_profile2.id,
                    subject_id=sub.id,
                    faculty_id=fac_profile.id,
                    date=cur_date,
                    period_number=period,
                    status=status_ananya
                ))
        db.flush()

        timetable_entries = [
            ("Monday", "09:30", "10:30", sub_cloud.id, "L-304"),
            ("Monday", "10:30", "11:30", sub_ds.id, "L-304"),
            ("Monday", "11:45", "12:45", sub_mgmt.id, "L-304"),
            ("Monday", "13:30", "15:30", sub_dbms.id, "CSE-LAB-2"),
            ("Tuesday", "09:30", "10:30", sub_dbms.id, "L-304"),
            ("Tuesday", "10:30", "11:30", sub_cloud.id, "L-304"),
            ("Tuesday", "11:45", "12:45", sub_ml.id, "L-304"),
            ("Wednesday", "09:30", "10:30", sub_ds.id, "L-304"),
            ("Wednesday", "10:30", "11:30", sub_mgmt.id, "L-304"),
            ("Thursday", "09:30", "10:30", sub_cloud.id, "L-304"),
            ("Thursday", "10:30", "12:30", sub_ml.id, "AI-LAB-1"),
            ("Friday", "09:30", "10:30", sub_dbms.id, "L-304"),
            ("Friday", "10:30", "11:30", sub_ds.id, "L-304"),
            ("Friday", "11:45", "12:45", sub_mgmt.id, "L-304")
        ]
        for day, st, et, sub_id, room in timetable_entries:
            db.add(Timetable(
                department_id=dept_cse.id,
                semester=6,
                section="A",
                subject_id=sub_id,
                faculty_id=fac_profile.id,
                day_of_week=day,
                start_time=st,
                end_time=et,
                room_number=room
            ))
        db.flush()

        results_rohan_sem5 = [
            (sub_ds.id, 5, 28.0, 64.0, 92.0, "O", 10.0, 4),
            (sub_dbms.id, 5, 27.0, 58.0, 85.0, "A+", 9.0, 4),
            (sub_cloud.id, 5, 25.0, 56.0, 81.0, "A+", 9.0, 3),
            (sub_mgmt.id, 5, 26.0, 52.0, 78.0, "A", 8.0, 3),
            (sub_ml.id, 5, 28.0, 57.0, 85.0, "A+", 9.0, 3)
        ]
        for sub_id, sem, internal, external, total, grade, gp, cred in results_rohan_sem5:
            db.add(ExamResult(
                student_id=stud_profile1.id,
                subject_id=sub_id,
                semester=sem,
                internal_marks=internal,
                external_marks=external,
                total_marks=total,
                grade=grade,
                grade_points=gp,
                sgpa=8.95,
                credits_earned=cred
            ))

        fee_rohan_1 = Fee(
            student_id=stud_profile1.id,
            academic_year="2025-2026",
            semester=6,
            fee_type="Tuition Fee (Semester 6)",
            total_amount=65000.0,
            paid_amount=65000.0,
            due_date=date.today() + timedelta(days=60),
            status=FeeStatusEnum.PAID
        )
        fee_rohan_2 = Fee(
            student_id=stud_profile1.id,
            academic_year="2025-2026",
            semester=6,
            fee_type="University Examination & Lab Fee",
            total_amount=3500.0,
            paid_amount=0.0,
            due_date=date.today() + timedelta(days=20),
            status=FeeStatusEnum.PENDING
        )
        db.add_all([fee_rohan_1, fee_rohan_2])

        doc_syllabus = Document(
            title="CBIT B.E. Computer Science R20 Academic Regulations & Syllabus",
            doc_type=DocumentTypeEnum.SYLLABUS,
            department_id=dept_cse.id,
            course_id=course_cse.id,
            semester=6,
            file_size_bytes=1048576,
            mime_type="application/pdf",
            uploaded_by=user_admin.id
        )
        db.add(doc_syllabus)
        db.flush()

        syllabus_chunks = [
            (1, "Chaitanya Bharathi Institute of Technology (Autonomous), Hyderabad - 500075. Academic Regulations R-20 for B.E. 4-Year Degree Programme. Attendance Criteria: A student shall be deemed eligible to appear for the semester-end examinations if they secure a minimum of 75% aggregate attendance in all registered subjects of that semester."),
            (2, "Condonation of shortage of attendance between 65% and 74.9% may be granted by the College Academic Committee on genuine medical grounds subject to submission of authentic medical certificate, prescription, and condonation fee within 3 days of resuming classes."),
            (3, "Course: 20ITC08 Cloud Computing and DevOps. Unit 1 covers Cloud virtualization, hypervisors, service models (IaaS, PaaS, SaaS). Unit 2 covers Amazon Web Services (AWS) infrastructure: EC2, VPC, Security Groups, IAM Policies, and Load Balancers. Unit 3 covers Amazon S3 and RDS PostgreSQL."),
            (4, "Course: 20MBAC02 Strategic Management. Unit 1 introduces vision, mission, and corporate objectives. Unit 2 covers Porter's 5 forces industry analysis. Unit 3 covers generic competitive strategies including cost leadership, differentiation, and focus.")
        ]
        for pg, txt in syllabus_chunks:
            vec = generate_embedding(txt)
            db.add(DocumentChunk(
                document_id=doc_syllabus.id,
                chunk_index=pg - 1,
                content=txt,
                page_number=pg,
                token_count=len(txt.split()),
                embedding=vec
            ))

        db.commit()
        logger.info("Database seeding completed successfully.")

    except Exception as e:
        db.rollback()
        logger.error(f"Database seeding failed: {e}")
    finally:
        db.close()
