from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')  # 'student', 'instructor', 'admin'
    avatar_url = db.Column(db.Text, nullable=True)
    bio = db.Column(db.Text, nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    points = db.Column(db.Integer, default=0)
    assignment_points = db.Column(db.Integer, default=0)
    quiz_points = db.Column(db.Integer, default=0)
    streak = db.Column(db.Integer, default=0)
    referral_code = db.Column(db.String(20), unique=True, nullable=True)
    roll_number = db.Column(db.String(30), unique=True, nullable=True)
    verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=True)

    # Relationships
    enrollments = db.relationship('Enrollment', back_populates='user', cascade='all, delete-orphan')
    certificates = db.relationship('Certificate', back_populates='user', cascade='all, delete-orphan')
    badges = db.relationship('UserBadge', back_populates='user', cascade='all, delete-orphan')
    redemptions = db.relationship('Redemption', back_populates='user', cascade='all, delete-orphan')
    forum_threads = db.relationship('ForumThread', back_populates='user', cascade='all, delete-orphan')
    forum_posts = db.relationship('ForumPost', back_populates='user', cascade='all, delete-orphan')
    sent_messages = db.relationship('Message', foreign_keys='Message.sender_id', back_populates='sender', cascade='all, delete-orphan')
    received_messages = db.relationship('Message', foreign_keys='Message.recipient_id', back_populates='recipient', cascade='all, delete-orphan')
    notifications = db.relationship('Notification', back_populates='user', cascade='all, delete-orphan')
    audit_logs = db.relationship('AuditLog', back_populates='user', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_roll_number(self, course=None):
        if course:
            c_id = course.id if hasattr(course, 'id') else course
            enr = Enrollment.query.filter_by(user_id=self.id, course_id=c_id).first()
            if enr:
                return enr.get_roll_number()
        if self.enrollments:
            return self.enrollments[0].get_roll_number()
        if self.roll_number:
            return self.roll_number
        base_no = 466960 + ((self.id or 1) - 1)
        return str(base_no)

class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    instructor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    thumbnail = db.Column(db.String(500), nullable=True)
    price = db.Column(db.Float, default=0.0)
    category = db.Column(db.String(100), nullable=True)
    level = db.Column(db.String(50), nullable=True)  # 'Beginner', 'Intermediate', 'Advanced'
    status = db.Column(db.String(20), default='draft')  # 'draft', 'published'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=True)
    access_code = db.Column(db.String(50), nullable=True, unique=True)
    student_limit = db.Column(db.Integer, default=100)

    # Relationships
    instructor = db.relationship('User', backref=db.backref('taught_courses', cascade='all, delete-orphan', lazy=True))
    lessons = db.relationship('Lesson', back_populates='course', cascade='all, delete-orphan', order_by='Lesson.order')
    enrollments = db.relationship('Enrollment', back_populates='course', cascade='all, delete-orphan')
    quizzes = db.relationship('Quiz', back_populates='course', cascade='all, delete-orphan')
    certificates = db.relationship('Certificate', back_populates='course', cascade='all, delete-orphan')
    revenue_records = db.relationship('RevenueRecord', back_populates='course', cascade='all, delete-orphan')

class Lesson(db.Model):
    __tablename__ = 'lessons'
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    order = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content_type = db.Column(db.String(50), nullable=False)  # 'video', 'text', 'quiz', 'lab'
    content = db.Column(db.Text, nullable=True)  # Video URL, article text, quiz JSON, or lab description
    duration = db.Column(db.Integer, default=0)  # In minutes
    due_date = db.Column(db.DateTime, nullable=True)

    course = db.relationship('Course', back_populates='lessons')
    quizzes = db.relationship('Quiz', back_populates='lesson', cascade='all, delete-orphan')

class Enrollment(db.Model):
    __tablename__ = 'enrollments'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    roll_number = db.Column(db.String(30), nullable=True)  # Course-specific Roll Number
    phone_number = db.Column(db.String(30), nullable=True)
    campus = db.Column(db.String(100), nullable=True)
    access_key_used = db.Column(db.String(100), nullable=True)
    progress_pct = db.Column(db.Integer, default=0)
    payment_status = db.Column(db.String(20), default='PAID')  # 'PAID', 'PENDING'
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship('User', back_populates='enrollments')
    course = db.relationship('Course', back_populates='enrollments')

    def get_roll_number(self):
        if self.roll_number:
            return self.roll_number
        base = 466960 + (self.id - 1)
        return str(base)

class Quiz(db.Model):
    __tablename__ = 'quizzes'
    id = db.Column(db.Integer, primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'), nullable=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    time_limit = db.Column(db.Integer, default=600)  # in seconds

    lesson = db.relationship('Lesson', back_populates='quizzes')
    course = db.relationship('Course', back_populates='quizzes')
    questions = db.relationship('Question', back_populates='quiz', cascade='all, delete-orphan')
    attempts = db.relationship('QuizAttempt', back_populates='quiz', cascade='all, delete-orphan')

class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(50), default='multiple_choice')  # 'multiple_choice', 'text', 'code'
    choices = db.Column(db.Text, nullable=True)  # JSON string array of choices
    correct_answer = db.Column(db.Text, nullable=False)

    quiz = db.relationship('Quiz', back_populates='questions')
    student_answers = db.relationship('StudentAnswer', back_populates='question', cascade='all, delete-orphan')

    def get_choices(self):
        if self.choices:
            try:
                return json.loads(self.choices)
            except:
                return []
        return []

class QuizAttempt(db.Model):
    __tablename__ = 'quiz_attempts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    score = db.Column(db.Float, default=0.0)  # Percentage score
    passed = db.Column(db.Boolean, default=False)
    attempted_at = db.Column(db.DateTime, default=datetime.utcnow)
    ai_feedback = db.Column(db.Text, nullable=True)

    user = db.relationship('User')
    quiz = db.relationship('Quiz', back_populates='attempts')
    answers = db.relationship('StudentAnswer', back_populates='quiz_attempt', cascade='all, delete-orphan')

class StudentAnswer(db.Model):
    __tablename__ = 'student_answers'
    id = db.Column(db.Integer, primary_key=True)
    quiz_attempt_id = db.Column(db.Integer, db.ForeignKey('quiz_attempts.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    student_answer = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    ai_evaluation = db.Column(db.Text, nullable=True)

    quiz_attempt = db.relationship('QuizAttempt', back_populates='answers')
    question = db.relationship('Question', back_populates='student_answers')

class Certificate(db.Model):
    __tablename__ = 'certificates'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    issued_at = db.Column(db.DateTime, default=datetime.utcnow)
    pdf_path = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', back_populates='certificates')
    course = db.relationship('Course', back_populates='certificates')

class Badge(db.Model):
    __tablename__ = 'badges'
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    icon = db.Column(db.String(50), nullable=True)  # Material icon name
    points_cost = db.Column(db.Integer, default=0)

class UserBadge(db.Model):
    __tablename__ = 'user_badges'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    badge_id = db.Column(db.Integer, db.ForeignKey('badges.id'), nullable=False)
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='badges')
    badge = db.relationship('Badge')

class RewardItem(db.Model):
    __tablename__ = 'reward_items'
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    points_cost = db.Column(db.Integer, nullable=False)
    icon = db.Column(db.String(50), nullable=True)

class Redemption(db.Model):
    __tablename__ = 'redemptions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reward_item_id = db.Column(db.Integer, db.ForeignKey('reward_items.id'), nullable=False)
    redeemed_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='redemptions')
    reward_item = db.relationship('RewardItem')

class ForumThread(db.Model):
    __tablename__ = 'forum_threads'
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category = db.Column(db.String(100), default='General')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='forum_threads')
    posts = db.relationship('ForumPost', back_populates='thread', cascade='all, delete-orphan')

