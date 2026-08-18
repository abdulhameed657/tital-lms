import os
from flask import Flask
from flask_login import LoginManager
from .models import db, User

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

import jinja2

def find_template_dirs():
    package_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(package_dir)
    return [
        os.path.join(package_dir, 'templates'),
        os.path.join(root_dir, 'titan_lms', 'templates'),
        os.path.join(root_dir, 'templates'),
        os.path.join(os.getcwd(), 'titan_lms', 'templates'),
        os.path.join(os.getcwd(), 'templates')
    ]

def create_app():
    package_dir = os.path.dirname(os.path.abspath(__file__))
    template_dir = os.path.join(package_dir, 'templates')
    static_dir = os.path.join(package_dir, 'static')
    
    app = Flask('titan_lms', root_path=package_dir, template_folder=template_dir, static_folder=static_dir)
    
    search_paths = find_template_dirs()
    if search_paths:
        app.jinja_env.loader = jinja2.FileSystemLoader(search_paths)
    
    # Configure App
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'titan-lms-super-secret-key-987654')
    
    # DB Configuration: Default to local SQLite db, or /tmp/titan_lms.db on Vercel
    is_vercel = os.environ.get('VERCEL') or os.environ.get('VERCEL_ENV')
    raw_db_url = os.environ.get('POSTGRES_URL') or os.environ.get('POSTGRES_URL_NON_POOLING') or os.environ.get('STORAGE_URL') or os.environ.get('DATABASE_URL')
    if not raw_db_url or not str(raw_db_url).strip():
        db_url = 'sqlite:////tmp/titan_lms.db' if is_vercel else 'sqlite:///titan_lms.db'
    else:
        db_url = str(raw_db_url).strip()
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
            
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 86400  # Cache static assets in browser for 24 hours
    
    if 'postgresql' in db_url:
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_size': 5,
            'max_overflow': 2,
            'pool_recycle': 300,
            'pool_pre_ping': True,
        }
    
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

    from flask_migrate import Migrate
    migrate = Migrate(app, db)
    
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        try:
            return User.query.get(int(user_id))
        except Exception:
            return None
    
    # Global context processor for notification, message badges, and multi-tenancy tenant context
    @app.before_request
    def detect_tenant():
        from flask import g, request
        from .models import Tenant
        try:
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
        except Exception:
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
        try:
            tenant = getattr(g, 'tenant', None)
            if current_user and current_user.is_authenticated:
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
        except Exception:
            return dict(unread_messages=0, unread_notifications=0, unread_notifications_list=[], current_tenant=None)
    
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
    
    try:
        with app.app_context():
            db.create_all()
            
            # Fast schema migrations executed in a single lightweight batch
            all_migration_stmts = [
                "ALTER TABLE users ADD COLUMN phone VARCHAR(50)",
                "ALTER TABLE users ADD COLUMN bio TEXT",
                "ALTER TABLE users ALTER COLUMN avatar_url TYPE TEXT",
                "ALTER TABLE student_registrations ALTER COLUMN avatar_url TYPE TEXT",
                "ALTER TABLE testimonials ALTER COLUMN avatar_url TYPE TEXT",
                "ALTER TABLE coupons ADD COLUMN status VARCHAR(30) DEFAULT 'approved'",
                "ALTER TABLE users ADD COLUMN referral_code VARCHAR(20)",
                "ALTER TABLE users ADD COLUMN assignment_points INTEGER DEFAULT 0",
                "ALTER TABLE users ADD COLUMN quiz_points INTEGER DEFAULT 0",
                "ALTER TABLE quiz_battle_sessions ADD COLUMN timer_seconds INTEGER DEFAULT 15",
                "ALTER TABLE quiz_battle_sessions ADD COLUMN question_start_time TIMESTAMP",
                "ALTER TABLE lessons ADD COLUMN due_date TIMESTAMP",
                "ALTER TABLE courses ADD COLUMN access_code VARCHAR(50)",
                "ALTER TABLE courses ADD COLUMN student_limit INTEGER DEFAULT 100",
                "ALTER TABLE enrollments ADD COLUMN phone_number VARCHAR(30)",
                "ALTER TABLE enrollments ADD COLUMN campus VARCHAR(100)",
                "ALTER TABLE enrollments ADD COLUMN access_key_used VARCHAR(100)",
                "ALTER TABLE student_registrations ADD COLUMN access_code_used VARCHAR(100)",
                "ALTER TABLE users ADD COLUMN tenant_id INTEGER REFERENCES tenants(id)",
                "ALTER TABLE courses ADD COLUMN tenant_id INTEGER REFERENCES tenants(id)",
                "ALTER TABLE webinars ADD COLUMN tenant_id INTEGER REFERENCES tenants(id)",
                "ALTER TABLE badges ADD COLUMN tenant_id INTEGER REFERENCES tenants(id)",
                "ALTER TABLE reward_items ADD COLUMN tenant_id INTEGER REFERENCES tenants(id)",
                "ALTER TABLE forum_threads ADD COLUMN tenant_id INTEGER REFERENCES tenants(id)",
                "ALTER TABLE moderation_items ADD COLUMN tenant_id INTEGER REFERENCES tenants(id)",
                "ALTER TABLE quiz_battle_sessions ADD COLUMN tenant_id INTEGER REFERENCES tenants(id)",
                "ALTER TABLE attendance_sessions ADD COLUMN tenant_id INTEGER REFERENCES tenants(id)",
                "ALTER TABLE course_schedules ADD COLUMN tenant_id INTEGER REFERENCES tenants(id)",
                "ALTER TABLE events ADD COLUMN tenant_id INTEGER REFERENCES tenants(id)",
                "ALTER TABLE quiz_battle_submissions ADD COLUMN selected_option VARCHAR(10)",
                "ALTER TABLE quiz_battle_submissions ADD COLUMN is_correct BOOLEAN DEFAULT FALSE",
                "ALTER TABLE webinars ADD COLUMN status VARCHAR(20) DEFAULT 'scheduled'",
                "ALTER TABLE enrollments ADD COLUMN payment_status VARCHAR(20) DEFAULT 'PAID'",
                "ALTER TABLE users ADD COLUMN roll_number VARCHAR(30)",
                "ALTER TABLE enrollments ADD COLUMN roll_number VARCHAR(30)"
            ]
            
            from sqlalchemy import text
            for stmt in all_migration_stmts:
                try:
                    db.session.execute(text(stmt))
                except Exception:
                    pass
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
                
            # Ensure Super Admin exists
            try:
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
                elif superadmin.role != 'superadmin':
                    superadmin.role = 'superadmin'
                    db.session.commit()
            except Exception:
                db.session.rollback()
    except Exception as err:
        print(f"Database init warning: {err}")
        
    return app
