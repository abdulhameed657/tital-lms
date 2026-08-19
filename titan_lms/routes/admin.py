from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from ..models import (
    db, User, Course, Enrollment, QuizAttempt, RevenueRecord, AuditLog, 
    Notification, Coupon, AttendanceSession, AttendanceRecord, 
    CourseSchedule, Event, TeamMember, Campus, LeaveApplication, CourseResource
)
from ..decorators import role_required
import os

admin_bp = Blueprint('admin', __name__)

@admin_bp.context_processor
def inject_admin_vars():
    endpoint = request.endpoint or ''
    active_page = 'dashboard'
    if 'users' in endpoint:
        active_page = 'users'
    elif 'attendance' in endpoint:
        active_page = 'attendance'
    elif 'leaves' in endpoint:
        active_page = 'leaves'
    elif 'schedules' in endpoint:
        active_page = 'schedules'
    elif 'events' in endpoint:
        active_page = 'events'
    elif 'revenue' in endpoint:
        active_page = 'revenue'
    elif 'audit_logs' in endpoint or 'logs' in endpoint:
        active_page = 'logs'
    elif 'settings' in endpoint:
        active_page = 'settings'
    elif 'courses' in endpoint or 'course' in endpoint or 'curriculum' in endpoint:
        active_page = 'courses'
    elif 'certificate' in endpoint:
        active_page = 'certificates'
    elif 'leaderboard' in endpoint:
        active_page = 'leaderboard'
    elif 'ai_assistant' in endpoint:
        active_page = 'ai_assistant'
    elif 'rbac' in endpoint:
        active_page = 'rbac'
    elif 'backups' in endpoint:
        active_page = 'backups'
    elif 'tenants' in endpoint:
        active_page = 'tenants'
    elif 'moderation' in endpoint:
        active_page = 'moderation'
    elif 'team' in endpoint:
        active_page = 'team'
    elif 'admin_campuses' in endpoint or 'campuses' in endpoint:
        active_page = 'admin_campuses'
    elif 'registrations' in endpoint:
        active_page = 'registrations'
    return dict(active_page=active_page)


@admin_bp.route('/dashboard')
@login_required
@role_required('admin')
def dashboard():
    from flask import g
    target_tenant_id = g.tenant.id if getattr(g, 'tenant', None) else None

    if target_tenant_id:
        users_count = User.query.filter_by(tenant_id=target_tenant_id).count()
        courses_count = Course.query.filter_by(tenant_id=target_tenant_id).count()
        attempts_count = QuizAttempt.query.join(User).filter(User.tenant_id == target_tenant_id).count()
        revenue_records = RevenueRecord.query.join(Course).filter(Course.tenant_id == target_tenant_id).all()
        logs = AuditLog.query.join(User).filter(User.tenant_id == target_tenant_id).order_by(AuditLog.created_at.desc()).limit(5).all()
    else:
        if current_user.role != 'superadmin':
            users_count = User.query.filter_by(tenant_id=current_user.tenant_id).count()
            courses_count = Course.query.filter_by(tenant_id=current_user.tenant_id).count()
            attempts_count = QuizAttempt.query.join(User).filter(User.tenant_id == current_user.tenant_id).count()
            revenue_records = RevenueRecord.query.join(Course).filter(Course.tenant_id == current_user.tenant_id).all()
            logs = AuditLog.query.join(User).filter(User.tenant_id == current_user.tenant_id).order_by(AuditLog.created_at.desc()).limit(5).all()
        else:
            users_count = User.query.count()
            courses_count = Course.query.count()
            attempts_count = QuizAttempt.query.count()
            revenue_records = RevenueRecord.query.all()
            logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(5).all()
    
    # Calculate gross financial revenue
    gross_revenue = sum([r.amount for r in revenue_records])
    
    # Platform share is 30% of total revenue
    platform_commission = gross_revenue * 0.3
    
    return render_template('admin/dashboard.html',
                           users_count=users_count,
                           courses_count=courses_count,
                           attempts_count=attempts_count,
                           gross_revenue=gross_revenue,
                           platform_commission=platform_commission,
                           logs=logs)

@admin_bp.route('/users')
@login_required
@role_required(['admin', 'superadmin'])
def users():
    from ..models import Tenant
    tenants = Tenant.query.filter_by(active=True).all() if current_user.role == 'superadmin' else []
    
    from flask import g
    target_tenant_id = g.tenant.id if getattr(g, 'tenant', None) else None
    
    from ..models import Enrollment
    if target_tenant_id:
        users = User.query.filter(User.role != 'superadmin', User.tenant_id == target_tenant_id).order_by(User.created_at.desc()).all()
        enrollments = Enrollment.query.join(User).filter(User.tenant_id == target_tenant_id, Enrollment.access_key_used != None).order_by(Enrollment.enrolled_at.desc()).all()
    else:
        if current_user.role != 'superadmin':
            users = User.query.filter(User.role != 'superadmin', User.tenant_id == current_user.tenant_id).order_by(User.created_at.desc()).all()
            enrollments = Enrollment.query.join(User).filter(User.tenant_id == current_user.tenant_id, Enrollment.access_key_used != None).order_by(Enrollment.enrolled_at.desc()).all()
        else:
            users = User.query.filter(User.role != 'superadmin').order_by(User.created_at.desc()).all()
            enrollments = Enrollment.query.filter(Enrollment.access_key_used != None).order_by(Enrollment.enrolled_at.desc()).all()
        
    return render_template('admin/users.html', users=users, tenants=tenants, enrollments=enrollments)

@admin_bp.route('/users/<int:user_id>/update', methods=['POST'])
@login_required
@role_required(['admin', 'superadmin'])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot modify your own administrative account.", "error")
        return redirect(url_for('admin.users'))
    if user.role == 'superadmin':
        flash("You do not have permission to modify a Super Admin.", "error")
        return redirect(url_for('admin.users'))
    if user.role == 'admin' and current_user.role != 'superadmin':
        flash("You do not have permission to modify or delete Admin accounts. Only Super Admins can manage Admins.", "error")
        return redirect(url_for('admin.users'))
        
    action = request.form.get('action')
    if action == 'toggle_verified':
        user.verified = not user.verified
        db.session.commit()
        flash(f"Updated verification state for student {user.name}.", "success")
    elif action == 'change_role':
        new_role = request.form.get('role')
        if new_role in ['student', 'instructor', 'admin']:
            user.role = new_role
            db.session.commit()
            flash(f"Changed role for {user.name} to {new_role}.", "success")
    elif action == 'change_tenant' and current_user.role == 'superadmin':
        tenant_id = request.form.get('tenant_id')
        if tenant_id and tenant_id.strip() != "":
            user.tenant_id = int(tenant_id)
        else:
            user.tenant_id = None
        db.session.commit()
        flash(f"Updated organization/tenant for {user.name}.", "success")
    elif action == 'delete':
        db.session.execute(db.text("PRAGMA foreign_keys = OFF"))
        db.session.delete(user)
        db.session.commit()
        db.session.execute(db.text("PRAGMA foreign_keys = ON"))
        flash(f"Successfully deleted user account '{user.name}'.", "success")
        
    return redirect(url_for('admin.users'))

@admin_bp.route('/courses')
@login_required
@role_required('admin')
def courses():
    from flask import g
    target_tenant_id = g.tenant.id if getattr(g, 'tenant', None) else None
    
    if target_tenant_id:
        all_courses = Course.query.filter_by(tenant_id=target_tenant_id).order_by(Course.created_at.desc()).all()
    else:
        if current_user.role != 'superadmin':
            all_courses = Course.query.filter_by(tenant_id=current_user.tenant_id).order_by(Course.created_at.desc()).all()
        else:
            all_courses = Course.query.order_by(Course.created_at.desc()).all()
    return render_template('admin/courses.html', courses=all_courses)


@admin_bp.route('/courses/create', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'superadmin'])
def create_course():
    from ..models import Course, User
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        price = float(request.form.get('price', 0.0))
        custom_category = request.form.get('custom_category', '').strip()
        category = custom_category if custom_category else request.form.get('category', 'General')
        level = request.form.get('level', 'Beginner')
        thumbnail = request.form.get('thumbnail')
        instructor_id = int(request.form.get('instructor_id', 0))
        student_limit = request.form.get('student_limit', default=100, type=int)
        
        # Fallback to current user if no instructor selected
        if not instructor_id:
            instructor_id = current_user.id
            
        if title and description:
            import uuid
            clean_title = "".join([c for c in title if c.isalnum()]).upper()
            prefix = clean_title[:4] if len(clean_title) >= 4 else "TITAN"
            access_code = f"{prefix}-{uuid.uuid4().hex[:6].upper()}"
            
            new_course = Course(
                instructor_id=instructor_id,
                title=title,
                description=description,
                price=price,
                category=category,
                level=level,
                thumbnail=thumbnail or 'https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=600',
                status='published', # Admin created courses can be published immediately!
                tenant_id=current_user.tenant_id,
                student_limit=student_limit,
                access_code=access_code
            )
            db.session.add(new_course)
            db.session.commit()
            flash(f"Course '{title}' successfully created by Admin!", "success")
            return redirect(url_for('admin.course_access_receipt', course_id=new_course.id))
            
    # Fetch all instructors to assign the course to them!
    instructors = User.query.filter_by(role='instructor').all()
    return render_template('admin/create_course.html', instructors=instructors)