class ForumPost(db.Model):
    __tablename__ = 'forum_posts'
    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.Integer, db.ForeignKey('forum_threads.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    thread = db.relationship('ForumThread', back_populates='posts')
    user = db.relationship('User', back_populates='forum_posts')

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

    sender = db.relationship('User', foreign_keys=[sender_id], back_populates='sent_messages')
    recipient = db.relationship('User', foreign_keys=[recipient_id], back_populates='received_messages')

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), default='info')  # 'info', 'alert', 'achievement'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

    user = db.relationship('User', back_populates='notifications')

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(200), nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='audit_logs')

class RevenueRecord(db.Model):
    __tablename__ = 'revenue_records'
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    instructor_earnings = db.Column(db.Float, nullable=False)
    platform_earnings = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    course = db.relationship('Course', back_populates='revenue_records')
    student = db.relationship('User', backref=db.backref('payments', cascade='all, delete-orphan', lazy=True))

class Coupon(db.Model):
    __tablename__ = 'coupons'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    discount_percent = db.Column(db.Integer, nullable=False, default=10)
    max_uses = db.Column(db.Integer, default=100)
    times_used = db.Column(db.Integer, default=0)
    expiry_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(30), default='pending_approval')  # 'pending_approval', 'approved', 'rejected'
    instructor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    instructor = db.relationship('User', backref=db.backref('created_coupons', cascade='all, delete-orphan', lazy=True))

