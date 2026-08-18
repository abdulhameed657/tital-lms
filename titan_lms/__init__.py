import os
from flask import Flask
from flask_login import LoginManager
from .models import db, User

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

def create_app():
    app = Flask(__name__)
    
    # Configure App
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'titan-lms-super-secret-key-987654')
    
    # DB Configuration: Default to local SQLite db, or /tmp/titan_lms.db on Vercel
    is_vercel = os.environ.get('VERCEL') or os.environ.get('VERCEL_ENV')
    default_db = 'sqlite:////tmp/titan_lms.db' if is_vercel else 'sqlite:///titan_lms.db'
    db_url = os.environ.get('DATABASE_URL', default_db)
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # File upload config
    if is_vercel:
        app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
    else:
        app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
    try:
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    except Exception:
        pass
    
    # Initialize Extensions
    db.init_app(app)
    
    with app.app_context():
        try:
            db.session.execute(db.text("ALTER TABLE users ADD COLUMN phone VARCHAR(50)"))
            db.session.commit()
        except Exception:
            db.session.rollback()

    from flask_migrate import Migrate
    migrate = Migrate(app, db)
    
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Global context processor for notification, message badges, and multi-tenancy tenant context
    @app.before_request
    def detect_tenant():
        from flask import g, request
        from .models import Tenant
        host = request.host.split(':')[0].lower()
        subdomain = None
        if '.' in host and not host.endswith('.localhost') and not host.startswith('127.'):
            parts = host.split('.')
            if len(parts) > 2:
                subdomain = parts[0]
        
        if not subdomain:
            subdomain = request.args.get('tenant')
            
        if subdomain:
            g.tenant = Tenant.query.filter_by(subdomain=subdomain.lower().strip()).first()
        else:
            g.tenant = None

    @app.url_defaults
    def add_tenant(endpoint, values):
        from flask import g
        tenant = getattr(g, 'tenant', None)
        if tenant and 'tenant' not in values:
            values['tenant'] = tenant.subdomain

    @app.context_processor
    def inject_unread_counts():
        from flask_login import current_user
        from flask import g
        from .models import Message, Notification
        tenant = getattr(g, 'tenant', None)
        if current_user.is_authenticated:
            unread_messages = Message.query.filter_by(recipient_id=current_user.id, is_read=False).count()
            notifications_q = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(10).all()
            unread_notifications = sum(1 for n in notifications_q if not n.is_read)
            return dict(
                unread_messages=unread_messages,
                unread_notifications=unread_notifications,
                unread_notifications_list=notifications_q,
                current_tenant=tenant
            )
        return dict(unread_messages=0, unread_notifications=0, unread_notifications_list=[], current_tenant=tenant)
    
    # Register Blueprints
    from .routes.auth import auth_bp
    from .routes.public import public_bp
    from .routes.student import student_bp
    from .routes.instructor import instructor_bp
    from .routes.admin import admin_bp
    from .routes.api import api_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(public_bp, url_prefix='')
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(instructor_bp, url_prefix='/instructor')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    with app.app_context():
        db.create_all()
        
        # Auto-migration helper for SQLite schema updates
        try:
            from sqlalchemy import text
            db.session.execute(text("ALTER TABLE coupons ADD COLUMN status VARCHAR(30) DEFAULT 'approved'"))
            db.session.commit()
        except Exception:
            db.session.rollback()
        try:
            from sqlalchemy import text
            db.session.execute(text("ALTER TABLE users ADD COLUMN referral_code VARCHAR(20)"))
            db.session.commit()
        except Exception:
            db.session.rollback()
        try:
            from sqlalchemy import text
            db.session.execute(text("ALTER TABLE users ADD COLUMN assignment_points INTEGER DEFAULT 0"))
            db.session.commit()
        except Exception:
            db.session.rollback()
        try:
            from sqlalchemy import text
            db.session.execute(text("ALTER TABLE users ADD COLUMN quiz_points INTEGER DEFAULT 0"))
            db.session.commit()
        except Exception:
            db.session.rollback()
        try:
            from sqlalchemy import text
            db.session.execute(text("ALTER TABLE quiz_battle_sessions ADD COLUMN timer_seconds INTEGER DEFAULT 15"))
            db.session.execute(text("ALTER TABLE quiz_battle_sessions ADD COLUMN question_start_time DATETIME"))
            db.session.commit()
        except Exception:
            db.session.rollback()
            
        try:
            from sqlalchemy import text
            db.session.execute(text("ALTER TABLE lessons ADD COLUMN due_date DATETIME"))
            db.session.commit()
        except Exception:
            db.session.rollback()

        try:
            from sqlalchemy import text
            db.session.execute(text("ALTER TABLE courses ADD COLUMN access_code VARCHAR(50)"))
            db.session.commit()
        except Exception:
            db.session.rollback()

        try:
            from sqlalchemy import text
            db.session.execute(text("ALTER TABLE courses ADD COLUMN student_limit INTEGER DEFAULT 100"))
            db.session.commit()
        except Exception:
            db.session.rollback()

        try:
            from sqlalchemy import text
            db.session.execute(text("ALTER TABLE enrollments ADD COLUMN phone_number VARCHAR(30)"))
            db.session.commit()
        except Exception:
            db.session.rollback()

        try:
            from sqlalchemy import text
            db.session.execute(text("ALTER TABLE enrollments ADD COLUMN campus VARCHAR(100)"))
            db.session.commit()
        except Exception:
            db.session.rollback()

        try:
            from sqlalchemy import text
            db.session.execute(text("ALTER TABLE enrollments ADD COLUMN access_key_used VARCHAR(100)"))
            db.session.commit()
        except Exception:
            db.session.rollback()

        try:
            from sqlalchemy import text
            db.session.execute(text("ALTER TABLE student_registrations ADD COLUMN access_code_used VARCHAR(100)"))
            db.session.commit()
        except Exception:
            db.session.rollback()

        # Tenant schema updates
        try:
            from sqlalchemy import text
            db.session.execute(text("ALTER TABLE users ADD COLUMN tenant_id INTEGER REFERENCES tenants(id)"))
            db.session.commit()
        except Exception:
            db.session.rollback()
        try:
            from sqlalchemy import text
            db.session.execute(text("ALTER TABLE courses ADD COLUMN tenant_id INTEGER REFERENCES tenants(id)"))
            db.session.commit()
        except Exception:
            db.session.rollback()
        try:
            from sqlalchemy import text
            db.session.execute(text("ALTER TABLE webinars ADD COLUMN tenant_id INTEGER REFERENCES tenants(id)"))
            db.session.commit()
        except Exception:
            db.session.rollback()
            
        try:
            from sqlalchemy import text
            for table in ['badges', 'reward_items', 'forum_threads', 'moderation_items', 'quiz_battle_sessions', 'attendance_sessions', 'course_schedules', 'events']:
                try:
                    db.session.execute(text(f"ALTER TABLE {table} ADD COLUMN tenant_id INTEGER REFERENCES tenants(id)"))
                    db.session.commit()
                except Exception:
                    db.session.rollback()
        except Exception:
            pass
            
        # Auto-create Super Admin if not exists
        superadmin = User.query.filter_by(email='superadmin@gmail.com').first()
        if not superadmin:
            superadmin = User(
                name='Super Admin',
                email='superadmin@gmail.com',
                role='superadmin',
                verified=True,
                bio='Platform Super Administrator'
            )
            superadmin.set_password('adminsuper123')
            db.session.add(superadmin)
            db.session.commit()
            print('✅ Super Admin created: superadmin@gmail.com / adminsuper123')
        elif superadmin.role != 'superadmin':
            superadmin.role = 'superadmin'
            db.session.commit()
            print('✅ Super Admin role updated to superadmin')


        try:
            from sqlalchemy import text
            db.session.execute(text("ALTER TABLE quiz_battle_submissions ADD COLUMN selected_option VARCHAR(10)"))
            db.session.execute(text("ALTER TABLE quiz_battle_submissions ADD COLUMN is_correct BOOLEAN DEFAULT 0"))
            db.session.commit()
        except Exception:
            db.session.rollback()
        try:
            from sqlalchemy import text
            db.session.execute(text("ALTER TABLE webinars ADD COLUMN status VARCHAR(20) DEFAULT 'scheduled'"))
            db.session.commit()
        except Exception:
            db.session.rollback()
        try:
            from sqlalchemy import text
            db.session.execute(text("ALTER TABLE enrollments ADD COLUMN payment_status VARCHAR(20) DEFAULT 'PAID'"))
            db.session.commit()
        except Exception:
            db.session.rollback()
        try:
            from sqlalchemy import text
            db.session.execute(text("ALTER TABLE users ADD COLUMN roll_number VARCHAR(30)"))
            db.session.commit()
        except Exception:
            db.session.rollback()
        try:
            from sqlalchemy import text
            db.session.execute(text("ALTER TABLE enrollments ADD COLUMN roll_number VARCHAR(30)"))
            db.session.commit()
        except Exception:
            db.session.rollback()
        
    return app