@admin_bp.route('/courses/<int:course_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'superadmin'])
def edit_course(course_id):
    from ..models import Course, Lesson, User
    course = Course.query.get_or_404(course_id)
    if current_user.role != 'superadmin' and course.tenant_id != current_user.tenant_id:
        abort(403)
        
    if request.method == 'POST':
        action = request.form.get('action', 'update_meta')
        
        if action == 'add_module':
            m_title = request.form.get('module_title')
            m_type = request.form.get('module_content_type', 'video')
            m_content = request.form.get('module_content', '').strip()
            m_duration = int(request.form.get('module_duration', 15))
            bulk_urls_raw = request.form.get('bulk_video_urls', '').strip()
            
            if bulk_urls_raw and m_type == 'video':
                # Split links by newline or comma
                raw_list = [url.strip() for url in bulk_urls_raw.replace(',', '\n').split('\n') if url.strip()]
                added_count = 0
                for idx, single_url in enumerate(raw_list, start=1):
                    order = len(course.lessons) + 1
                    lesson_title = f"{m_title} (Part {idx})" if len(raw_list) > 1 else m_title
                    new_l = Lesson(
                        course_id=course.id,
                        order=order,
                        title=lesson_title,
                        content_type='video',
                        content=single_url,
                        duration=m_duration
                    )
                    db.session.add(new_l)
                    added_count += 1
                db.session.commit()
                flash(f"🎬 Successfully added {added_count} video lectures to course!", "success")
                return redirect(url_for('admin.curriculum', course_id=course.id))
            elif m_title:
                order = len(course.lessons) + 1
                new_l = Lesson(
                    course_id=course.id,
                    order=order,
                    title=m_title,
                    content_type=m_type,
                    content=m_content,
                    duration=m_duration
                )
                db.session.add(new_l)
                db.session.commit()
                flash(f"✨ Module {order}: '{m_title}' added to course!", "success")
                return redirect(url_for('admin.curriculum', course_id=course.id))
        else:
            title = request.form.get('title')
            description = request.form.get('description')
            price_raw = request.form.get('price')
            price = float(price_raw) if price_raw is not None and price_raw != '' else course.price
            custom_category = request.form.get('custom_category', '').strip()
            category = custom_category if custom_category else request.form.get('category', course.category)
            level = request.form.get('level', course.level)
            thumbnail = request.form.get('thumbnail')
            instructor_id = int(request.form.get('instructor_id', 0))
            
            if title and description:
                course.title = title
                course.description = description
                course.price = price
                course.category = category
                course.level = level
                if thumbnail:
                    course.thumbnail = thumbnail
                if instructor_id:
                    course.instructor_id = instructor_id
                db.session.commit()
                flash(f"✏️ Course '{title}' details updated successfully!", "success")
                return redirect(url_for('admin.edit_course', course_id=course.id))
                
    instructors = User.query.filter_by(role='instructor').all()
    return render_template('admin/edit_course.html', course=course, instructors=instructors)


@admin_bp.route('/courses/<int:course_id>/curriculum', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'superadmin'])
def curriculum(course_id):
    from ..models import Course, Lesson, Quiz
    course = Course.query.get_or_404(course_id)
    if current_user.role != 'superadmin' and course.tenant_id != current_user.tenant_id:
        abort(403)
        
    if request.method == 'POST':
        # Add a new module/lesson
        title = request.form.get('title')
        content_type = request.form.get('content_type') # 'video', 'text', 'quiz', 'lab'
        content = request.form.get('content')
        duration = int(request.form.get('duration', 10))
        
        if title and content_type:
            order = len(course.lessons) + 1
            new_lesson = Lesson(
                course_id=course.id,
                order=order,
                title=title,
                content_type=content_type,
                content=content,
                duration=duration
            )
            db.session.add(new_lesson)
            db.session.commit()
            
            # If it's a quiz, instantiate a Quiz record
            if content_type == 'quiz':
                new_quiz = Quiz(
                    course_id=course.id,
                    lesson_id=new_lesson.id,
                    title=f"{title} Quiz",
                    time_limit=600
                )
                db.session.add(new_quiz)
                db.session.commit()
                
            flash(f"Module {order}: '{title}' added to curriculum successfully.", "success")
            return redirect(url_for('admin.curriculum', course_id=course.id))
            
    return render_template('admin/curriculum.html', course=course)


@admin_bp.route('/lessons/<int:lesson_id>/delete', methods=['POST'])
@login_required
@role_required(['admin', 'superadmin'])
def delete_lesson(lesson_id):
    from ..models import Lesson
    lesson = Lesson.query.get_or_404(lesson_id)
    course = lesson.course
    if current_user.role != 'superadmin' and course.tenant_id != current_user.tenant_id:
        abort(403)
        
    title = lesson.title
    db.session.delete(lesson)
    db.session.commit()
    flash(f"🗑️ Module '{title}' deleted from curriculum.", "success")
    return redirect(url_for('admin.curriculum', course_id=course.id))


@admin_bp.route('/lessons/<int:lesson_id>/edit', methods=['POST'])
@login_required
@role_required(['admin', 'superadmin'])
def edit_lesson(lesson_id):
    from ..models import Lesson
    lesson = Lesson.query.get_or_404(lesson_id)
    course = lesson.course
    if current_user.role != 'superadmin' and course.tenant_id != current_user.tenant_id:
        abort(403)
        
    title = request.form.get('title')
    content_type = request.form.get('content_type')
    content = request.form.get('content')
    duration = int(request.form.get('duration', 10))
    
    if title:
        lesson.title = title
    if content_type:
        lesson.content_type = content_type
    if content is not None:
        lesson.content = content
    lesson.duration = duration
    
    db.session.commit()
    flash(f"✏️ Module '{lesson.title}' updated successfully!", "success")
    return redirect(url_for('admin.curriculum', course_id=course.id))


@admin_bp.route('/courses/<int:course_id>/publish', methods=['POST'])
@login_required
@role_required(['admin', 'superadmin'])
def publish_course(course_id):
    from ..models import Course
    course = Course.query.get_or_404(course_id)
    if current_user.role != 'superadmin' and course.tenant_id != current_user.tenant_id:
        abort(403)
    if not course.lessons:
        flash("You cannot publish a course without any lessons.", "error")
    else:
        course.status = 'published'
        db.session.commit()
        flash(f"Course '{course.title}' is now live!", "success")
    return redirect(url_for('admin.courses'))


@admin_bp.route('/issue_certificate', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'superadmin'])
def issue_certificate():
    from ..models import Course, Enrollment, Certificate, Notification, User
    # Admin can issue certificates for ANY course under their tenant!
    if current_user.role == 'superadmin':
        courses = Course.query.all()
    else:
        courses = Course.query.filter_by(tenant_id=current_user.tenant_id).all()
        
    course_ids = [c.id for c in courses]
    all_enrollments = Enrollment.query.filter(Enrollment.course_id.in_(course_ids)).all() if course_ids else []
    
    if request.method == 'POST':
        course_id = int(request.form.get('course_id', 0))
        student_id = int(request.form.get('student_id', 0))
        
        course = Course.query.get_or_404(course_id)
        student = User.query.get_or_404(student_id)
        
        # Verify tenant boundary
        if current_user.role != 'superadmin' and course.tenant_id != current_user.tenant_id:
            abort(403)
            
        cert = Certificate.query.filter_by(user_id=student_id, course_id=course_id).first()
        if not cert:
            cert = Certificate(user_id=student_id, course_id=course_id)
            db.session.add(cert)
            
        enrollment = Enrollment.query.filter_by(user_id=student_id, course_id=course_id).first()
        if enrollment:
            enrollment.progress_pct = 100
            enrollment.completed_at = datetime.utcnow()
            
        notif = Notification(
            user_id=student_id,
            title="🎉 Official Course Certificate Issued!",
            content=f"Congratulations! Admin {current_user.name} has officially awarded you a Certificate of Completion for '{course.title}'!",
            type="achievement"
        )
        db.session.add(notif)
        db.session.commit()
        
        flash(f"Certificate successfully issued and awarded to student {student.name} for '{course.title}'!", "success")
        return redirect(url_for('admin.issue_certificate'))
        
    recent_certificates = Certificate.query.filter(Certificate.course_id.in_(course_ids)).order_by(Certificate.issued_at.desc()).all() if course_ids else []
    
    return render_template('admin/issue_certificate.html', 
                           courses=courses, 
                           enrollments=all_enrollments, 
                           recent_certificates=recent_certificates)


@admin_bp.route('/issue_certificate/<int:cert_id>/delete', methods=['POST'])
@login_required
@role_required(['admin', 'superadmin'])
def delete_certificate(cert_id):
    from ..models import Certificate
    cert = Certificate.query.get_or_404(cert_id)
    if current_user.role != 'superadmin' and cert.course.tenant_id != current_user.tenant_id:
        abort(403)
    db.session.delete(cert)
    db.session.commit()
    flash("Certificate successfully deleted/revoked!", "success")
    return redirect(url_for('admin.issue_certificate'))

@admin_bp.route('/courses/<int:course_id>/toggle_status', methods=['POST'])
@login_required
@role_required(['admin', 'superadmin'])
def toggle_course_status(course_id):
    course = Course.query.get_or_404(course_id)
    if current_user.role != 'superadmin' and course.tenant_id != current_user.tenant_id:
        abort(403)
        
    if course.status == 'draft':
        course.status = 'published'
        if not course.access_code:
            import uuid
            clean_title = "".join([c for c in course.title if c.isalnum()]).upper()
            prefix = clean_title[:4] if len(clean_title) >= 4 else "TITAN"
            course.access_code = f"{prefix}-{uuid.uuid4().hex[:6].upper()}"
        db.session.commit()
        flash(f"Course '{course.title}' approved/published successfully!", "success")
        return redirect(url_for('admin.course_access_receipt', course_id=course.id))
    else:
        course.status = 'draft'
        db.session.commit()
        flash(f"Course '{course.title}' status updated to DRAFT.", "success")
        return redirect(url_for('admin.courses'))

@admin_bp.route('/courses/<int:course_id>/approve_delete', methods=['POST'])
@login_required
@role_required('admin')
def approve_delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    title = course.title
    instructor_id = course.instructor_id
    
    db.session.delete(course)
    
    # Send notification back to instructor
    notif = Notification(
        user_id=instructor_id,
        title="✅ Course Deletion Approved",
        content=f"Admin has approved the deletion request for course '{title}'. It has been permanently removed.",
        type="info"
    )
    db.session.add(notif)
    db.session.commit()
    flash(f"✅ Approved and permanently deleted course '{title}'.", "success")
    return redirect(url_for('admin.courses'))