class Webinar(db.Model):
    __tablename__ = 'webinars'
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    meeting_url = db.Column(db.String(500), nullable=False)
    scheduled_at = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, default=60)
    status = db.Column(db.String(20), default='scheduled') # 'scheduled', 'live', 'completed'
    instructor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    instructor = db.relationship('User', backref=db.backref('hosted_webinars', cascade='all, delete-orphan', lazy=True))
    course = db.relationship('Course', backref=db.backref('webinars', lazy=True))

class FlashcardDeck(db.Model):
    __tablename__ = 'flashcard_decks'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    topic = db.Column(db.String(100), default='General')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('flashcard_decks', lazy=True))
    cards = db.relationship('Flashcard', back_populates='deck', cascade='all, delete-orphan')

class Flashcard(db.Model):
    __tablename__ = 'flashcards'
    id = db.Column(db.Integer, primary_key=True)
    deck_id = db.Column(db.Integer, db.ForeignKey('flashcard_decks.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='unlearned')  # 'unlearned', 'learning', 'mastered'

    deck = db.relationship('FlashcardDeck', back_populates='cards')

class Tenant(db.Model):
    __tablename__ = 'tenants'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    subdomain = db.Column(db.String(100), unique=True, nullable=False)
    logo_url = db.Column(db.String(500), nullable=True)
    primary_color = db.Column(db.String(30), default='#0054CB')
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class RolePermission(db.Model):
    __tablename__ = 'role_permissions'
    id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(50), nullable=False)  # e.g., 'Content Moderator', 'Finance Admin'
    permission_key = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True)

class ModerationItem(db.Model):
    __tablename__ = 'moderation_items'
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=True)
    content_type = db.Column(db.String(50), nullable=False)  # 'comment', 'forum_thread', 'course_review'
    content_id = db.Column(db.Integer, nullable=False)
    text_preview = db.Column(db.Text, nullable=False)
    flag_reason = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'removed'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ReferralRecord(db.Model):
    __tablename__ = 'referral_records'
    id = db.Column(db.Integer, primary_key=True)
    referrer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    referred_email = db.Column(db.String(120), nullable=False)
    points_awarded = db.Column(db.Integer, default=500)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    referrer = db.relationship('User', backref=db.backref('referrals_sent', lazy=True))

class QuizBattleSession(db.Model):
    __tablename__ = 'quiz_battle_sessions'
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=True)
    battle_pin = db.Column(db.String(10), unique=True, nullable=False)
    title = db.Column(db.String(200), default='Titan Live Quiz Battle')
    host_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='lobby')  # 'lobby', 'active', 'finished'
    current_question = db.Column(db.Integer, default=0)
    total_questions = db.Column(db.Integer, default=5)
    timer_seconds = db.Column(db.Integer, default=15)
    question_start_time = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    host = db.relationship('User', backref=db.backref('hosted_battles', lazy=True))

