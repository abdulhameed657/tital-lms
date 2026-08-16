import os
import json
from datetime import datetime, timedelta
from titan_lms import create_app
from titan_lms.models import (
    db, User, Course, Lesson, Enrollment, Quiz, Question, 
    QuizAttempt, StudentAnswer, Certificate, Badge, UserBadge, 
    RewardItem, Redemption, ForumThread, ForumPost, Message, 
    Notification, AuditLog, RevenueRecord, CourseSchedule, Event,
    AttendanceSession, AttendanceRecord
)

def seed_database():
    app = create_app()
    with app.app_context():
        print("Dropping existing tables...")
        db.drop_all()
        print("Creating tables...")
        db.create_all()
        
        print("Seeding Users...")
        # 1 Admin
        admin = User(
            name="Arthur Titan",
            email="admin@titan.com",
            role="admin",
            avatar_url="https://images.unsplash.com/photo-1560250097-0b93528c311a?w=150",
            bio="System Architect and Chief Educational Officer at Titan LMS.",
            points=1200,
            streak=15,
            verified=True
        )
        admin.set_password("admin123")
        
        # 2 Instructors
        instructor1 = User(
            name="Dr. Sarah Jenkins",
            email="instructor1@titan.edu",
            role="instructor",
            avatar_url="https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150",
            bio="Ph.D. in Computer Science. Expert in Full Stack Engineering, Python, Flask, and Distributed Databases.",
            points=800,
            streak=4,
            verified=True
        )
        instructor1.set_password("instpass1")
        
        instructor2 = User(
            name="Prof. Marcus Vance",
            email="instructor2@titan.edu",
            role="instructor",
            avatar_url="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150",
            bio="Systems Architect and AI Researcher. Specializes in interactive cloud sandboxes and infrastructure.",
            points=950,
            streak=8,
            verified=True
        )
        instructor2.set_password("instpass2")
        
        # 5 Students
        student1 = User(
            name="Alex Rivera",
            email="student1@titan.edu",
            role="student",
            roll_number="466960",
            avatar_url="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150",
            bio="Aspiring Software Engineer. Enjoys backend systems and building interactive web apps.",
            points=450,
            streak=5,
            verified=True
        )
        student1.set_password("studpass1")
        
        student2 = User(
            name="David Chen",
            email="student2@titan.edu",
            role="student",
            roll_number="466961",
            avatar_url="https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150",
            bio="Undergrad student. Interested in UI/UX and full stack templates.",
            points=120,
            streak=2,
            verified=True
        )
        student2.set_password("studpass2")
        
        student3 = User(
            name="Emily Watson",
            email="student3@titan.edu",
            role="student",
            roll_number="466962",
            avatar_url="https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150",
            bio="Junior Engineer seeking a career switch. Addicted to earning badges on Titan!",
            points=980,
            streak=12,
            verified=True
        )
        student3.set_password("studpass3")
        
        student4 = User(
            name="Sophia Martinez",
            email="student4@titan.edu",
            role="student",
            roll_number="466963",
            avatar_url="https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=150",
            bio="Freshly enrolled student looking forward to systems engineering courses.",
            points=0,
            streak=0,
            verified=True
        )
        student4.set_password("studpass4")
        
        student5 = User(
            name="Michael Novak",
            email="student5@titan.edu",
            role="student",
            roll_number="466964",
            avatar_url="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150",
            bio="New user awaiting validation code.",
            points=0,
            streak=0,
            verified=False,
            verification_token="verification-token-novak"
        )
        student5.set_password("studpass5")
        
        db.session.add_all([admin, instructor1, instructor2, student1, student2, student3, student4, student5])
        db.session.commit()
        
        print("Seeding Courses...")
        # Course 1
        course1 = Course(
            instructor_id=instructor1.id,
            title="Web Development Bootcamp",
            description="A comprehensive guide to full-stack web development. Learn HTML, CSS, JavaScript, Tailwind, and Flask from scratch. Deploy real database-backed projects.",
            thumbnail="https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=600",
            price=99.00,
            category="Development",
            level="Beginner",
            status="published"
        )
        # Course 2
        course2 = Course(
            instructor_id=instructor2.id,
            title="Interactive Systems Engineering",
            description="Deep dive into interactive systems, cloud deployments, virtual sandboxes, and UNIX terminal architecture. Build scalable, high-performance tools.",
            thumbnail="https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=600",
            price=149.00,
            category="Engineering",
            level="Intermediate",
            status="published"
        )
        # Course 3 (Draft for Course Management demo)
        course3 = Course(
            instructor_id=instructor1.id,
            title="Advanced Data Structures & Algorithms",
            description="Master advanced algorithms, dynamic programming, graphs, and system design. For students preparing for top technical interviews.",
            thumbnail="https://images.unsplash.com/photo-1618401471353-b98aedd07871?w=600",
            price=199.00,
            category="Algorithms",
            level="Advanced",
            status="draft"
        )
        
        db.session.add_all([course1, course2, course3])
        db.session.commit()
        
        print("Seeding Lessons...")
        # Lessons for Course 1
        c1_l1 = Lesson(
            course_id=course1.id,
            order=1,
            title="Introduction to Web Development",
            content_type="text",
            content="Welcome to the Web Development Bootcamp! In this lesson, we will understand how the web works, client-server models, HTTP requests, and the role of HTML, CSS, and JavaScript in modern applications. Write down your learning objectives before starting.",
            duration=15
        )
        c1_l2 = Lesson(
            course_id=course1.id,
            order=2,
            title="Mastering Tailwind CSS Layouts",
            content_type="video",
            content="https://www.w3schools.com/html/mov_bbb.mp4", # Sample video URL
            duration=25
        )
        c1_l3 = Lesson(
            course_id=course1.id,
            order=3,
            title="Building Your First Flask Server",
            content_type="video",
            content="https://www.w3schools.com/html/movie.mp4",
            duration=35
        )
        c1_l4 = Lesson(
            course_id=course1.id,
            order=4,
            title="Final Assessment Quiz",
            content_type="quiz",
            content="Use the quiz tab to complete this lesson and earn your certificate.",
            duration=20
        )
        
        # Lessons for Course 2
        c2_l1 = Lesson(
            course_id=course2.id,
            order=1,
            title="Distributed Architectures Overview",
            content_type="text",
            content="Learn about microservices, message queues, and high availability systems. This lesson outlines how distributed systems handle high request loads using load balancing.",
            duration=20
        )
        c2_l2 = Lesson(
            course_id=course2.id,
            order=2,
            title="Lab: Linux Shell Essentials",
            content_type="lab",
            content="In this live terminal lab, you will run command line operations to manage local servers, query logs, and edit configuration parameters in a secure sandbox.",
            duration=40
        )
        c2_l3 = Lesson(
            course_id=course2.id,
            order=3,
            title="Midterm Evaluation Quiz",
            content_type="quiz",
            content="Test your systems design and command line knowledge.",
            duration=15
        )
        
        db.session.add_all([c1_l1, c1_l2, c1_l3, c1_l4, c2_l1, c2_l2, c2_l3])
        db.session.commit()
        
        print("Seeding Quizzes & Questions...")
        # Quiz 1
        q1 = Quiz(lesson_id=c1_l4.id, course_id=course1.id, title="Bootcamp Final Quiz", time_limit=600)
        db.session.add(q1)
        db.session.commit()
        
        q1_q1 = Question(
            quiz_id=q1.id,
            question_text="What does CSS stand for?",
            question_type="multiple_choice",
            choices=json.dumps(["Cascading Style Sheets", "Computer Style Sheets", "Creative Style Sheets", "Colorful Style Sheets"]),
            correct_answer="Cascading Style Sheets"
        )
        q1_q2 = Question(
            quiz_id=q1.id,
            question_text="Which decorator is used to define a route in Flask?",
            question_type="multiple_choice",
            choices=json.dumps(["@app.route", "@app.link", "@app.blueprint", "@flask.route"]),
            correct_answer="@app.route"
        )
        db.session.add_all([q1_q1, q1_q2])
        
        # Quiz 2
        q2 = Quiz(lesson_id=c2_l3.id, course_id=course2.id, title="Systems Midterm Quiz", time_limit=300)
        db.session.add(q2)
        db.session.commit()
        
        q2_q1 = Question(
            quiz_id=q2.id,
            question_text="Which command displays the current working directory path in UNIX systems?",
            question_type="multiple_choice",
            choices=json.dumps(["pwd", "ls", "cd", "whereis"]),
            correct_answer="pwd"
        )
        db.session.add(q2_q1)
        db.session.commit()
        
        print("Seeding Enrollments with Course-Specific Roll Numbers...")
        # Alex (student1) - enrolled in Course 1 & Course 2 with distinct Roll Numbers
        e1_c1 = Enrollment(user_id=student1.id, course_id=course1.id, roll_number="466960", progress_pct=85, enrolled_at=datetime.utcnow() - timedelta(days=10))
        e1_c2 = Enrollment(user_id=student1.id, course_id=course2.id, roll_number="466961", progress_pct=40, enrolled_at=datetime.utcnow() - timedelta(days=5))
        # David (student2)
        e2_c1 = Enrollment(user_id=student2.id, course_id=course1.id, roll_number="466962", progress_pct=10, enrolled_at=datetime.utcnow() - timedelta(days=2))
        # Emily (student3) - enrolled in Course 1 & Course 2 with distinct Roll Numbers
        e3_c1 = Enrollment(user_id=student3.id, course_id=course1.id, roll_number="466963", progress_pct=100, enrolled_at=datetime.utcnow() - timedelta(days=20), completed_at=datetime.utcnow() - timedelta(days=2))
        e3_c2 = Enrollment(user_id=student3.id, course_id=course2.id, roll_number="466964", progress_pct=75, enrolled_at=datetime.utcnow() - timedelta(days=8))
        # Novak (student5)
        e5_c1 = Enrollment(user_id=student5.id, course_id=course1.id, roll_number="466965", progress_pct=0, enrolled_at=datetime.utcnow() - timedelta(days=1))
        
        db.session.add_all([e1_c1, e1_c2, e2_c1, e3_c1, e3_c2, e5_c1])
        db.session.commit()
        
        print("Seeding Quiz Attempts...")
        # Emily completed Final Quiz
        attempt = QuizAttempt(
            user_id=student3.id,
            quiz_id=q1.id,
            score=100.0,
            passed=True,
            attempted_at=datetime.utcnow() - timedelta(days=2),
            ai_feedback="Outstanding performance! You selected Cascading Style Sheets and @app.route correctly. Your understanding of web styling rules and routing structures is expert level."
        )
        db.session.add(attempt)
        db.session.commit()
        
        sa1 = StudentAnswer(quiz_attempt_id=attempt.id, question_id=q1_q1.id, student_answer="Cascading Style Sheets", is_correct=True, ai_evaluation="Correct answer. CSS defines presentation style.")
        sa2 = StudentAnswer(quiz_attempt_id=attempt.id, question_id=q1_q2.id, student_answer="@app.route", is_correct=True, ai_evaluation="Correct answer. @app.route maps URLs to Python functions.")
        db.session.add_all([sa1, sa2])
        db.session.commit()
        
        # Alex failed attempt
        attempt2 = QuizAttempt(
            user_id=student1.id,
            quiz_id=q1.id,
            score=50.0,
            passed=False,
            attempted_at=datetime.utcnow() - timedelta(days=1),
            ai_feedback="Good effort. You correctly identified CSS, but selected @app.blueprint instead of @app.route for basic routing. Remember that Blueprints partition apps while route decorators define endpoints."
        )
        db.session.add(attempt2)
        db.session.commit()
        
        sa3 = StudentAnswer(quiz_attempt_id=attempt2.id, question_id=q1_q1.id, student_answer="Cascading Style Sheets", is_correct=True, ai_evaluation="Correct answer.")
        sa4 = StudentAnswer(quiz_attempt_id=attempt2.id, question_id=q1_q2.id, student_answer="@app.blueprint", is_correct=False, ai_evaluation="Incorrect. @app.blueprint is for defining Blueprints; @app.route is for mapping endpoints.")
        db.session.add_all([sa3, sa4])
        db.session.commit()
        
        print("Seeding Certificates...")
        cert = Certificate(
            user_id=student3.id,
            course_id=course1.id,
            issued_at=datetime.utcnow() - timedelta(days=2),
            pdf_path="static/uploads/certificate_emily_1.pdf"
        )
        db.session.add(cert)
        db.session.commit()
        
        print("Seeding Badges...")
        b1 = Badge(name="First Code", description="Enrolled in your first development course.", icon="code", points_cost=50)
        b2 = Badge(name="Quiz Master", description="Scored 100% on any lesson assessment.", icon="quiz", points_cost=100)
        b3 = Badge(name="Titan Champion", description="Completed a full course syllabus.", icon="emoji_events", points_cost=200)
        b4 = Badge(name="Streak Sentinel", description="Maintained a 10-day learning streak.", icon="local_fire_department", points_cost=150)
        b5 = Badge(name="AI Pioneer", description="Generated your first custom quiz using AI.", icon="psychology", points_cost=100)
        
        db.session.add_all([b1, b2, b3, b4, b5])
        db.session.commit()
        
        # User Badges
        ub1 = UserBadge(user_id=student3.id, badge_id=b1.id)
        ub2 = UserBadge(user_id=student3.id, badge_id=b2.id)
        ub3 = UserBadge(user_id=student3.id, badge_id=b3.id)
        ub4 = UserBadge(user_id=student3.id, badge_id=b4.id)
        
        ub5 = UserBadge(user_id=student1.id, badge_id=b1.id)
        ub6 = UserBadge(user_id=student1.id, badge_id=b4.id)
        
        ub7 = UserBadge(user_id=student2.id, badge_id=b1.id)
        
        db.session.add_all([ub1, ub2, ub3, ub4, ub5, ub6, ub7])
        db.session.commit()
        
        print("Seeding Reward Items...")
        r1 = RewardItem(name="Exclusive Titan Swag Hoodie", description="Premium heavyweight cotton hoodie with custom metallic gold Titan logo embroidery.", points_cost=500, icon="shopping_bag")
        r2 = RewardItem(name="1-on-1 Code Review Session", description="A 30-minute private video session with Dr. Jenkins to review your repository design.", points_cost=800, icon="video_call")
        r3 = RewardItem(name="Dynamic Portfolio Glow-up", description="Professional review of your dynamic student portfolio page by our top enterprise recruiters.", points_cost=300, icon="rate_review")
        
        db.session.add_all([r1, r2, r3])
        db.session.commit()
        
        # Emily redeemed hoodie
        red1 = Redemption(user_id=student3.id, reward_item_id=r1.id, redeemed_at=datetime.utcnow() - timedelta(days=3))
        student3.points -= r1.points_cost
        db.session.add(red1)
        db.session.commit()
        
        print("Seeding Forum Threads & Posts...")
        ft1 = ForumThread(
            title="Handling circular imports in Flask-SQLAlchemy?",
            content="I am setting up a clean blueprints structure, but when importing my database connection from titan_lms in my routes, I hit a circular import block. What's the clean way to handle this in Python?",
            user_id=student1.id,
            category="Development"
        )
        db.session.add(ft1)
        db.session.commit()
        
        fp1 = ForumPost(
            thread_id=ft1.id,
            user_id=instructor1.id,
            content="A great way is to use the App Factory pattern. Define your db object globally in models.py (or a shared file) without initializing it (don't pass 'app'). Then, import 'db' in your __init__.py and call 'db.init_app(app)' inside create_app(). Finally, import your models and blueprints inside create_app() so they aren't loaded at definition time."
        )
        fp2 = ForumPost(
            thread_id=ft1.id,
            user_id=student1.id,
            content="Brilliant, Dr. Jenkins! I modified my imports, initialized inside the factory, and now it spins up perfectly. Thanks for the quick feedback!"
        )
        db.session.add_all([fp1, fp2])
        db.session.commit()
        
        print("Seeding Inbox Messages...")
        msg1 = Message(sender_id=student1.id, recipient_id=instructor1.id, content="Hi Dr. Sarah, will we cover Docker compose in the backend module of Web Dev Bootcamp?", created_at=datetime.utcnow() - timedelta(days=2))
        msg2 = Message(sender_id=instructor1.id, recipient_id=student1.id, content="Yes, Alex! In Module 4 we'll learn container orchestration, writing a docker-compose.yml file, and hooking Flask up to a live PostgreSQL container.", created_at=datetime.utcnow() - timedelta(days=2) + timedelta(hours=1))
        msg3 = Message(sender_id=student1.id, recipient_id=instructor1.id, content="Awesome! Looking forward to it. I'll read ahead on docker network namespaces.", created_at=datetime.utcnow() - timedelta(days=1), is_read=True)
        db.session.add_all([msg1, msg2, msg3])
        db.session.commit()
        
        print("Seeding Notifications...")
        n1 = Notification(user_id=student1.id, title="Badge Earned", content="You have earned the 'Streak Sentinel' badge for studying 5 days in a row!", type="achievement")
        n2 = Notification(user_id=student1.id, title="New Reply", content="Dr. Sarah Jenkins replied to your thread in 'Development'.", type="info")
        n3 = Notification(user_id=student3.id, title="Certificate Generated", content="Your official course certificate for 'Web Development Bootcamp' has been issued.", type="success")
        
        db.session.add_all([n1, n2, n3])
        db.session.commit()
        
        print("Seeding Revenue Records...")
        # Emily bought Web Dev ($99) and Systems ($149)
        rev1 = RevenueRecord(course_id=course1.id, user_id=student3.id, amount=99.00, instructor_earnings=79.20, platform_earnings=19.80, created_at=datetime.utcnow() - timedelta(days=20))
        rev2 = RevenueRecord(course_id=course2.id, user_id=student3.id, amount=149.00, instructor_earnings=119.20, platform_earnings=29.80, created_at=datetime.utcnow() - timedelta(days=8))
        # Alex bought Web Dev ($99) and Systems ($149)
        rev3 = RevenueRecord(course_id=course1.id, user_id=student1.id, amount=99.00, instructor_earnings=79.20, platform_earnings=19.80, created_at=datetime.utcnow() - timedelta(days=10))
        rev4 = RevenueRecord(course_id=course2.id, user_id=student1.id, amount=149.00, instructor_earnings=119.20, platform_earnings=29.80, created_at=datetime.utcnow() - timedelta(days=5))
        # David bought Web Dev ($99)
        rev5 = RevenueRecord(course_id=course1.id, user_id=student2.id, amount=99.00, instructor_earnings=79.20, platform_earnings=19.80, created_at=datetime.utcnow() - timedelta(days=2))
        
        db.session.add_all([rev1, rev2, rev3, rev4, rev5])
        db.session.commit()
        
        print("Seeding Audit Logs...")
        log1 = AuditLog(user_id=admin.id, action="Admin console accessed", ip_address="192.168.1.50", user_agent="Mozilla/5.0 Chrome/120.0")
        log2 = AuditLog(user_id=student5.id, action="User signup initiated (Unverified)", ip_address="192.168.1.102", user_agent="Mozilla/5.0 Safari/605.1")
        log3 = AuditLog(user_id=student3.id, action="Course Web Development Bootcamp completed", ip_address="10.0.0.12", user_agent="Mozilla/5.0 Firefox/121.0")
        
        db.session.add_all([log1, log2, log3])
        db.session.commit()
        
        print("Seeding Course Schedules & Approval Workflow...")
        s_start1 = datetime.utcnow().date() - timedelta(days=14)
        s_end1 = datetime.utcnow().date() + timedelta(days=35)
        tot1 = CourseSchedule.calculate_total_classes(s_start1, s_end1, "Monday, Wednesday, Friday")
        cs1 = CourseSchedule(
            course_id=course1.id,
            instructor_id=instructor1.id,
            title="Web Dev Bootcamp - Morning Regular Batch",
            days_of_week="Monday, Wednesday, Friday",
            start_time="09:00 AM",
            end_time="10:30 AM",
            start_date=s_start1,
            end_date=s_end1,
            total_classes=tot1,
            completed_classes=6,
            room_or_link="Lab 101 / Zoom Room Alpha",
            status="approved",
            created_by_id=instructor1.id
        )

        s_start2 = datetime.utcnow().date() - timedelta(days=7)
        s_end2 = datetime.utcnow().date() + timedelta(days=42)
        tot2 = CourseSchedule.calculate_total_classes(s_start2, s_end2, "Tuesday, Thursday")
        cs2 = CourseSchedule(
            course_id=course2.id,
            instructor_id=instructor2.id,
            title="Distributed Systems & Cloud - Evening Batch",
            days_of_week="Tuesday, Thursday",
            start_time="04:00 PM",
            end_time="06:00 PM",
            start_date=s_start2,
            end_date=s_end2,
            total_classes=tot2,
            completed_classes=3,
            room_or_link="Auditorium B / Live Stream",
            status="approved",
            created_by_id=admin.id
        )

        s_start3 = datetime.utcnow().date() + timedelta(days=3)
        s_end3 = datetime.utcnow().date() + timedelta(days=30)
        tot3 = CourseSchedule.calculate_total_classes(s_start3, s_end3, "Saturday, Sunday")
        cs3 = CourseSchedule(
            course_id=course1.id,
            instructor_id=instructor1.id,
            title="Weekend Web Engineering Intensive",
            days_of_week="Saturday, Sunday",
            start_time="11:00 AM",
            end_time="02:00 PM",
            start_date=s_start3,
            end_date=s_end3,
            total_classes=tot3,
            completed_classes=0,
            room_or_link="Online Live Classroom 3",
            status="pending_approval",
            created_by_id=instructor1.id
        )

        db.session.add_all([cs1, cs2, cs3])
        db.session.commit()

        print("Seeding Campus & Course Events...")
        ev1 = Event(
            title="AI & LLM RAG Pipeline Workshop",
            event_type="workshop",
            course_id=course1.id,
            created_by_id=admin.id,
            event_date=datetime.utcnow().date() + timedelta(days=4),
            start_time="02:00 PM",
            end_time="05:00 PM",
            location_or_link="Main Auditorium & Youtube Stream",
            description="Hands-on workshop building AI-powered RAG applications with Python and vector databases.",
            status="published"
        )
        ev2 = Event(
            title="Mid-Term Live Coding Assessment",
            event_type="exam",
            course_id=course1.id,
            created_by_id=instructor1.id,
            event_date=datetime.utcnow().date() + timedelta(days=9),
            start_time="10:00 AM",
            end_time="01:00 PM",
            location_or_link="Computer Lab 4",
            description="Comprehensive practical assessment covering Flask, SQLAlchemy, and API design.",
            status="published"
        )
        ev3 = Event(
            title="Enterprise Cloud Scalability Talk",
            event_type="guest_lecture",
            course_id=course2.id,
            created_by_id=instructor2.id,
            event_date=datetime.utcnow().date() + timedelta(days=15),
            start_time="03:00 PM",
            end_time="04:30 PM",
            location_or_link="Virtual Seminar Room 1",
            description="Keynote by Principal Infrastructure Engineers on scaling Kubernetes clusters.",
            status="pending_approval"
        )
        ev4 = Event(
            title="Annual Tech Symposium & Holiday",
            event_type="holiday",
            course_id=None,
            created_by_id=admin.id,
            event_date=datetime.utcnow().date() + timedelta(days=20),
            start_time="09:00 AM",
            end_time="06:00 PM",
            location_or_link="Titan Campus Ground",
            description="Campus-wide holiday and technical showcase. Regular lectures suspended.",
            status="published"
        )

        db.session.add_all([ev1, ev2, ev3, ev4])
        db.session.commit()
        
        print("Database successfully seeded!")

if __name__ == "__main__":
    seed_database()