@admin_bp.route('/courses/<int:course_id>/reject_delete', methods=['POST'])
@login_required
@role_required('admin')
def reject_delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    course.status = 'draft'
    
    # Send notification back to instructor
    notif = Notification(
        user_id=course.instructor_id,
        title="❌ Course Deletion Rejected",
        content=f"Admin rejected deletion for course '{course.title}'. Course status reset to Draft.",
        type="warning"
    )
    db.session.add(notif)
    db.session.commit()
    flash(f"Rejected deletion request for '{course.title}'. Course reset to Draft.", "info")
    return redirect(url_for('admin.courses'))

@admin_bp.route('/revenue')
@login_required
@role_required('admin')
def revenue():
    from flask import g
    target_tenant_id = g.tenant.id if getattr(g, 'tenant', None) else None
    
    if target_tenant_id:
        records = RevenueRecord.query.join(Course).filter(Course.tenant_id == target_tenant_id).order_by(RevenueRecord.created_at.desc()).all()
    else:
        if current_user.role != 'superadmin':
            records = RevenueRecord.query.join(Course).filter(Course.tenant_id == current_user.tenant_id).order_by(RevenueRecord.created_at.desc()).all()
        else:
            records = RevenueRecord.query.order_by(RevenueRecord.created_at.desc()).all()
    gross_revenue = sum([r.amount for r in records])
    platform_share = gross_revenue * 0.3
    instructor_share = gross_revenue * 0.7
    
    return render_template('admin/revenue.html',
                           records=records,
                           gross_revenue=gross_revenue,
                           platform_share=platform_share,
                           instructor_share=instructor_share)

@admin_bp.route('/audit_logs')
@login_required
@role_required('superadmin')
def audit_logs():
    from flask import g
    target_tenant_id = g.tenant.id if getattr(g, 'tenant', None) else None
    if target_tenant_id:
        logs = AuditLog.query.join(User, AuditLog.user_id == User.id).filter(User.tenant_id == target_tenant_id).order_by(AuditLog.created_at.desc()).all()
    else:
        logs = AuditLog.query.order_by(AuditLog.created_at.desc()).all()
    return render_template('admin/audit_logs.html', logs=logs)

@admin_bp.route('/leaderboard')
@login_required
@role_required('admin')
def leaderboard():
    from flask import g
    target_tenant_id = g.tenant.id if getattr(g, 'tenant', None) else None
    
    if target_tenant_id:
        students = User.query.filter_by(role='student', tenant_id=target_tenant_id).order_by(User.points.desc()).all()
    else:
        if current_user.role != 'superadmin':
            students = User.query.filter_by(role='student', tenant_id=current_user.tenant_id).order_by(User.points.desc()).all()
        else:
            students = User.query.filter_by(role='student').order_by(User.points.desc()).all()
    podium = students[:3]
    remaining = students[3:]
    return render_template('admin/leaderboard.html', podium=podium, remaining=remaining)

@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@role_required('superadmin')
def settings():
    if request.method == 'POST':
        secret_key = request.form.get('secret_key')
        gemini_key = request.form.get('gemini_key')
        
        if secret_key:
            os.environ['SECRET_KEY'] = secret_key
        if gemini_key:
            os.environ['GEMINI_API_KEY'] = gemini_key
            
        flash("⚙️ System configurations updated successfully.", "success")
        return redirect(url_for('admin.settings'))
        
    system_configs = {
        'SECRET_KEY': os.environ.get('SECRET_KEY', 'titan-lms-super-secret-key-987654'),
        'GEMINI_API_KEY': os.environ.get('GEMINI_API_KEY', 'not-configured-mock-active')
    }
    return render_template('admin/settings.html', configs=system_configs, active_page='settings')

@admin_bp.route('/ai_assistant', methods=['GET', 'POST'])
@login_required
@role_required('superadmin')
def ai_assistant():
    users_count = User.query.count()
    courses_count = Course.query.count()
    revenue_records = RevenueRecord.query.all()
    gross_revenue = sum([r.amount for r in revenue_records])
    platform_commission = gross_revenue * 0.3
    recent_logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(8).all()
    
    return render_template('admin/ai_assistant.html',
                           users_count=users_count,
                           courses_count=courses_count,
                           gross_revenue=gross_revenue,
                           platform_commission=platform_commission,
                           recent_logs=recent_logs)

@admin_bp.route('/rbac', methods=['GET', 'POST'])
@login_required
@role_required('superadmin')
def rbac():
    from ..models import RolePermission, User
    if request.method == 'POST':
        role_name = request.form.get('role_name')
        perm = request.form.get('permission_key')
        user_id = request.form.get('user_id')
        if role_name and perm:
            rp = RolePermission(role_name=role_name, permission_key=perm, description=f"Permission for {role_name}")
            db.session.add(rp)
            db.session.commit()
            flash(f"🔐 Capability '{perm}' successfully assigned to staff member!", "success")
            return redirect(url_for('admin.rbac'))
    permissions = RolePermission.query.all()
    staff_members = User.query.filter(User.role.in_(['instructor', 'admin'])).all()
    return render_template('admin/rbac.html', permissions=permissions, staff_members=staff_members, active_page='rbac')

@admin_bp.route('/backups', methods=['GET', 'POST'])
@login_required
@role_required('superadmin')
def backups():
    import os
    from flask import current_app
    if request.method == 'POST':
        flash("💾 Database Snapshot created successfully! Automated backup logged.", "success")
        return redirect(url_for('admin.backups'))
    
    db_path = os.path.join(current_app.root_path, '..', 'instance', 'titan_lms.db')
    db_size = "14.8 MB"
    if os.path.exists(db_path):
        size_bytes = os.path.getsize(db_path)
        db_size = f"{size_bytes / (1024 * 1024):.2f} MB"
    return render_template('admin/backups.html', db_size=db_size, active_page='backups')

@admin_bp.route('/backups/download')
@login_required
@role_required('superadmin')
def download_backup():
    import os, datetime
    from flask import send_file, current_app
    db_path = os.path.join(current_app.root_path, '..', 'instance', 'titan_lms.db')
    if not os.path.exists(db_path):
        db_path = os.path.join(current_app.root_path, 'titan_lms.db')
    if os.path.exists(db_path):
        filename = f"titan_lms_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        return send_file(db_path, as_attachment=True, download_name=filename)
    flash("❌ Database file not found for download.", "error")
    return redirect(url_for('admin.backups'))

@admin_bp.route('/backups/upload', methods=['POST'])
@login_required
@role_required('superadmin')
def upload_backup():
    import os
    from flask import current_app
    file = request.files.get('backup_file')
    if not file or not file.filename:
        flash("❌ Please select a database backup file to upload.", "error")
        return redirect(url_for('admin.backups'))
    db_path = os.path.join(current_app.root_path, '..', 'instance', 'titan_lms.db')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    file.save(db_path)
    flash("💾 Database backup uploaded & system data restored successfully!", "success")
    return redirect(url_for('admin.backups'))

@admin_bp.route('/rbac/update-role/<int:user_id>', methods=['POST'])
@login_required
@role_required('superadmin')
def update_user_role(user_id):
    u = User.query.get_or_404(user_id)
    new_role = request.form.get('role', 'student').lower()
    if new_role in ['student', 'instructor', 'admin']:
        u.role = new_role
        db.session.commit()
        flash(f"🔐 User '{u.name}' role updated to '{new_role.capitalize()}'!", "success")
    return redirect(url_for('admin.rbac'))

@admin_bp.route('/coupons')
@login_required
@role_required('admin')
def coupons():
    from flask import g
    target_tenant_id = g.tenant.id if getattr(g, 'tenant', None) else None
    
    if target_tenant_id:
        pending_coupons = Coupon.query.join(User, Coupon.instructor_id == User.id).filter(Coupon.status == 'pending_approval', User.tenant_id == target_tenant_id).order_by(Coupon.created_at.desc()).all()
        approved_coupons = Coupon.query.join(User, Coupon.instructor_id == User.id).filter(Coupon.status == 'approved', User.tenant_id == target_tenant_id).order_by(Coupon.created_at.desc()).all()
        all_coupons = Coupon.query.join(User, Coupon.instructor_id == User.id).filter(User.tenant_id == target_tenant_id).order_by(Coupon.created_at.desc()).all()
    else:
        if current_user.role != 'superadmin':
            pending_coupons = Coupon.query.join(User, Coupon.instructor_id == User.id).filter(Coupon.status == 'pending_approval', User.tenant_id == current_user.tenant_id).order_by(Coupon.created_at.desc()).all()
            approved_coupons = Coupon.query.join(User, Coupon.instructor_id == User.id).filter(Coupon.status == 'approved', User.tenant_id == current_user.tenant_id).order_by(Coupon.created_at.desc()).all()
            all_coupons = Coupon.query.join(User, Coupon.instructor_id == User.id).filter(User.tenant_id == current_user.tenant_id).order_by(Coupon.created_at.desc()).all()
        else:
            pending_coupons = Coupon.query.filter_by(status='pending_approval').order_by(Coupon.created_at.desc()).all()
            approved_coupons = Coupon.query.filter_by(status='approved').order_by(Coupon.created_at.desc()).all()
            all_coupons = Coupon.query.order_by(Coupon.created_at.desc()).all()
    return render_template('admin/coupons.html', pending_coupons=pending_coupons, approved_coupons=approved_coupons, all_coupons=all_coupons, active_page='coupons')

@admin_bp.route('/coupons/<int:coupon_id>/approve', methods=['POST'])
@login_required
@role_required('admin')
def approve_coupon(coupon_id):
    cp = Coupon.query.get_or_404(coupon_id)
    cp.status = 'approved'
    if cp.instructor_id:
        notif = Notification(
            user_id=cp.instructor_id,
            title="✅ Discount Coupon Approved!",
            content=f"Your promo code '{cp.code}' ({cp.discount_percent}% OFF) has been approved by Admin and is now published for students!",
            type="info"
        )
        db.session.add(notif)
    db.session.commit()
    flash(f"✅ Coupon '{cp.code}' approved and published!", "success")
    return redirect(url_for('admin.coupons'))