class QuizBattleParticipant(db.Model):
    __tablename__ = 'quiz_battle_participants'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('quiz_battle_sessions.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    score = db.Column(db.Integer, default=0)
    streak = db.Column(db.Integer, default=0)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    session = db.relationship('QuizBattleSession', backref=db.backref('participants', lazy=True, cascade='all, delete-orphan'))
    user = db.relationship('User', backref=db.backref('battle_participations', lazy=True))

class QuizBattleQuestion(db.Model):
    __tablename__ = 'quiz_battle_questions'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('quiz_battle_sessions.id'), nullable=False)
    order_num = db.Column(db.Integer, default=1)
    question_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(300), nullable=False)
    option_b = db.Column(db.String(300), nullable=False)
    option_c = db.Column(db.String(300), nullable=False)
    option_d = db.Column(db.String(300), nullable=False)
    correct_option = db.Column(db.String(10), nullable=False)  # 'a', 'b', 'c', 'd'

    session = db.relationship('QuizBattleSession', backref=db.backref('questions', lazy=True, cascade='all, delete-orphan'))

class QuizBattleSubmission(db.Model):
    __tablename__ = 'quiz_battle_submissions'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('quiz_battle_sessions.id'), nullable=False)
    question_order = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    selected_option = db.Column(db.String(10), nullable=True)
    is_correct = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    session = db.relationship('QuizBattleSession', backref=db.backref('submissions', lazy=True, cascade='all, delete-orphan'))

class AttendanceSession(db.Model):
    __tablename__ = 'attendance_sessions'
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    instructor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), default='Daily Lecture Attendance')
    session_date = db.Column(db.Date, default=datetime.utcnow().date)
    pin_code = db.Column(db.String(10), nullable=True)  # E.g. '849201' for 6-digit live check-in PIN
    status = db.Column(db.String(20), default='open')  # 'open', 'closed'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    course = db.relationship('Course', backref=db.backref('attendance_sessions', lazy=True, cascade='all, delete-orphan'))
    instructor = db.relationship('User', backref=db.backref('created_attendance_sessions', cascade='all, delete-orphan', lazy=True))

