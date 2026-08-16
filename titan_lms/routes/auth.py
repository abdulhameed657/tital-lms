from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from ..models import db, User, AuditLog
from werkzeug.security import generate_password_hash
import uuid
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

import os

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect_role_dashboard(current_user.role)
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            # Create a failed audit log
            failed_log = AuditLog(
                user_id=user.id if user else None,
                action=f"Failed login attempt for email: {email}",
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string
            )
            db.session.add(failed_log)
            db.session.commit()
            
            flash('Invalid email or password.', 'error')
            return redirect(url_for('auth.login'))
            
        if not user.verified:
            flash('Please verify your academic email before logging in.', 'warning')
            return redirect(url_for('auth.login'))
            
        # Role constraint check (Admin and Superadmin can log in via any selection)
        selected_role = request.form.get('role', 'student')
        if user.role not in ['admin', 'superadmin']:
            if selected_role == 'instructor' and user.role != 'instructor':
                flash('Access denied: Your account is registered as a Student. Please select the Student role to sign in.', 'error')
                return redirect(url_for('auth.login'))
            elif selected_role == 'student' and user.role != 'student':
                flash('Access denied: Your account is registered as an Instructor. Please select the Instructor role to sign in.', 'error')
                return redirect(url_for('auth.login'))

        login_user(user, remember=remember)
        
        # Log successful audit
        success_log = AuditLog(
            user_id=user.id,
            action="Successful login",
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        db.session.add(success_log)
        db.session.commit()
        
        return redirect_role_dashboard(user.role)
        
    from ..models import Tenant
    tenants = Tenant.query.filter_by(active=True).all()
    selected_tenant_subdomain = request.args.get('tenant', '')
    return render_template('auth/login_signup.html', tenants=tenants, selected_tenant_subdomain=selected_tenant_subdomain)

@auth_bp.route('/google-login')
def google_login():
    from flask import g
    # Authenticate via Google mock
    tenant_id = g.tenant.id if getattr(g, 'tenant', None) else None
    
    email = "student1@titan.edu" if not tenant_id else f"student_{tenant_id}@titan.edu"
    
    user = User.query.filter_by(email=email).first()
    
    if not user:
        # Create a mock student for this tenant
        user = User(
            name="Google Student",
            email=email,
            role="student",
            verified=True,
            bio="Logged in via Google.",
            tenant_id=tenant_id
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

    login_user(user)
    # Log successful audit
    success_log = AuditLog(
        user_id=user.id,
        action=f"Successful Google login ({user.name})",
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    db.session.add(success_log)
    db.session.commit()
    flash("Successfully logged in via Google!", "success")
    return redirect(url_for('student.dashboard'))

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'student') # student, instructor, admin
        
        if role == 'student':
            flash('⚠️ Students must apply via the Admission Enrollment Form.', 'error')
            return redirect(url_for('public.enroll'))
            
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email address already registered.', 'error')
            return redirect(url_for('auth.login'))
            
        verification_token = str(uuid.uuid4())
        
        tenant_id = request.form.get('tenant_id')
        if tenant_id and tenant_id.strip() == "":
            tenant_id = None
        
        phone = request.form.get('phone', '').strip()
        
        # In a real app, send an email. For this LMS, we'll auto-verify students, or keep Michael Novak unverified
        new_user = User(
            name=name,
            email=email,
            role=role,
            phone=phone,
            avatar_url="https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150", # default avatar
            bio="New Faculty Member." if role == "instructor" else "New Titan learner.",
            verified=True,  # Auto-verify signups so the demo works smoothly immediately
            verification_token=verification_token,
            tenant_id=tenant_id
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        
        # If student, trigger a default notification
        if role == 'student':
            from ..models import Notification
            notif = Notification(
                user_id=new_user.id,
                title="Welcome to Titan LMS!",
                content="Explore courses and complete quizzes to earn certificates and badges.",
                type="info"
            )
            # Add to session after user gets ID
            db.session.commit()
            notif.user_id = new_user.id
            db.session.add(notif)
            
        db.session.commit()
        
        # Log audit
        signup_log = AuditLog(
            user_id=new_user.id,
            action=f"User signed up as {role}",
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        db.session.add(signup_log)
        db.session.commit()
        
        flash('Account created successfully! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
        
    return redirect(url_for('auth.login'))

@auth_bp.route('/secure-access', methods=['GET', 'POST'])
def secure_access():
    if request.method == 'POST':
        # Handles alternate auth gateway
        return login()
    return render_template('auth/secure_access.html')

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    from ..models import PasswordResetRequest
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        new_password = request.form.get('new_password', '').strip()

        user = User.query.filter_by(email=email).first()
        if not user:
            flash('No registered user account was found with this email address.', 'error')
            return redirect(url_for('auth.forgot_password'))

        if new_password:
            # Check if there is already a pending request for this user
            existing_pending = PasswordResetRequest.query.filter_by(user_id=user.id, status='pending').first()
            if existing_pending:
                existing_pending.new_password_hash = generate_password_hash(new_password)
                existing_pending.created_at = datetime.utcnow()
            else:
                new_reset_req = PasswordResetRequest(
                    user_id=user.id,
                    new_password_hash=generate_password_hash(new_password),
                    status='pending'
                )
                db.session.add(new_reset_req)
            
            db.session.commit()

            audit = AuditLog(
                user_id=user.id,
                action="Password reset request submitted for Admin Approval",
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string
            )
            db.session.add(audit)
            db.session.commit()
            
            flash('⏳ Your password reset request has been submitted to Admin! Once approved by Admin, your password will be updated.', 'info')
            return redirect(url_for('auth.login'))

        return render_template('auth/forgot_password.html', reset_user=user)

    return render_template('auth/forgot_password.html')

@auth_bp.route('/verify/<token>')
def verify_email(token):
    user = User.query.filter_by(verification_token=token).first()
    if not user:
        flash('Invalid or expired verification token.', 'error')
        return redirect(url_for('auth.login'))
        
    user.verified = True
    user.verification_token = None
    db.session.commit()
    
    # Audit log
    audit = AuditLog(
        user_id=user.id,
        action="Email verified via token",
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    db.session.add(audit)
    db.session.commit()
    
    flash('Your academic email has been verified! You can now log in.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
@login_required
def logout():
    logout_log = AuditLog(
        user_id=current_user.id,
        action="User logged out",
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    db.session.add(logout_log)
    db.session.commit()
    
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('public.home'))

def redirect_role_dashboard(role):
    if role == 'superadmin':
        return redirect(url_for('admin.ai_assistant'))
    elif role == 'admin':
        return redirect(url_for('admin.dashboard'))
    elif role == 'instructor':
        return redirect(url_for('instructor.dashboard'))
    else:
        return redirect(url_for('student.dashboard'))