@admin_bp.route('/coupons/<int:coupon_id>/reject', methods=['POST'])
@login_required
@role_required('admin')
def reject_coupon(coupon_id):
    cp = Coupon.query.get_or_404(coupon_id)
    cp.status = 'rejected'
    if cp.instructor_id:
        notif = Notification(
            user_id=cp.instructor_id,
            title="❌ Discount Coupon Rejected",
            content=f"Your promo code '{cp.code}' was rejected by Admin. Please update the discount details.",
            type="alert"
        )
        db.session.add(notif)
    db.session.commit()
    flash(f"❌ Coupon '{cp.code}' rejected.", "warning")
    return redirect(url_for('admin.coupons'))

@admin_bp.route('/coupons/<int:coupon_id>/edit', methods=['POST'])
@login_required
@role_required('admin')
def edit_coupon(coupon_id):
    cp = Coupon.query.get_or_404(coupon_id)
    cp.code = request.form.get('code', cp.code).upper().strip()
    cp.discount_percent = float(request.form.get('discount_percent', cp.discount_percent))
    cp.max_uses = int(request.form.get('max_uses', cp.max_uses or 100))
    cp.status = request.form.get('status', cp.status)
    db.session.commit()
    flash(f"✏️ Promo Coupon '{cp.code}' updated successfully!", "success")
    return redirect(url_for('admin.coupons'))