class AttendanceRecord(db.Model):
    __tablename__ = 'attendance_records'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('attendance_sessions.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='present')  # 'present', 'late', 'absent', 'excused'
    marked_at = db.Column(db.DateTime, default=datetime.utcnow)
    method = db.Column(db.String(30), default='self_checkin')  # 'self_checkin', 'pin_verify', 'instructor_marked'

    session = db.relationship('AttendanceSession', backref=db.backref('records', lazy=True, cascade='all, delete-orphan'))
    user = db.relationship('User', backref=db.backref('attendance_records', lazy=True, cascade='all, delete-orphan'))

class CourseSchedule(db.Model):
    __tablename__ = 'course_schedules'
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    instructor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    days_of_week = db.Column(db.String(200), nullable=False, default='Monday, Wednesday, Friday')
    start_time = db.Column(db.String(50), nullable=False, default='10:00 AM')
    end_time = db.Column(db.String(50), nullable=False, default='11:30 AM')
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    total_classes = db.Column(db.Integer, default=0)
    completed_classes = db.Column(db.Integer, default=0)
    room_or_link = db.Column(db.String(300), nullable=True)
    status = db.Column(db.String(30), default='pending_approval')  # 'pending_approval', 'approved', 'rejected'
    rejection_reason = db.Column(db.Text, nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    course = db.relationship('Course', backref=db.backref('schedules', lazy=True, cascade='all, delete-orphan'))
    instructor = db.relationship('User', foreign_keys=[instructor_id], backref=db.backref('taught_schedules', cascade='all, delete-orphan', lazy=True))
    creator = db.relationship('User', foreign_keys=[created_by_id])

    @staticmethod
    def calculate_total_classes(start_date_obj, end_date_obj, days_str):
        if not start_date_obj or not end_date_obj or not days_str:
            return 0
        from datetime import timedelta
        target_days = [d.strip().lower() for d in days_str.split(',') if d.strip()]
        day_map = {'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6}
        target_indices = [day_map[d] for d in target_days if d in day_map]
        if not target_indices:
            return 0
        
        curr = start_date_obj
        count = 0
        while curr <= end_date_obj:
            if curr.weekday() in target_indices:
                count += 1
            curr += timedelta(days=1)
        return count

class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    event_type = db.Column(db.String(50), default='workshop')  # 'workshop', 'seminar', 'exam', 'holiday', 'guest_lecture', 'other'
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    event_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.String(50), nullable=False, default='02:00 PM')
    end_time = db.Column(db.String(50), nullable=False, default='04:00 PM')
    location_or_link = db.Column(db.String(300), nullable=True)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    status = db.Column(db.String(30), default='published')  # 'pending_approval', 'published', 'rejected'
    rejection_reason = db.Column(db.Text, nullable=True)
class TeamMember(db.Model):
    __tablename__ = 'team_members'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    designation = db.Column(db.String(150), nullable=False)
    bio = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    initials = db.Column(db.String(10), nullable=True)
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Campus(db.Model):
    __tablename__ = 'campuses'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    region = db.Column(db.String(150), nullable=True)
    address = db.Column(db.String(500), nullable=False)
    phone = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    description = db.Column(db.Text, nullable=True)
    active_students = db.Column(db.Integer, default=500)
    image_url = db.Column(db.String(500), nullable=True)
    video_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class StudentRegistration(db.Model):
    __tablename__ = 'student_registrations'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    father_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    dob = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    father_phone = db.Column(db.String(50), nullable=True)
    id_number = db.Column(db.String(50), nullable=False)
    father_id_number = db.Column(db.String(50), nullable=True)
    country = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    class_preference = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(50), nullable=False)
    course_name = db.Column(db.String(200), nullable=False)
    campus_name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.Text, nullable=False)
    computer_proficiency = db.Column(db.String(100), nullable=True)
    last_qualification = db.Column(db.String(100), nullable=True)
    heard_from = db.Column(db.String(100), nullable=True)
    has_laptop = db.Column(db.String(10), default='Yes')
    avatar_url = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(30), default='pending')  # 'pending', 'approved', 'rejected'
    access_code_used = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Testimonial(db.Model):
    __tablename__ = 'testimonials'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False, default='Student')
    rating = db.Column(db.Integer, default=5)
    content = db.Column(db.Text, nullable=False)
    avatar_url = db.Column(db.Text, nullable=True)
    is_approved = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User')


class PasswordResetRequest(db.Model):
    __tablename__ = 'password_reset_requests'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    new_password_hash = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default='pending') # 'pending', 'approved', 'rejected'
    reason = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship('User', backref=db.backref('password_reset_requests', lazy=True))


class CourseKey(db.Model):
    __tablename__ = 'course_keys'
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    key_code = db.Column(db.String(100), unique=True, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    used_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    used_at = db.Column(db.DateTime, nullable=True)
    
    course = db.relationship('Course', backref=db.backref('keys', cascade='all, delete-orphan', lazy=True))
    used_by = db.relationship('User', backref='redeemed_keys')


class LeaveApplication(db.Model):
    __tablename__ = 'leave_applications'
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=True)
    leave_type = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), default='Approved')  # 'Approved', 'Pending', 'Rejected'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('leave_applications', lazy=True, cascade='all, delete-orphan'))
    course = db.relationship('Course', backref=db.backref('leave_applications', lazy=True, cascade='all, delete-orphan'))


class CourseResource(db.Model):
    __tablename__ = 'course_resources'
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    uploader_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    resource_type = db.Column(db.String(50), nullable=False)  # 'PDF', 'Code', 'Slide', 'Book', 'Link'
    file_url = db.Column(db.String(500), nullable=True)
    external_url = db.Column(db.String(500), nullable=True)
    file_size = db.Column(db.String(50), nullable=True, default='1.5 MB')
    description = db.Column(db.Text, nullable=True)
    downloads_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    course = db.relationship('Course', backref=db.backref('resources', lazy=True, cascade='all, delete-orphan'))
    uploader = db.relationship('User', backref=db.backref('uploaded_resources', lazy=True))