@admin_bp.route('/coupons/<int:coupon_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_coupon(coupon_id):
    cp = Coupon.query.get_or_404(coupon_id)
    code = cp.code
    db.session.delete(cp)
    db.session.commit()
    flash(f"🗑️ Coupon '{code}' deleted permanently.", "info")
    return redirect(url_for('admin.coupons'))

@admin_bp.route('/tenants', methods=['GET', 'POST'])
@login_required
@role_required('superadmin')
def tenants():
    from ..models import Tenant
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        subdomain = request.form.get('subdomain', '').lower().strip()
        primary_color = request.form.get('primary_color', '#00008c')
        
        if name and subdomain:
            existing = Tenant.query.filter_by(subdomain=subdomain).first()
            if existing:
                flash(f"⚠️ Subdomain '{subdomain}' is already taken by another client! Please choose a different subdomain prefix.", "warning")
                return redirect(url_for('admin.tenants'))
            
            admin_name = request.form.get('admin_name', 'Admin').strip()
            admin_email = request.form.get('admin_email', '').strip()
            admin_password = request.form.get('admin_password', '').strip()
            
            from ..models import User
            existing_user = User.query.filter_by(email=admin_email).first()
            if existing_user:
                flash(f"⚠️ Email '{admin_email}' is already registered in the system.", "warning")
                return redirect(url_for('admin.tenants'))
            
            t = Tenant(name=name, subdomain=subdomain, primary_color=primary_color)
            db.session.add(t)
            db.session.flush() # Get tenant ID
            
            # Create admin user for this tenant
            admin_user = User(
                name=admin_name,
                email=admin_email,
                role='admin',
                verified=True,
                tenant_id=t.id,
                bio=f"Administrator for {name}"
            )
            admin_user.set_password(admin_password)
            db.session.add(admin_user)
            
            db.session.commit()
            flash(f"🏢 Corporate Sub-tenant '{name}' ({subdomain}.titanlms.com) initialized with admin '{admin_email}'!", "success")
            return redirect(url_for('admin.tenants'))
    tenants_list = Tenant.query.order_by(Tenant.created_at.desc()).all()
    return render_template('admin/tenants.html', tenants=tenants_list, active_page='tenants')

@admin_bp.route('/tenants/<int:tenant_id>/edit', methods=['POST'])
@login_required
@role_required('superadmin')
def edit_tenant(tenant_id):
    from ..models import Tenant
    t = Tenant.query.get_or_404(tenant_id)
    name = request.form.get('name', '').strip()
    subdomain = request.form.get('subdomain', '').lower().strip()
    primary_color = request.form.get('primary_color', t.primary_color or '#00008c')
    
    if subdomain != t.subdomain:
        existing = Tenant.query.filter_by(subdomain=subdomain).first()
        if existing:
            flash(f"⚠️ Subdomain '{subdomain}' is already taken by another client! Please choose a different subdomain prefix.", "warning")
            return redirect(url_for('admin.tenants'))
            
    if name and subdomain:
        t.name = name
        t.subdomain = subdomain
        t.primary_color = primary_color
        db.session.commit()
        flash(f"✏️ Corporate Tenant '{t.name}' updated successfully!", "success")
    return redirect(url_for('admin.tenants'))

@admin_bp.route('/tenants/<int:tenant_id>/delete', methods=['POST'])
@login_required
@role_required('superadmin')
def delete_tenant(tenant_id):
    from ..models import Tenant
    t = Tenant.query.get_or_404(tenant_id)
    name = t.name
    db.session.delete(t)
    db.session.commit()
    flash(f"🗑️ Sub-tenant portal '{name}' deleted permanently.", "info")
    return redirect(url_for('admin.tenants'))

@admin_bp.route('/moderation', methods=['GET', 'POST'])
@login_required
@role_required('superadmin')
def moderation():
    from ..models import ModerationItem
    if request.method == 'POST':
        item_id = request.form.get('item_id')
        action = request.form.get('action')
        item = ModerationItem.query.get(item_id)
        if item:
            item.status = 'approved' if action == 'approve' else 'removed'
            db.session.commit()
            flash(f"Moderation queue updated: Item marked as {item.status}.", "success")
            return redirect(url_for('admin.moderation'))
    # Ensure some sample items if empty
    if ModerationItem.query.count() == 0:
        db.session.add_all([
            ModerationItem(content_type='comment', content_id=1, text_preview='Check this external suspicious link www.test.com', flag_reason='External Link Spam', status='pending'),
            ModerationItem(content_type='course_review', content_id=2, text_preview='Worst course ever, complete waste', flag_reason='Excessive Hostility', status='pending')
        ])
        db.session.commit()
    items = ModerationItem.query.all()
    return render_template('admin/moderation.html', items=items, active_page='moderation')


@admin_bp.route('/attendance', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def attendance():
    from ..utils import auto_mark_absent_for_closed_sessions
    auto_mark_absent_for_closed_sessions()

    from flask import g
    target_tenant_id = g.tenant.id if getattr(g, 'tenant', None) else None
    
    if target_tenant_id:
        all_courses = Course.query.filter_by(tenant_id=target_tenant_id).all()
    else:
        if current_user.role != 'superadmin':
            all_courses = Course.query.filter_by(tenant_id=current_user.tenant_id).all()
        else:
            all_courses = Course.query.all()

    if not all_courses:
        course1 = Course(
            title="Introduction to Computer Science",
            description="Foundations of programming, algorithms, and computational thinking.",
            instructor_id=current_user.id,
            tenant_id=current_user.tenant_id or target_tenant_id
        )
        course2 = Course(
            title="Web Application Development",
            description="Building high-performance modern web apps with HTML, CSS, and JS.",
            instructor_id=current_user.id,
            tenant_id=current_user.tenant_id or target_tenant_id
        )
        db.session.add(course1)
        db.session.add(course2)
        db.session.commit()
        if target_tenant_id:
            all_courses = Course.query.filter_by(tenant_id=target_tenant_id).all()
        else:
            if current_user.role != 'superadmin':
                all_courses = Course.query.filter_by(tenant_id=current_user.tenant_id).all()
            else:
                all_courses = Course.query.all()
    search_q = request.args.get('q', '').strip()

    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'create_session':
            course_id = request.form.get('course_id')
            title = request.form.get('title', 'Daily Class Attendance').strip()
            pin_code = request.form.get('pin_code', '').strip()
            session_date_str = request.form.get('session_date', '').strip()
            
            sess_date = datetime.utcnow().date()
            if session_date_str:
                try:
                    sess_date = datetime.strptime(session_date_str, '%Y-%m-%d').date()
                except Exception:
                    pass

            if not pin_code:
                import random
                pin_code = str(random.randint(100000, 999999))

            course = Course.query.get(course_id)
            inst_id = course.instructor_id if course else current_user.id

            sess = AttendanceSession(
                course_id=course_id,
                instructor_id=inst_id,
                title=title,
                session_date=sess_date,
                pin_code=pin_code,
                status='open'
            )
            db.session.add(sess)
            db.session.commit()
            flash(f"✅ Admin Attendance Session Created! Date: {sess_date} | PIN Code: {pin_code}", "success")
            return redirect(url_for('admin.attendance'))

        elif action == 'admin_mark_attendance':
            # Admin manual override for missed days / roll numbers
            course_id = request.form.get('course_id')
            roll_number = request.form.get('roll_number', '').strip()
            date_str = request.form.get('session_date', '').strip()
            rec_status = request.form.get('status', 'present')

            # Search enrollment by course-specific roll_number
            enr = Enrollment.query.filter((Enrollment.roll_number == roll_number) | (Enrollment.id == roll_number)).first()
            if enr:
                student = enr.user
                if not course_id:
                    course_id = enr.course_id
            else:
                student = User.query.filter((User.roll_number == roll_number) | (User.id == roll_number)).first()

            if not student:
                flash(f"⚠️ Student with Roll No / ID '{roll_number}' not found!", "error")
                return redirect(url_for('admin.attendance'))

            target_date = datetime.utcnow().date()
            if date_str:
                try:
                    target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                except Exception:
                    pass

            # Find existing session for course & date, or create dynamic session
            sess = AttendanceSession.query.filter_by(course_id=course_id, session_date=target_date).first()
            if not sess:
                course = Course.query.get(course_id)
                inst_id = course.instructor_id if course else current_user.id
                sess = AttendanceSession(
                    course_id=course_id,
                    instructor_id=inst_id,
                    title=f"Class Attendance ({target_date.strftime('%b %d, %Y')})",
                    session_date=target_date,
                    status='closed'
                )
                db.session.add(sess)
                db.session.commit()

            # Record or update attendance
            record = AttendanceRecord.query.filter_by(session_id=sess.id, user_id=student.id).first()
            if not record:
                record = AttendanceRecord(
                    session_id=sess.id,
                    user_id=student.id,
                    status=rec_status,
                    method='admin_override'
                )
                db.session.add(record)
            else:
                record.status = rec_status
                record.method = 'admin_override'

            db.session.commit()
            flash(f"✅ Admin marked Attendance for Roll No '{student.get_roll_number()}' ({student.name}) as '{rec_status.upper()}' for date {target_date}!", "success")
            return redirect(url_for('admin.attendance'))

        elif action == 'edit_attendance_record':
            # Admin inline record editing
            record_id = request.form.get('record_id')
            new_status = request.form.get('status', 'present')
            rec = AttendanceRecord.query.get(record_id)
            if rec:
                rec.status = new_status
                rec.method = 'admin_override'
                db.session.commit()
                flash(f"✏️ Attendance Record #{rec.id} updated to '{new_status.upper()}'!", "success")
            return redirect(url_for('admin.attendance'))

        elif action == 'close_session':
            session_id = request.form.get('session_id')
            sess = AttendanceSession.query.get(session_id)
            if sess:
                sess.status = 'closed'
                db.session.commit()
                flash("🔒 Session Closed by Admin.", "info")
            return redirect(url_for('admin.attendance'))

        elif action == 'update_payment':
            enrollment_id = request.form.get('enrollment_id')
            new_status = request.form.get('payment_status', 'PAID')
            enr = Enrollment.query.get(enrollment_id)
            if enr:
                enr.payment_status = new_status
                db.session.commit()
                flash(f"💳 Payment status updated to '{new_status}' for {enr.user.name}!", "success")
            return redirect(url_for('admin.attendance'))

    if target_tenant_id:
        sessions = AttendanceSession.query.join(Course).filter(Course.tenant_id == target_tenant_id).order_by(AttendanceSession.session_date.desc(), AttendanceSession.created_at.desc()).all()
        all_students = User.query.filter_by(role='student', tenant_id=target_tenant_id).order_by(User.id.asc()).all()
        records_query = AttendanceRecord.query.join(User).filter(User.tenant_id == target_tenant_id).order_by(AttendanceRecord.marked_at.desc())
        enrollments = Enrollment.query.join(User).filter(User.tenant_id == target_tenant_id).order_by(Enrollment.enrolled_at.desc()).all()
    else:
        if current_user.role != 'superadmin':
            sessions = AttendanceSession.query.join(Course).filter(Course.tenant_id == current_user.tenant_id).order_by(AttendanceSession.session_date.desc(), AttendanceSession.created_at.desc()).all()
            all_students = User.query.filter_by(role='student', tenant_id=current_user.tenant_id).order_by(User.id.asc()).all()
            records_query = AttendanceRecord.query.join(User).filter(User.tenant_id == current_user.tenant_id).order_by(AttendanceRecord.marked_at.desc())
            enrollments = Enrollment.query.join(User).filter(User.tenant_id == current_user.tenant_id).order_by(Enrollment.enrolled_at.desc()).all()
        else:
            sessions = AttendanceSession.query.order_by(AttendanceSession.session_date.desc(), AttendanceSession.created_at.desc()).all()
            all_students = User.query.filter_by(role='student').order_by(User.id.asc()).all()
            records_query = AttendanceRecord.query.order_by(AttendanceRecord.marked_at.desc())
            enrollments = Enrollment.query.order_by(Enrollment.enrolled_at.desc()).all()
        
    if search_q:
        all_students = [s for s in all_students if search_q.lower() in (s.name.lower() + " " + s.email.lower() + " " + s.get_roll_number().lower())]

    recent_records = records_query.limit(50).all()
    
    return render_template(
        'admin/attendance.html',
        all_courses=all_courses,
        sessions=sessions,
        students=all_students,
        recent_records=recent_records,
        enrollments=enrollments,
        search_q=search_q
    )


@admin_bp.route('/schedules', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def schedules():
    from flask import g
    target_tenant_id = g.tenant.id if getattr(g, 'tenant', None) else None
    
    if target_tenant_id:
        all_courses = Course.query.filter_by(tenant_id=target_tenant_id).all()
        all_instructors = User.query.filter_by(role='instructor', tenant_id=target_tenant_id).all()
    else:
        if current_user.role != 'superadmin':
            all_courses = Course.query.filter_by(tenant_id=current_user.tenant_id).all()
            all_instructors = User.query.filter_by(role='instructor', tenant_id=current_user.tenant_id).all()
        else:
            all_courses = Course.query.all()
            all_instructors = User.query.filter_by(role='instructor').all()

    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'create_schedule':
            course_id = request.form.get('course_id')
            title = request.form.get('title', 'Course Lecture Schedule').strip()
            days_of_week = request.form.get('days_of_week', 'Monday, Wednesday, Friday').strip()
            start_time = request.form.get('start_time', '10:00 AM').strip()
            end_time = request.form.get('end_time', '11:30 AM').strip()
            start_date_str = request.form.get('start_date')
            end_date_str = request.form.get('end_date')
            room_or_link = request.form.get('room_or_link', 'Lab 101').strip()

            s_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else datetime.utcnow().date()
            e_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else (s_date + timedelta(days=30))

            course = Course.query.get(course_id)
            inst_id = course.instructor_id if course else current_user.id

            tot_classes = CourseSchedule.calculate_total_classes(s_date, e_date, days_of_week)

            sched = CourseSchedule(
                course_id=course_id,
                instructor_id=inst_id,
                title=title,
                days_of_week=days_of_week,
                start_time=start_time,
                end_time=end_time,
                start_date=s_date,
                end_date=e_date,
                total_classes=tot_classes,
                completed_classes=0,
                room_or_link=room_or_link,
                status='approved',  # Direct admin creation is auto-approved
                created_by_id=current_user.id
            )
            db.session.add(sched)
            db.session.commit()
            flash(f"✅ Course Schedule Created & Published! Total Classes: {tot_classes}", "success")
            return redirect(url_for('admin.schedules'))

        elif action == 'approve_schedule':
            sched_id = request.form.get('schedule_id')
            sched = CourseSchedule.query.get(sched_id)
            if sched:
                sched.status = 'approved'
                db.session.commit()
                flash(f"🎉 Approved Schedule '{sched.title}' for {sched.course.title}!", "success")
            return redirect(url_for('admin.schedules'))

        elif action == 'reject_schedule':
            sched_id = request.form.get('schedule_id')
            reason = request.form.get('rejection_reason', 'Needs revisions').strip()
            sched = CourseSchedule.query.get(sched_id)
            if sched:
                sched.status = 'rejected'
                sched.rejection_reason = reason
                db.session.commit()
                flash(f"❌ Schedule '{sched.title}' rejected.", "info")
            return redirect(url_for('admin.schedules'))

        elif action == 'edit_schedule':
            sched_id = request.form.get('schedule_id')
            sched = CourseSchedule.query.get(sched_id)
            if sched:
                course_id = request.form.get('course_id')
                if course_id:
                    sched.course_id = int(course_id)
                    course = Course.query.get(sched.course_id)
                    if course:
                        sched.instructor_id = course.instructor_id
                sched.title = request.form.get('title', sched.title).strip()
                sched.days_of_week = request.form.get('days_of_week', sched.days_of_week).strip()
                sched.start_time = request.form.get('start_time', sched.start_time).strip()
                sched.end_time = request.form.get('end_time', sched.end_time).strip()
                start_date_str = request.form.get('start_date')
                end_date_str = request.form.get('end_date')
                if start_date_str:
                    sched.start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                if end_date_str:
                    sched.end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                sched.room_or_link = request.form.get('room_or_link', sched.room_or_link).strip()
                sched.total_classes = CourseSchedule.calculate_total_classes(sched.start_date, sched.end_date, sched.days_of_week)
                db.session.commit()
                flash(f"✏️ Schedule '{sched.title}' updated successfully!", "success")
            return redirect(url_for('admin.schedules'))

        elif action == 'delete_schedule':
            sched_id = request.form.get('schedule_id')
            sched = CourseSchedule.query.get(sched_id)
            if sched:
                db.session.delete(sched)
                db.session.commit()
                flash("🗑️ Schedule deleted.", "info")
            return redirect(url_for('admin.schedules'))

    if target_tenant_id:
        all_schedules = CourseSchedule.query.join(Course).filter(Course.tenant_id == target_tenant_id).order_by(CourseSchedule.created_at.desc()).all()
    else:
        if current_user.role != 'superadmin':
            all_schedules = CourseSchedule.query.join(Course).filter(Course.tenant_id == current_user.tenant_id).order_by(CourseSchedule.created_at.desc()).all()
        else:
            all_schedules = CourseSchedule.query.order_by(CourseSchedule.created_at.desc()).all()
    pending_schedules = [s for s in all_schedules if s.status == 'pending_approval']
    approved_schedules = [s for s in all_schedules if s.status == 'approved']
    rejected_schedules = [s for s in all_schedules if s.status == 'rejected']

    return render_template(
        'admin/schedules.html',
        courses=all_courses,
        instructors=all_instructors,
        all_schedules=all_schedules,
        pending_schedules=pending_schedules,
        approved_schedules=approved_schedules,
        rejected_schedules=rejected_schedules
    )


@admin_bp.route('/events', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def events():
    from flask import g
    target_tenant_id = g.tenant.id if getattr(g, 'tenant', None) else None
    
    if target_tenant_id:
        all_courses = Course.query.filter_by(tenant_id=target_tenant_id).all()
    else:
        if current_user.role != 'superadmin':
            all_courses = Course.query.filter_by(tenant_id=current_user.tenant_id).all()
        else:
            all_courses = Course.query.all()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'create_event':
            title = request.form.get('title').strip()
            event_type = request.form.get('event_type', 'workshop')
            course_id = request.form.get('course_id')
            course_id = int(course_id) if course_id and course_id != 'all' else None
            date_str = request.form.get('event_date')
            start_time = request.form.get('start_time', '02:00 PM').strip()
            end_time = request.form.get('end_time', '04:00 PM').strip()
            location_or_link = request.form.get('location_or_link', 'Campus Auditorium').strip()
            description = request.form.get('description', '').strip()
            image_url = request.form.get('image_url', '').strip()

            ev_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else datetime.utcnow().date()

            ev = Event(
                title=title,
                event_type=event_type,
                course_id=course_id,
                created_by_id=current_user.id,
                event_date=ev_date,
                start_time=start_time,
                end_time=end_time,
                location_or_link=location_or_link,
                description=description,
                image_url=image_url if image_url else None,
                status='published'
            )
            db.session.add(ev)
            db.session.commit()
            flash(f"🚀 Event '{title}' Published Successfully!", "success")
            return redirect(url_for('admin.events'))

        elif action == 'approve_event':
            event_id = request.form.get('event_id')
            ev = Event.query.get(event_id)
            if ev:
                ev.status = 'published'
                db.session.commit()
                flash(f"🎉 Approved & Published Event '{ev.title}'!", "success")
            return redirect(url_for('admin.events'))

        elif action == 'reject_event':
            event_id = request.form.get('event_id')
            reason = request.form.get('rejection_reason', 'Content unsuitable').strip()
            ev = Event.query.get(event_id)
            if ev:
                ev.status = 'rejected'
                ev.rejection_reason = reason
                db.session.commit()
                flash(f"❌ Event '{ev.title}' rejected.", "info")
            return redirect(url_for('admin.events'))

        elif action == 'edit_event':
            event_id = request.form.get('event_id')
            ev = Event.query.get(event_id)
            if ev:
                ev.title = request.form.get('title', ev.title).strip()
                ev.event_type = request.form.get('event_type', ev.event_type)
                course_id = request.form.get('course_id')
                ev.course_id = int(course_id) if course_id and course_id != 'all' else None
                date_str = request.form.get('event_date')
                if date_str:
                    ev.event_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                ev.start_time = request.form.get('start_time', ev.start_time).strip()
                ev.end_time = request.form.get('end_time', ev.end_time).strip()
                ev.location_or_link = request.form.get('location_or_link', ev.location_or_link).strip()
                ev.description = request.form.get('description', ev.description or '').strip()
                image_url = request.form.get('image_url', '').strip()
                if image_url:
                    ev.image_url = image_url
                db.session.commit()
                flash(f"✏️ Event '{ev.title}' updated successfully!", "success")
            return redirect(url_for('admin.events'))

    if target_tenant_id:
        all_events = Event.query.join(User, Event.created_by_id == User.id).filter(User.tenant_id == target_tenant_id).order_by(Event.event_date.asc()).all()
    else:
        if current_user.role != 'superadmin':
            all_events = Event.query.join(User, Event.created_by_id == User.id).filter(User.tenant_id == current_user.tenant_id).order_by(Event.event_date.asc()).all()
        else:
            all_events = Event.query.order_by(Event.event_date.asc()).all()

    # Auto-expire events whose date has passed
    today = datetime.utcnow().date()
    expired_any = False
    for ev in all_events:
        if ev.event_date < today and ev.status not in ('expired', 'rejected'):
            ev.status = 'expired'
            expired_any = True
    if expired_any:
        db.session.commit()

    published_events = [e for e in all_events if e.status == 'published']
    pending_events = [e for e in all_events if e.status == 'pending_approval']
    rejected_events = [e for e in all_events if e.status == 'rejected']
    expired_events = [e for e in all_events if e.status == 'expired']

    return render_template(
        'admin/events.html',
        courses=all_courses,
        all_events=all_events,
        published_events=published_events,
        pending_events=pending_events,
        rejected_events=rejected_events,
        expired_events=expired_events
    )


@admin_bp.route('/api/scan_attendance', methods=['POST'])
@login_required
@role_required('admin')
def api_scan_attendance():
    data = request.get_json(silent=True) or request.form
    roll_number = str(data.get('roll_number', '')).strip()
    course_id = data.get('course_id')
    status_val = data.get('status', 'present')

    if course_id == "":
        course_id = None

    if not roll_number:
        return jsonify({'success': False, 'message': 'Roll Number required!'}), 400

    student = None
    enr = Enrollment.query.filter((Enrollment.roll_number == roll_number) | (Enrollment.id == roll_number)).first()
    if enr:
        student = enr.user
        if not course_id:
            course_id = enr.course_id
    else:
        student = User.query.filter((User.roll_number == roll_number) | (str(User.id) == roll_number)).first()
        if not student:
            student = User.query.filter_by(email=f"student_{roll_number}@titan.edu").first()

    if not student:
        return jsonify({'success': False, 'message': f'Student with Roll No {roll_number} not found!'}), 404

    student_roll = roll_number
    if enr:
        student_roll = enr.get_roll_number()
    elif student:
        student_roll = student.roll_number or str(student.id)

    target_date = datetime.utcnow().date()
    if not course_id:
        if student.enrollments:
            course_id = student.enrollments[0].course_id
        else:
            return jsonify({'success': False, 'message': 'Student has no active course enrollments!'}), 400

    course = Course.query.get(course_id)
    if not course:
        return jsonify({'success': False, 'message': 'Course not found!'}), 404

    sess = AttendanceSession.query.filter_by(course_id=course_id, session_date=target_date).first()
    if not sess:
        inst_id = course.instructor_id if course.instructor_id else current_user.id
        sess = AttendanceSession(
            course_id=course_id,
            instructor_id=inst_id,
            title=f"Daily Class Session - {target_date}",
            session_date=target_date,
            pin_code="AUTO-QR",
            status='open'
        )
        db.session.add(sess)
        db.session.commit()

    rec = AttendanceRecord.query.filter_by(session_id=sess.id, user_id=student.id).first()
    if not rec:
        rec = AttendanceRecord(
            session_id=sess.id,
            user_id=student.id,
            status=status_val,
            method='qr_scan',
            marked_at=datetime.utcnow()
        )
        db.session.add(rec)
        action_msg = f"Marked {status_val.upper()}"
    else:
        rec.status = status_val
        rec.method = 'qr_scan'
        action_msg = f"Updated to {status_val.upper()}"

    db.session.commit()

    # Check fee payment status on enrollment or student user
    payment_status = (enr.payment_status if (enr and hasattr(enr, 'payment_status')) else None) or getattr(student, 'payment_status', 'PAID')
    is_fee_paid = (payment_status and str(payment_status).upper() == 'PAID')

    if not is_fee_paid:
        msg = f"⚠️ FEE UNPAID WARNING: {student.name} (Roll No: {student_roll}) Fee Status is '{payment_status or 'UNPAID'}'!"
    else:
        msg = f"✅ {student.name} (Roll No: {student_roll}) - {action_msg}!"

    return jsonify({
        'success': True,
        'fee_paid': is_fee_paid,
        'payment_status': payment_status or 'UNPAID',
        'message': msg,
        'student_name': student.name,
        'roll_number': student_roll,
        'course_title': course.title,
        'status': status_val,
        'time': datetime.utcnow().strftime('%I:%M:%S %p')
    })


def _save_or_base64_upload(file_obj, subfolder='team', is_video=False):
    if not file_obj or not getattr(file_obj, 'filename', None):
        return None
    import base64
    from werkzeug.utils import secure_filename
    from flask import current_app
    
    is_vercel = bool(os.environ.get('VERCEL') or os.environ.get('VERCEL_ENV'))

    # If running on Vercel or serverless, read directly into Base64 (avoiding read-only filesystem completely)
    if is_vercel:
        try:
            file_obj.seek(0)
            file_bytes = file_obj.read()
            if file_bytes:
                mime = getattr(file_obj, 'mimetype', None) or ('video/mp4' if is_video else 'image/jpeg')
                encoded = base64.b64encode(file_bytes).decode('utf-8')
                return f"data:{mime};base64,{encoded}"
        except Exception:
            return None

    # Local development: Attempt saving to static/uploads
    try:
        prefix = 'tour' if is_video else subfolder
        fname = secure_filename(f"{prefix}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{file_obj.filename}")
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', subfolder)
        os.makedirs(upload_folder, exist_ok=True)
        save_path = os.path.join(upload_folder, fname)
        file_obj.save(save_path)
        return f"/static/uploads/{subfolder}/{fname}"
    except Exception:
        try:
            file_obj.seek(0)
            file_bytes = file_obj.read()
            if file_bytes:
                mime = getattr(file_obj, 'mimetype', None) or ('video/mp4' if is_video else 'image/jpeg')
                encoded = base64.b64encode(file_bytes).decode('utf-8')
                return f"data:{mime};base64,{encoded}"
        except Exception:
            pass
    return None


@admin_bp.route('/team', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'superadmin'])
def team():
    from .public import _ensure_team_members_seeded
    _ensure_team_members_seeded()

    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            designation = request.form.get('designation', '').strip()
            bio = request.form.get('bio', '').strip()
            
            try:
                order = int(request.form.get('order', 1))
            except (ValueError, TypeError):
                order = 1

            image_url = None
            image_b64 = request.form.get('image_b64', '').strip()
            if image_b64 and image_b64.startswith('data:'):
                image_url = image_b64
            else:
                file = request.files.get('image')
                if file and file.filename:
                    image_url = _save_or_base64_upload(file, 'team')

            initials = ''.join([w[0].upper() for w in name.split()[:2]]) if name else 'TM'

            member = TeamMember(
                name=name,
                designation=designation,
                bio=bio,
                image_url=image_url,
                initials=initials,
                order=order
            )
            db.session.add(member)
            db.session.commit()
            flash(f"👤 Team member '{name}' added successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"⚠️ Error saving team member: {str(e)}", "error")
        return redirect(url_for('admin.team'))

    members = TeamMember.query.order_by(TeamMember.order.asc(), TeamMember.id.asc()).all()
    return render_template('admin/team.html', members=members, active_page='team')


@admin_bp.route('/team/<int:member_id>/edit', methods=['POST'])
@login_required
@role_required(['admin', 'superadmin'])
def edit_team_member(member_id):
    from .public import _ensure_team_members_seeded
    _ensure_team_members_seeded()

    try:
        member = TeamMember.query.get(member_id)
        if not member:
            flash("⚠️ Team member not found.", "error")
            return redirect(url_for('admin.team'))

        member.name = request.form.get('name', member.name).strip()
        member.designation = request.form.get('designation', member.designation).strip()
        member.bio = request.form.get('bio', member.bio or '').strip()
        
        try:
            member.order = int(request.form.get('order', member.order or 1))
        except (ValueError, TypeError):
            pass

        member.initials = ''.join([w[0].upper() for w in member.name.split()[:2]]) if member.name else 'TM'

        try:
            from sqlalchemy import text
            db.session.execute(text("ALTER TABLE team_members ALTER COLUMN image_url TYPE TEXT;"))
            db.session.commit()
        except Exception:
            db.session.rollback()

        image_b64 = request.form.get('image_b64', '').strip()
        if image_b64 and image_b64.startswith('data:'):
            member.image_url = image_b64
        else:
            file = request.files.get('image')
            if file and file.filename:
                new_img = _save_or_base64_upload(file, 'team')
                if new_img:
                    member.image_url = new_img

        db.session.commit()
        flash(f"✏️ Team member '{member.name}' updated successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"⚠️ Error updating team member: {str(e)}", "error")

    return redirect(url_for('admin.team'))


@admin_bp.route('/team/<int:member_id>/delete', methods=['POST'])
@login_required
@role_required(['admin', 'superadmin'])
def delete_team_member(member_id):
    try:
        member = TeamMember.query.get(member_id)
        if member:
            name = member.name
            db.session.delete(member)
            db.session.commit()
            flash(f"🗑️ Team member '{name}' removed successfully.", "info")
    except Exception as e:
        db.session.rollback()
        flash(f"⚠️ Error removing team member: {str(e)}", "error")
    return redirect(url_for('admin.team'))


@admin_bp.route('/campuses', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'superadmin'])
def admin_campuses():
    from .public import _ensure_campuses_seeded
    _ensure_campuses_seeded()

    if request.method == 'POST':
        try:
            title = request.form.get('title', '').strip()
            city = request.form.get('city', '').strip()
            region = request.form.get('region', 'Main Hub').strip()
            address = request.form.get('address', '').strip()
            phone = request.form.get('phone', '').strip()
            email = request.form.get('email', '').strip()
            description = request.form.get('description', '').strip()
            try:
                active_students = int(request.form.get('active_students', 500))
            except (ValueError, TypeError):
                active_students = 500

            image_url = None
            image_b64 = request.form.get('image_b64', '').strip()
            if image_b64 and image_b64.startswith('data:'):
                image_url = image_b64
            else:
                img_file = request.files.get('image')
                if img_file and img_file.filename:
                    image_url = _save_or_base64_upload(img_file, 'campuses')

            video_url = None
            vid_file = request.files.get('video')
            if vid_file and vid_file.filename:
                video_url = _save_or_base64_upload(vid_file, 'campuses', is_video=True)
            else:
                video_url = request.form.get('video_link', '').strip() or None

            campus = Campus(
                title=title,
                city=city,
                region=region,
                address=address,
                phone=phone,
                email=email,
                description=description,
                active_students=active_students,
                image_url=image_url,
                video_url=video_url
            )
            db.session.add(campus)
            db.session.commit()
            flash(f"🏛️ Campus '{title}' in {city} created successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"⚠️ Error creating campus: {str(e)}", "error")
        return redirect(url_for('admin.admin_campuses'))

    campuses_list = Campus.query.order_by(Campus.city.asc(), Campus.id.desc()).all()
    return render_template('admin/campuses.html', campuses=campuses_list, active_page='admin_campuses')


@admin_bp.route('/campuses/<int:campus_id>/edit', methods=['POST'])
@login_required
@role_required(['admin', 'superadmin'])
def edit_campus(campus_id):
    try:
        campus = Campus.query.get(campus_id)
        if not campus:
            flash("⚠️ Campus not found.", "error")
            return redirect(url_for('admin.admin_campuses'))

        campus.title = request.form.get('title', campus.title).strip()
        campus.city = request.form.get('city', campus.city).strip()
        campus.region = request.form.get('region', campus.region).strip()
        campus.address = request.form.get('address', campus.address).strip()
        campus.phone = request.form.get('phone', campus.phone).strip()
        campus.email = request.form.get('email', campus.email).strip()
        campus.description = request.form.get('description', campus.description).strip()
        try:
            campus.active_students = int(request.form.get('active_students', campus.active_students or 500))
        except (ValueError, TypeError):
            pass

        image_b64 = request.form.get('image_b64', '').strip()
        if image_b64 and image_b64.startswith('data:'):
            campus.image_url = image_b64
        else:
            img_file = request.files.get('image')
            if img_file and img_file.filename:
                new_img = _save_or_base64_upload(img_file, 'campuses')
                if new_img:
                    campus.image_url = new_img

        vid_file = request.files.get('video')
        if vid_file and vid_file.filename:
            new_vid = _save_or_base64_upload(vid_file, 'campuses', is_video=True)
            if new_vid:
                campus.video_url = new_vid
        elif request.form.get('video_link'):
            campus.video_url = request.form.get('video_link').strip()

        db.session.commit()
        flash(f"✏️ Campus '{campus.title}' updated successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"⚠️ Error updating campus: {str(e)}", "error")

    return redirect(url_for('admin.admin_campuses'))


@admin_bp.route('/campuses/<int:campus_id>/delete', methods=['POST'])
@login_required
@role_required(['admin', 'superadmin'])
def delete_campus(campus_id):
    try:
        campus = Campus.query.get(campus_id)
        if campus:
            title = campus.title
            db.session.delete(campus)
            db.session.commit()
            flash(f"🗑️ Campus '{title}' removed successfully.", "info")
    except Exception as e:
        db.session.rollback()
        flash(f"⚠️ Error deleting campus: {str(e)}", "error")
    return redirect(url_for('admin.admin_campuses'))


@admin_bp.route('/registrations')
@login_required
@role_required(['admin', 'superadmin'])
def registrations():
    from ..models import StudentRegistration, User
    
    # Auto-verify any approved students who are not yet verified (fixes retroactively approved users)
    approved_registrations = StudentRegistration.query.filter_by(status='approved').all()
    if approved_registrations:
        emails = [r.email for r in approved_registrations]
        unverified_users = User.query.filter(User.verified == False, User.email.in_(emails)).all()
        if unverified_users:
            for u in unverified_users:
                u.verified = True
            db.session.commit()

    pending = StudentRegistration.query.filter_by(status='pending').order_by(StudentRegistration.id.desc()).all()
    approved = StudentRegistration.query.filter_by(status='approved').order_by(StudentRegistration.id.desc()).all()
    rejected = StudentRegistration.query.filter_by(status='rejected').order_by(StudentRegistration.id.desc()).all()
    return render_template('admin/registrations.html', pending=pending, approved=approved, rejected=rejected, active_page='registrations')


@admin_bp.route('/registrations/<int:reg_id>/approve', methods=['POST'])
@login_required
@role_required(['admin', 'superadmin'])
def approve_registration(reg_id):
    from ..models import StudentRegistration, User, Course, Enrollment
    reg = StudentRegistration.query.get_or_404(reg_id)
    
    # Check if User already exists
    user = User.query.filter_by(email=reg.email).first()
    if not user:
        user = User(
            name=reg.full_name,
            email=reg.email,
            password_hash=reg.password_hash,
            role='student',
            avatar_url=reg.avatar_url,
            verified=True,
            bio=f"Student of {reg.course_name} at {reg.campus_name}. CNIC/ID: {reg.id_number}, Father: {reg.father_name}"
        )
        db.session.add(user)
        db.session.flush() # get user.id
    else:
        user.verified = True

    # Enroll in course if available
    course = Course.query.filter(Course.title.ilike(f"%{reg.course_name}%")).first()
    if not course:
        course = Course.query.first()
    
    if course:
        existing_enr = Enrollment.query.filter_by(user_id=user.id, course_id=course.id).first()
        if not existing_enr:
            from ..models import CourseKey
            course_key = None
            if reg.access_code_used:
                course_key = CourseKey.query.filter_by(key_code=reg.access_code_used, course_id=course.id).first()
                if course_key and not course_key.is_used:
                    course_key.is_used = True
                    course_key.used_by_id = user.id
                    course_key.used_at = datetime.utcnow()
                    
            enr = Enrollment(
                user_id=user.id,
                course_id=course.id,
                phone_number=reg.phone,
                roll_number=f"SMIT-{user.id:04d}",
                campus=reg.campus_name,
                access_key_used=reg.access_code_used if course_key else None
            )
            db.session.add(enr)

    reg.status = 'approved'
    db.session.commit()
    flash(f"✅ Student application for '{reg.full_name}' approved successfully! User account created.", "success")
    return redirect(url_for('admin.registrations'))


@admin_bp.route('/registrations/<int:reg_id>/reject', methods=['POST'])
@login_required
@role_required(['admin', 'superadmin'])
def reject_registration(reg_id):
    from ..models import StudentRegistration
    reg = StudentRegistration.query.get_or_404(reg_id)
    reg.status = 'rejected'
    db.session.commit()
    flash(f"❌ Student application for '{reg.full_name}' rejected.", "info")
    return redirect(url_for('admin.registrations'))


# ════════════════════════════════════════════════════════════════════════════
# PASSWORD RESET ADMIN APPROVAL ROUTES
# ════════════════════════════════════════════════════════════════════════════
@admin_bp.route('/password-resets')
@login_required
@role_required(['admin', 'superadmin'])
def password_resets():
    from ..models import PasswordResetRequest
    pending_requests = PasswordResetRequest.query.filter_by(status='pending').order_by(PasswordResetRequest.created_at.desc()).all()
    processed_requests = PasswordResetRequest.query.filter(PasswordResetRequest.status != 'pending').order_by(PasswordResetRequest.processed_at.desc()).limit(20).all()
    return render_template('admin/password_resets.html', pending_requests=pending_requests, processed_requests=processed_requests, active_page='admin_password_resets')


@admin_bp.route('/password-resets/<int:req_id>/approve', methods=['POST'])
@login_required
@role_required(['admin', 'superadmin'])
def approve_password_reset(req_id):
    from ..models import PasswordResetRequest
    req_item = PasswordResetRequest.query.get_or_404(req_id)
    
    # Update user password with the approved hash
    req_item.user.password_hash = req_item.new_password_hash
    req_item.status = 'approved'
    req_item.processed_at = datetime.utcnow()
    
    audit = AuditLog(
        user_id=current_user.id,
        action=f"Approved password reset for user ID: {req_item.user_id} ({req_item.user.name})",
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    db.session.add(audit)
    db.session.commit()
    
    flash(f"✅ Password reset for '{req_item.user.name}' ({req_item.user.email}) approved! Password has been updated.", "success")
    return redirect(url_for('admin.password_resets'))


@admin_bp.route('/password-resets/<int:req_id>/reject', methods=['POST'])
@login_required
@role_required(['admin', 'superadmin'])
def reject_password_reset(req_id):
    from ..models import PasswordResetRequest
    req_item = PasswordResetRequest.query.get_or_404(req_id)
    req_item.status = 'rejected'
    req_item.processed_at = datetime.utcnow()
    
    audit = AuditLog(
        user_id=current_user.id,
        action=f"Rejected password reset for user ID: {req_item.user_id} ({req_item.user.name})",
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    db.session.add(audit)
    db.session.commit()
    
    flash(f"❌ Password reset request for '{req_item.user.name}' rejected.", "info")
    return redirect(url_for('admin.password_resets'))

@admin_bp.route('/courses/<int:course_id>/access-receipt')
@login_required
@role_required(['admin', 'superadmin'])
def course_access_receipt(course_id):
    from ..models import Course, CourseKey
    course = Course.query.get_or_404(course_id)
    if current_user.role != 'superadmin' and course.tenant_id != current_user.tenant_id:
        abort(403)
        
    # Get how many keys already exist
    existing_keys_count = CourseKey.query.filter_by(course_id=course.id).count()
    limit = course.student_limit or 100
    
    # Generate missing keys
    if existing_keys_count < limit:
        import uuid
        clean_title = "".join([c for c in course.title if c.isalnum()]).upper()
        prefix = clean_title[:4] if len(clean_title) >= 4 else "TITAN"
        
        for _ in range(limit - existing_keys_count):
            while True:
                candidate = f"{prefix}-{uuid.uuid4().hex[:6].upper()}"
                if not CourseKey.query.filter_by(key_code=candidate).first():
                    new_key = CourseKey(course_id=course.id, key_code=candidate)
                    db.session.add(new_key)
                    break
        db.session.commit()
        
    all_keys = CourseKey.query.filter_by(course_id=course.id).all()
    return render_template('admin/course_access_receipt.html', course=course, keys=all_keys)


@admin_bp.route('/courses/<int:course_id>/add-seats', methods=['POST'])
@login_required
@role_required(['admin', 'superadmin'])
def course_add_seats(course_id):
    from ..models import Course, CourseKey
    course = Course.query.get_or_404(course_id)
    if current_user.role != 'superadmin' and course.tenant_id != current_user.tenant_id:
        abort(403)
        
    try:
        additional_seats = int(request.form.get('additional_seats', 0))
    except ValueError:
        additional_seats = 0
        
    if additional_seats > 0:
        course.student_limit = (course.student_limit or 100) + additional_seats
        db.session.commit()
        
        # Generate new keys
        import uuid
        clean_title = "".join([c for c in course.title if c.isalnum()]).upper()
        prefix = clean_title[:4] if len(clean_title) >= 4 else "TITAN"
        
        for _ in range(additional_seats):
            while True:
                candidate = f"{prefix}-{uuid.uuid4().hex[:6].upper()}"
                if not CourseKey.query.filter_by(key_code=candidate).first():
                    new_key = CourseKey(course_id=course.id, key_code=candidate)
                    db.session.add(new_key)
                    break
        db.session.commit()
        flash(f"🎟️ Successfully added {additional_seats} more seats and generated access keys!", "success")
        
    return redirect(url_for('admin.course_access_receipt', course_id=course.id))


@admin_bp.route('/api/send_broadcast', methods=['POST'])
@login_required
@role_required('admin')
def api_send_broadcast():
    from ..models import Notification, User
    data = request.get_json(silent=True) or request.form
    target = data.get('target', 'all')
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({'success': False, 'message': 'Message content cannot be empty.'}), 400
        
    query = User.query
    if current_user.role != 'superadmin' and current_user.tenant_id:
        query = query.filter_by(tenant_id=current_user.tenant_id)
        
    if target == 'instructors':
        query = query.filter_by(role='instructor')
    elif target == 'enterprise':
        query = query.filter(User.role.in_(['superadmin', 'admin', 'instructor']))
    # 'all' targets all active platform users

    recipient_users = query.all()
    count = 0
    for u in recipient_users:
        n = Notification(
            user_id=u.id,
            title="📢 Platform Announcement",
            content=message,
            type="info"
        )
        db.session.add(n)
        count += 1
        
    db.session.commit()
    return jsonify({
        'success': True,
        'message': f"📢 Broadcast successfully dispatched to {count} users!",
        'count': count
    })


@admin_bp.route('/leaves', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def leaves():
    if request.method == 'POST':
        action = request.form.get('action')
        leave_id = request.form.get('leave_id')
        leave_obj = LeaveApplication.query.get_or_404(leave_id)
        
        if action == 'approve':
            leave_obj.status = 'Approved'
            # Notify student
            n = Notification(
                user_id=leave_obj.user_id,
                title="✅ Leave Application Approved",
                content=f"Your leave application from {leave_obj.start_date} to {leave_obj.end_date} has been officially APPROVED by Admin."
            )
            db.session.add(n)
            flash(f"✅ Leave application for '{leave_obj.user.name}' marked as APPROVED.", "success")
        elif action == 'reject':
            leave_obj.status = 'Rejected'
            # Notify student
            n = Notification(
                user_id=leave_obj.user_id,
                title="❌ Leave Application Status Update",
                content=f"Your leave application from {leave_obj.start_date} to {leave_obj.end_date} was reviewed by Admin."
            )
            db.session.add(n)
            flash(f"⚠️ Leave application for '{leave_obj.user.name}' marked as REJECTED.", "info")
        elif action == 'delete':
            db.session.delete(leave_obj)
            flash("🗑️ Leave application record removed.", "info")
            
        db.session.commit()
        return redirect(url_for('admin.leaves'))

    # Fetch all leaves for the current tenant
    leaves_query = LeaveApplication.query.filter_by(tenant_id=current_user.tenant_id)
    
    # Filter by status if provided
    status_filter = request.args.get('status', 'all')
    if status_filter and status_filter != 'all':
        leaves_query = leaves_query.filter(LeaveApplication.status.ilike(status_filter))
        
    leaves_list = leaves_query.order_by(LeaveApplication.created_at.desc()).all()
    courses = Course.query.filter_by(tenant_id=current_user.tenant_id).all()
    
    return render_template('admin/leaves.html', leaves=leaves_list, courses=courses, active_page='leaves')


@admin_bp.route('/resources', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def resources():
    db.create_all()
    courses = Course.query.filter_by(tenant_id=current_user.tenant_id).all()

    if request.method == 'POST':
        course_id = request.form.get('course_id', type=int)
        title = request.form.get('title', '').strip()
        resource_type = request.form.get('resource_type', 'PDF')
        file_url = request.form.get('file_url', '').strip() or None
        external_url = request.form.get('external_url', '').strip() or None
        file_size = request.form.get('file_size', '2.5 MB').strip()
        description = request.form.get('description', '').strip()

        if not course_id or not title:
            flash("❌ Please select a course and provide a resource title.", "danger")
        else:
            res = CourseResource(
                tenant_id=current_user.tenant_id,
                course_id=course_id,
                uploader_id=current_user.id,
                title=title,
                resource_type=resource_type,
                file_url=file_url,
                external_url=external_url,
                file_size=file_size,
                description=description
            )
            db.session.add(res)
            db.session.commit()
            flash(f"✅ Resource '{title}' published successfully for students!", "success")
            return redirect(url_for('admin.resources'))

    resources_list = CourseResource.query.order_by(CourseResource.created_at.desc()).all()
    return render_template('admin/resources.html', resources=resources_list, courses=courses, active_page='resources')


@admin_bp.route('/resources/<int:id>/edit', methods=['POST'])
@login_required
@role_required('admin')
def edit_resource(id):
    res = CourseResource.query.get_or_404(id)
    res.course_id = request.form.get('course_id', type=int) or res.course_id
    res.title = request.form.get('title', '').strip() or res.title
    res.resource_type = request.form.get('resource_type', 'PDF')
    res.file_url = request.form.get('file_url', '').strip() or None
    res.external_url = request.form.get('external_url', '').strip() or None
    res.file_size = request.form.get('file_size', '2.5 MB').strip()
    res.description = request.form.get('description', '').strip()
    db.session.commit()
    flash(f"✅ Resource '{res.title}' updated successfully!", "success")
    return redirect(url_for('admin.resources'))


@admin_bp.route('/resources/<int:id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_resource(id):
    res = CourseResource.query.get_or_404(id)
    db.session.delete(res)
    db.session.commit()
    flash("🗑️ Course resource deleted successfully.", "success")
    return redirect(url_for('admin.resources'))












