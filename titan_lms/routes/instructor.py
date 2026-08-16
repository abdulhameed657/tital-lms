from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from ..models import (
    db, User, Course, Lesson, Enrollment, Quiz, Question, QuizAttempt, 
    StudentAnswer, RevenueRecord, Notification, Certificate, 
    AttendanceSession, AttendanceRecord, CourseSchedule, Event, CourseResource
)
from ..decorators import role_required
import json

instructor_bp = Blueprint('instructor', __name__)

@instructor_bp.context_processor
def inject_instructor_vars():
    endpoint = request.endpoint
    active_page = 'dashboard'
    if endpoint:
        if 'dashboard' in endpoint:
            active_page = 'dashboard'
        elif 'schedules' in endpoint:
            active_page = 'schedules'
        elif 'events' in endpoint:
            active_page = 'events'
        elif 'attendance' in endpoint:
            active_page = 'attendance'
        elif 'resources' in endpoint:
            active_page = 'resources'
        elif 'create_course' in endpoint or 'curriculum' in endpoint or 'course' in endpoint:
            active_page = 'courses'
        elif 'submission' in endpoint or 'grade' in endpoint or 'grading' in endpoint:
            active_page = 'grading'
        elif 'certificate' in endpoint:
            active_page = 'certificates'
        elif 'revenue' in endpoint:
            active_page = 'revenue'
        elif 'ai_quiz' in endpoint:
            active_page = 'ai_quiz'
        elif 'live' in endpoint:
            active_page = 'live'
        elif 'forum' in endpoint:
            active_page = 'forum'
        elif 'leaderboard' in endpoint:
            active_page = 'leaderboard'
        elif 'profile' in endpoint:
            active_page = 'profile'
    
    unread_notifications = 0
    if current_user and current_user.is_authenticated:
        unread_notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        
    return dict(active_page=active_page, unread_notifications=unread_notifications)


@instructor_bp.route('/dashboard')
@login_required
@role_required('instructor')
def dashboard():
    courses = Course.query.filter_by(instructor_id=current_user.id).all()
    # Calculate some stats
    total_students = 0
    total_revenue = 0.0
    for course in courses:
        total_students += len(course.enrollments)
        for rev in course.revenue_records:
            total_revenue += rev.amount
            
    # Platform split: instructor gets 70%
    instructor_share = total_revenue * 0.7

    # Calculate at-risk students dynamically
    course_ids = [c.id for c in courses]
    at_risk_students = []
    
    if course_ids:
        enrollments = Enrollment.query.filter(Enrollment.course_id.in_(course_ids)).all()
        student_users = {}
        for enr in enrollments:
            if enr.user:
                student_users[enr.user_id] = enr.user
                
        for user_id, student in student_users.items():
            failed_quiz = QuizAttempt.query.filter_by(user_id=student.id).filter((QuizAttempt.passed == False) | (QuizAttempt.score < 50.0)).first()
            
            # Count absences
            absent_count = 0
            attendance_recs = AttendanceRecord.query.filter_by(user_id=student.id).all()
            for att_rec in attendance_recs:
                if att_rec.status == 'absent':
                    absent_count += 1
            
            reason = None
            if failed_quiz:
                quiz_title = failed_quiz.quiz.title if failed_quiz.quiz else "Quiz"
                reason = f"Failed {quiz_title} ({int(failed_quiz.score)}% - Retry Needed)"
            elif absent_count > 0:
                reason = f"Missed {absent_count} class sessions (Absent)"
            elif not attendance_recs and enrollments:
                reason = "Low engagement (No attendance logged)"
                
            if reason:
                avatar_url = f"https://api.dicebear.com/7.x/adventurer/svg?seed={student.name}"
                at_risk_students.append({
                    'id': student.id,
                    'name': student.name,
                    'reason': reason,
                    'avatar_url': avatar_url,
                    'email': student.email
                })
    
    return render_template('instructor/dashboard.html', 
                           courses=courses, 
                           total_students=total_students, 
                           total_revenue=total_revenue,
                           instructor_share=instructor_share,
                           at_risk_students=at_risk_students)

@instructor_bp.route('/courses')
@login_required
@role_required('instructor')
def course_management():
    courses = Course.query.filter_by(instructor_id=current_user.id).all()
    return render_template('instructor/courses.html', courses=courses)

@instructor_bp.route('/courses/create', methods=['GET', 'POST'])
@login_required
@role_required('instructor')
def create_course():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        price = float(request.form.get('price', 0.0))
        custom_category = request.form.get('custom_category', '').strip()
        category = custom_category if custom_category else request.form.get('category', 'General')
        level = request.form.get('level', 'Beginner')
        thumbnail = request.form.get('thumbnail')
        
        if title and description:
            new_course = Course(
                instructor_id=current_user.id,
                title=title,
                description=description,
                price=price,
                category=category,
                level=level,
                thumbnail=thumbnail or 'https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=600',
                status='draft',
                tenant_id=current_user.tenant_id
            )
            db.session.add(new_course)
            db.session.commit()
            flash(f"Course '{title}' successfully created as Draft! Add lessons to publish.", "success")
            return redirect(url_for('instructor.course_management'))
            
    return render_template('instructor/create_course.html')

@instructor_bp.route('/courses/<int:course_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('instructor')
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    if course.instructor_id != current_user.id:
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
                return redirect(url_for('instructor.edit_course', course_id=course.id))
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
                return redirect(url_for('instructor.edit_course', course_id=course.id))
        else:
            title = request.form.get('title')
            description = request.form.get('description')
            price_raw = request.form.get('price')
            price = float(price_raw) if price_raw is not None and price_raw != '' else course.price
            custom_category = request.form.get('custom_category', '').strip()
            category = custom_category if custom_category else request.form.get('category', course.category)
            level = request.form.get('level', course.level)
            thumbnail = request.form.get('thumbnail')
            
            if title and description:
                course.title = title
                course.description = description
                course.price = price
                course.category = category
                course.level = level
                if thumbnail:
                    course.thumbnail = thumbnail
                db.session.commit()
                flash(f"✏️ Course '{title}' details updated successfully!", "success")
                return redirect(url_for('instructor.edit_course', course_id=course.id))
                
    return render_template('instructor/edit_course.html', course=course)

@instructor_bp.route('/courses/<int:course_id>/request_delete', methods=['POST'])
@login_required
@role_required('instructor')
def request_delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    if course.instructor_id != current_user.id:
        abort(403)
        
    reason = request.form.get('reason', 'Requested deletion by instructor')
    course.status = 'delete_requested'
    
    # Send notification to Admin users
    if current_user.tenant_id:
        admin_users = User.query.filter_by(role='admin', tenant_id=current_user.tenant_id).all()
    else:
        admin_users = User.query.filter_by(role='admin', tenant_id=current_user.tenant_id).all()
    for admin in admin_users:
        notif = Notification(
            user_id=admin.id,
            title="⚠️ Course Deletion Approval Required",
            content=f"Instructor {current_user.name} requested deletion for course '{course.title}' (ID #{course.id}). Reason: {reason}",
            type="warning"
        )
        db.session.add(notif)
    db.session.commit()
    
    flash(f"⏳ Deletion request for '{course.title}' sent to Admin for approval. The course is now pending deletion approval.", "info")
    return redirect(url_for('instructor.course_management'))

@instructor_bp.route('/courses/<int:course_id>/curriculum', methods=['GET', 'POST'])
@login_required
@role_required('instructor')
def curriculum(course_id):
    course = Course.query.get_or_404(course_id)
    if course.instructor_id != current_user.id:
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
            return redirect(url_for('instructor.curriculum', course_id=course.id))
            
    return render_template('instructor/curriculum.html', course=course)

@instructor_bp.route('/lessons/<int:lesson_id>/delete', methods=['POST'])
@login_required
@role_required('instructor')
def delete_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    course = lesson.course
    if course.instructor_id != current_user.id:
        abort(403)
        
    title = lesson.title
    db.session.delete(lesson)
    db.session.commit()
    flash(f"🗑️ Module '{title}' deleted from curriculum.", "success")
    return redirect(url_for('instructor.edit_course', course_id=course.id))

@instructor_bp.route('/lessons/<int:lesson_id>/edit', methods=['POST'])
@login_required
@role_required('instructor')
def edit_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    course = lesson.course
    if course.instructor_id != current_user.id:
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
    return redirect(url_for('instructor.edit_course', course_id=course.id))

@instructor_bp.route('/courses/<int:course_id>/publish', methods=['POST'])
@login_required
@role_required('instructor')
def publish_course(course_id):
    course = Course.query.get_or_404(course_id)
    if course.instructor_id != current_user.id:
        abort(403)
    if not course.lessons:
        flash("You cannot publish a course without any lessons.", "error")
    else:
        course.status = 'published'
        db.session.commit()
        flash(f"Course '{course.title}' is now live!", "success")
    return redirect(url_for('instructor.course_management'))

@instructor_bp.route('/submissions')
@login_required
@role_required('instructor')
def grading():
    # Show quiz attempts for courses taught by this instructor
    courses = Course.query.filter_by(instructor_id=current_user.id).all()
    course_ids = [c.id for c in courses]
    attempts = QuizAttempt.query.join(Quiz).filter(Quiz.course_id.in_(course_ids)).order_by(QuizAttempt.attempted_at.desc()).all()
    
    # Scan assignment upload files on disk
    from flask import current_app
    import os
    from datetime import datetime
    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'assignments')
    file_submissions = []
    if os.path.exists(upload_dir):
        for fname in os.listdir(upload_dir):
            parts = fname.split('_')
            if len(parts) >= 2:
                try:
                    student_id = int(parts[0])
                    lesson_id = int(parts[1])
                    
                    student = User.query.get(student_id)
                    lesson = Lesson.query.get(lesson_id)
                    
                    if student and lesson and lesson.course_id in course_ids:
                        file_path = os.path.join(upload_dir, fname)
                        mtime = os.path.getmtime(file_path)
                        submitted_at = datetime.fromtimestamp(mtime)
                        
                        file_submissions.append({
                            'student': student,
                            'lesson': lesson,
                            'submitted_at': submitted_at,
                            'file_url': f'/static/uploads/assignments/{fname}',
                            'filename': fname
                        })
                except Exception:
                    continue
                    
    # Sort files newest first
    file_submissions.sort(key=lambda x: x['submitted_at'], reverse=True)
    
    return render_template('instructor/submissions.html', attempts=attempts, file_submissions=file_submissions)

@instructor_bp.route('/submissions/<int:attempt_id>/grade', methods=['GET', 'POST'])
@login_required
@role_required('instructor')
def grade_submission(attempt_id):
    attempt = QuizAttempt.query.get_or_404(attempt_id)
    # verify instructor teaches the course
    if attempt.quiz.course.instructor_id != current_user.id:
        abort(403)
        
    if request.method == 'POST':
        # Grade review comments
        feedback = request.form.get('feedback')
        score = float(request.form.get('score', attempt.score))
        passed = request.form.get('passed') == 'true'
        
        attempt.ai_feedback = feedback
        attempt.score = score
        attempt.passed = passed
        db.session.commit()
        flash("Grading evaluation successfully submitted.", "success")
        return redirect(url_for('instructor.grading'))
        
    return render_template('instructor/assignment_review.html', attempt=attempt)


@instructor_bp.route('/ai_quiz_generator', methods=['GET', 'POST'])
@login_required
@role_required('instructor')
def ai_quiz_generator():
    from ..ai import generate_quiz
    courses = Course.query.filter_by(instructor_id=current_user.id).all()
    generated_quiz = None
    target_course_id = None
    topic = ""
    if request.method == 'POST':
        target_course_id = request.form.get('course_id')
        topic = request.form.get('topic', 'General Programming')
        num_q = int(request.form.get('num_questions', 5))
        generated_quiz = generate_quiz(topic, num_questions=num_q)
        flash(f"✨ Gemini AI successfully generated {len(generated_quiz)} questions for '{topic}'!", "success")
    return render_template('instructor/ai_quiz_generator.html', courses=courses, generated_quiz=generated_quiz, target_course_id=target_course_id, topic=topic, active_page='ai_quiz')

@instructor_bp.route('/live_session')
@login_required
@role_required('instructor')
def live_session():
    courses = Course.query.filter_by(instructor_id=current_user.id).all()
    return render_template('instructor/live_session.html', courses=courses)

@instructor_bp.route('/leaderboard')
@login_required
@role_required('instructor')
def leaderboard():
    if current_user.tenant_id:
        students = User.query.filter_by(role='student', tenant_id=current_user.tenant_id).order_by(User.points.desc()).all()
    else:
        students = User.query.filter_by(role='student', tenant_id=current_user.tenant_id).order_by(User.points.desc()).all()
    podium = students[:3]
    remaining = students[3:]
    return render_template('instructor/leaderboard.html', podium=podium, remaining=remaining)

@instructor_bp.route('/ai_course_builder', methods=['GET', 'POST'])
@login_required
@role_required('instructor')
def ai_course_builder():
    if request.method == 'POST':
        topic = request.form.get('topic', 'Fullstack Web Development')
        level = request.form.get('level', 'Intermediate')
        video_url = request.form.get('video_url', '').strip()
        try:
            price = float(request.form.get('price', 49.99))
        except ValueError:
            price = 49.99

        if not video_url:
            video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

        c = Course(
            title=f"{topic} Mastery",
            description=f"Comprehensive course curriculum covering fundamental to advanced practices in {topic}.",
            price=price,
            category="Technology",
            level=level,
            instructor_id=current_user.id,
            status='draft'
        )
        db.session.add(c)
        db.session.flush()

        module_titles = request.form.getlist('module_title[]')
        module_types = request.form.getlist('module_type[]')
        module_contents = request.form.getlist('module_content[]')

        if module_titles and len(module_titles) > 0:
            for idx, title in enumerate(module_titles):
                if title.strip():
                    m_type = module_types[idx] if idx < len(module_types) else 'text'
                    m_content = module_contents[idx] if idx < len(module_contents) else ''
                    if m_type == 'video' and not m_content.strip():
                        m_content = video_url
                    l = Lesson(
                        course_id=c.id,
                        order=idx + 1,
                        title=title.strip(),
                        content_type=m_type,
                        content=m_content.strip() or "Module content"
                    )
                    db.session.add(l)
        else:
            # Default 3 generated modules
            l1 = Lesson(course_id=c.id, order=1, title=f"Introduction to {topic}", content_type="text", content=f"Overview of {topic} core principles.")
            l2 = Lesson(course_id=c.id, order=2, title=f"Advanced {topic} Masterclass", content_type="video", content=video_url)
            l3 = Lesson(course_id=c.id, order=3, title=f"{topic} Final Assessment", content_type="quiz", content="Quiz module")
            db.session.add_all([l1, l2, l3])

        db.session.commit()
        flash(f"🚀 AI Course '{c.title}' published successfully at Rs. {price:.2f}!", "success")
        return redirect(url_for('instructor.edit_course', course_id=c.id))
    return render_template('instructor/ai_course_builder.html', active_page='ai_course_builder')

@instructor_bp.route('/coupons', methods=['GET', 'POST'])
@login_required
@role_required('instructor')
def coupons():
    from ..models import Coupon
    if request.method == 'POST':
        code = request.form.get('code', '').upper().strip()
        discount = int(request.form.get('discount_percent', 10))
        max_uses = int(request.form.get('max_uses', 100))
        if code:
            cp = Coupon(code=code, discount_percent=discount, max_uses=max_uses, instructor_id=current_user.id, status='pending_approval')
            db.session.add(cp)
            db.session.commit()
            flash(f"🎟️ Coupon '{code}' ({discount}% OFF) created! Sent to Admin for approval.", "success")
            return redirect(url_for('instructor.coupons'))
    coupons_list = Coupon.query.filter_by(instructor_id=current_user.id).order_by(Coupon.created_at.desc()).all()
    return render_template('instructor/coupons.html', coupons=coupons_list, active_page='coupons')

@instructor_bp.route('/coupons/<int:coupon_id>/edit', methods=['POST'])
@login_required
@role_required('instructor')
def edit_coupon(coupon_id):
    from ..models import Coupon
    cp = Coupon.query.get_or_404(coupon_id)
    if cp.instructor_id != current_user.id:
        abort(403)
    code = request.form.get('code', '').upper().strip()
    discount = int(request.form.get('discount_percent', 10))
    max_uses = int(request.form.get('max_uses', 100))
    if code:
        cp.code = code
        cp.discount_percent = discount
        cp.max_uses = max_uses
        cp.status = 'pending_approval'  # Requires Admin re-approval
        db.session.commit()
        flash(f"✏️ Coupon '{code}' updated! Submitted for Admin re-approval.", "success")
    return redirect(url_for('instructor.coupons'))

@instructor_bp.route('/coupons/<int:coupon_id>/delete', methods=['POST'])
@login_required
@role_required('instructor')
def delete_coupon(coupon_id):
    from ..models import Coupon
    cp = Coupon.query.get_or_404(coupon_id)
    if cp.instructor_id != current_user.id:
        abort(403)
    db.session.delete(cp)
    db.session.commit()
    flash(f"🗑️ Coupon '{cp.code}' deleted.", "success")
    return redirect(url_for('instructor.coupons'))

@instructor_bp.route('/webinars', methods=['GET', 'POST'])
@login_required
@role_required('instructor')
def webinars():
    from ..models import Webinar
    if request.method == 'POST':
        title = request.form.get('title')
        meeting_url = request.form.get('meeting_url', 'https://zoom.us/j/123456789')
        duration = int(request.form.get('duration', 60))
        scheduled_at_str = request.form.get('scheduled_at')
        
        scheduled_at = datetime.utcnow()
        if scheduled_at_str:
            try:
                scheduled_at = datetime.strptime(scheduled_at_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                pass

        if title:
            w = Webinar(
                title=title,
                meeting_url=meeting_url,
                scheduled_at=scheduled_at,
                duration_minutes=duration,
                instructor_id=current_user.id
            )
            db.session.add(w)
            db.session.commit()
            flash(f"📹 Virtual Classroom '{title}' scheduled for {scheduled_at.strftime('%b %d, %Y at %I:%M %p')}!", "success")
            return redirect(url_for('instructor.webinars'))
    webinars_list = Webinar.query.filter_by(instructor_id=current_user.id).order_by(Webinar.scheduled_at.desc()).all()
    return render_template('instructor/webinars.html', webinars=webinars_list, active_page='webinars')

@instructor_bp.route('/webinars/delete/<int:webinar_id>', methods=['POST'])
@login_required
@role_required('instructor')
def delete_webinar(webinar_id):
    from ..models import Webinar
    w = Webinar.query.get_or_404(webinar_id)
    if w.instructor_id != current_user.id:
        abort(403)
    db.session.delete(w)
    db.session.commit()
    flash(f"🗑️ Virtual Classroom '{w.title}' deleted successfully.", "success")
    return redirect(url_for('instructor.webinars'))

@instructor_bp.route('/webinars/end/<int:webinar_id>', methods=['POST'])
@login_required
@role_required('instructor')
def end_webinar(webinar_id):
    from ..models import Webinar
    w = Webinar.query.get_or_404(webinar_id)
    if w.instructor_id != current_user.id:
        abort(403)
    w.status = 'completed'
    db.session.commit()
    flash(f"🏁 Live Session '{w.title}' marked as Completed and closed for students.", "success")
    return redirect(url_for('instructor.webinars'))

@instructor_bp.route('/webinars/edit/<int:webinar_id>', methods=['POST'])
@login_required
@role_required('instructor')
def edit_webinar(webinar_id):
    from ..models import Webinar
    w = Webinar.query.get_or_404(webinar_id)
    if w.instructor_id != current_user.id:
        abort(403)
        
    title = request.form.get('title')
    meeting_url = request.form.get('meeting_url')
    duration = int(request.form.get('duration', 60))
    scheduled_at_str = request.form.get('scheduled_at')
    
    if title:
        w.title = title
    if meeting_url:
        w.meeting_url = meeting_url
    w.duration_minutes = duration
    if scheduled_at_str:
        try:
            w.scheduled_at = datetime.strptime(scheduled_at_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            pass
            
    db.session.commit()
    flash(f"✏️ Virtual Classroom '{w.title}' updated successfully!", "success")
    return redirect(url_for('instructor.webinars'))

@instructor_bp.route('/quizzes/ai_generate', methods=['POST'])
@login_required
@role_required('instructor')
def ai_generate_quiz():
    course_id = request.form.get('course_id')
    topic = request.form.get('topic', 'Software Engineering')
    question_count = int(request.form.get('question_count', 3))
    
    course = Course.query.get_or_404(course_id)
    if course.instructor_id != current_user.id:
        abort(403)
        
    from ..ai import generate_quiz
    quiz_data = generate_quiz(topic, num_questions=question_count)
    
    # Create lesson & quiz
    order = len(course.lessons) + 1
    lesson = Lesson(
        course_id=course.id,
        order=order,
        title=f"AI Generated Quiz: {topic}",
        content_type="quiz",
        content="AI generated assessment module."
    )
    db.session.add(lesson)
    db.session.flush()
    
    quiz = Quiz(
        course_id=course.id,
        lesson_id=lesson.id,
        title=f"AI Assessment - {topic}",
        time_limit=900
    )
    db.session.add(quiz)
    db.session.flush()
    
    for q_item in quiz_data:
        choices_json = json.dumps(q_item.get('choices', [])) if isinstance(q_item.get('choices'), list) else ""
        q = Question(
            quiz_id=quiz.id,
            question_text=q_item.get('question_text', 'Sample Question'),
            question_type=q_item.get('question_type', 'multiple_choice'),
            choices=choices_json,
            correct_answer=q_item.get('correct_answer', '')
        )
        db.session.add(q)
        
    db.session.commit()
    flash(f"⚡ AI generated {len(quiz_data)} questions for quiz '{quiz.title}'!", "success")
    return redirect(url_for('instructor.edit_course', course_id=course.id))

@instructor_bp.route('/quizzes/save_ai_quiz', methods=['POST'])
@login_required
@role_required('instructor')
def save_ai_quiz():
    course_id = request.form.get('course_id')
    course = Course.query.get_or_404(course_id)
    if course.instructor_id != current_user.id:
        abort(403)
        
    quiz_title = request.form.get('quiz_title', 'AI Generated Quiz')
    time_limit_mins = int(request.form.get('time_limit_mins', 10))
    
    # Create lesson
    order = len(course.lessons) + 1
    lesson = Lesson(
        course_id=course.id,
        order=order,
        title=quiz_title,
        content_type="quiz",
        content="AI generated assessment module."
    )
    db.session.add(lesson)
    db.session.flush()
    
    # Create quiz
    quiz = Quiz(
        course_id=course.id,
        lesson_id=lesson.id,
        title=quiz_title,
        time_limit=time_limit_mins * 60
    )
    db.session.add(quiz)
    db.session.flush()
    
    q_texts = request.form.getlist('question_text')
    c_as = request.form.getlist('choice_a')
    c_bs = request.form.getlist('choice_b')
    c_cs = request.form.getlist('choice_c')
    c_ds = request.form.getlist('choice_d')
    correct_indices = request.form.getlist('correct_choice_index')
    
    for idx, text in enumerate(q_texts):
        if text.strip():
            ca = c_as[idx].strip() if idx < len(c_as) else "Option A"
            cb = c_bs[idx].strip() if idx < len(c_bs) else "Option B"
            cc = c_cs[idx].strip() if idx < len(c_cs) else "Option C"
            cd = c_ds[idx].strip() if idx < len(c_ds) else "Option D"
            c_list = [ca, cb, cc, cd]
            
            c_idx_str = correct_indices[idx] if idx < len(correct_indices) else "0"
            try:
                c_idx = int(c_idx_str)
            except ValueError:
                c_idx = 0
            correct_ans = c_list[c_idx] if 0 <= c_idx < len(c_list) else c_list[0]
            
            q = Question(
                quiz_id=quiz.id,
                question_text=text.strip(),
                question_type="multiple_choice",
                choices=json.dumps(c_list),
                correct_answer=correct_ans
            )
            db.session.add(q)
            
    db.session.commit()
    flash(f"🚀 Quiz '{quiz_title}' with {len(q_texts)} questions published to {course.title}!", "success")
    return redirect(url_for('instructor.edit_quiz', quiz_id=quiz.id))

@instructor_bp.route('/quizzes/<int:quiz_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('instructor')
def edit_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    course = quiz.course
    if course.instructor_id != current_user.id:
        abort(403)
        
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_quiz_info':
            quiz.title = request.form.get('title', quiz.title)
            mins = int(request.form.get('time_limit_mins', 10))
            quiz.time_limit = mins * 60
            if quiz.lesson:
                quiz.lesson.title = quiz.title
            db.session.commit()
            flash("✨ Quiz settings updated successfully!", "success")
            
        elif action == 'add_question':
            q_text = request.form.get('question_text', '').strip()
            ca = request.form.get('choice_a', '').strip()
            cb = request.form.get('choice_b', '').strip()
            cc = request.form.get('choice_c', '').strip()
            cd = request.form.get('choice_d', '').strip()
            c_idx = int(request.form.get('correct_choice_index', 0))
            
            if q_text and ca and cb:
                c_list = [ca, cb, cc, cd]
                correct_ans = c_list[c_idx] if 0 <= c_idx < len(c_list) else c_list[0]
                q = Question(
                    quiz_id=quiz.id,
                    question_text=q_text,
                    question_type="multiple_choice",
                    choices=json.dumps(c_list),
                    correct_answer=correct_ans
                )
                db.session.add(q)
                db.session.commit()
                flash("➕ New question added to quiz!", "success")
                
        elif action == 'update_question':
            q_id = request.form.get('question_id')
            q = Question.query.get(q_id)
            if q and q.quiz_id == quiz.id:
                q_text = request.form.get('question_text', '').strip()
                ca = request.form.get('choice_a', '').strip()
                cb = request.form.get('choice_b', '').strip()
                cc = request.form.get('choice_c', '').strip()
                cd = request.form.get('choice_d', '').strip()
                c_idx = int(request.form.get('correct_choice_index', 0))
                
                if q_text:
                    c_list = [ca, cb, cc, cd]
                    correct_ans = c_list[c_idx] if 0 <= c_idx < len(c_list) else c_list[0]
                    q.question_text = q_text
                    q.choices = json.dumps(c_list)
                    q.correct_answer = correct_ans
                    db.session.commit()
                    flash("✏️ Question updated successfully!", "success")
                    
        elif action == 'delete_question':
            q_id = request.form.get('question_id')
            q = Question.query.get(q_id)
            if q and q.quiz_id == quiz.id:
                db.session.delete(q)
                db.session.commit()
                flash("🗑️ Question deleted from quiz.", "success")
                
        return redirect(url_for('instructor.edit_quiz', quiz_id=quiz.id))
        
    return render_template('instructor/edit_quiz.html', quiz=quiz, course=course, active_page='ai_quiz')

@instructor_bp.route('/quizzes/<int:quiz_id>/delete', methods=['POST'])
@login_required
@role_required('instructor')
def delete_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    course = quiz.course
    if course.instructor_id != current_user.id:
        abort(403)
        
    course_id = course.id
    lesson = quiz.lesson
    if lesson:
        db.session.delete(lesson)
    db.session.delete(quiz)
    db.session.commit()
    flash("🗑️ Quiz deleted successfully.", "success")
    return redirect(url_for('instructor.edit_course', course_id=course_id))

@instructor_bp.route('/video_analytics')
@login_required
@role_required('instructor')
def video_analytics():
    courses = Course.query.filter_by(instructor_id=current_user.id).all()
    course_ids = [c.id for c in courses]
    enrollments = Enrollment.query.filter(Enrollment.course_id.in_(course_ids)).all() if course_ids else []
    # Unique enrolled students
    students_dict = {}
    for e in enrollments:
        if e.user and e.user.id not in students_dict:
            students_dict[e.user.id] = e.user
    students = list(students_dict.values())
    return render_template('instructor/video_analytics.html', courses=courses, students=students, active_page='video_analytics')

@instructor_bp.route('/send_reminder/<int:student_id>', methods=['POST'])
@login_required
@role_required('instructor')
def send_reminder(student_id):
    student = User.query.get_or_404(student_id)
    msg_type = request.form.get('type', 'reminder')
    
    if msg_type == 'help':
        title = "Instructor Help Offer"
        content = f"Your instructor {current_user.name} noticed you might need help with your course modules. Feel free to reach out!"
    else:
        title = "Course Completion Reminder"
        content = f"Reminder from {current_user.name}: Please complete your pending course modules to keep up with your cohort."
        
    notif = Notification(
        user_id=student.id,
        title=title,
        content=content,
        type='info'
    )
    db.session.add(notif)
    db.session.commit()
    
    return {"status": "success", "message": f"Notification sent to {student.name}!"}

# --- TITAN LIVE QUIZ Battle Hosting ---
@instructor_bp.route('/quiz-battle/host', methods=['GET', 'POST'])
@login_required
@role_required('instructor')
def host_quiz_battle():
    import random
    from datetime import datetime
    from ..models import QuizBattleSession, QuizBattleParticipant, QuizBattleQuestion
    
    if request.method == 'POST':
        title = request.form.get('title', 'Titan Live Quiz Arena')
        timer = int(request.form.get('timer_seconds', 15))
        pin = str(random.randint(100000, 999999))
        session = QuizBattleSession(
            battle_pin=pin,
            title=title,
            host_id=current_user.id,
            status='lobby',
            current_question=0,
            total_questions=1,
            timer_seconds=timer,
            question_start_time=None
        )
        db.session.add(session)
        db.session.flush()

        # Seed initial sample question
        q1 = QuizBattleQuestion(
            session_id=session.id,
            order_num=1,
            question_text="What is the output of `console.log(typeof NaN)` in JavaScript?",
            option_a="undefined",
            option_b="number",
            option_c="NaN",
            option_d="object",
            correct_option="b"
        )
        db.session.add(q1)

        # Broadcast live notification to all enrolled students
        from ..models import Notification, User
        if current_user.tenant_id:
            students = User.query.filter_by(role='student', tenant_id=current_user.tenant_id).all()
        else:
            students = User.query.filter_by(role='student', tenant_id=current_user.tenant_id).all()
        for st in students:
            notif = Notification(
                user_id=st.id,
                title=f"⚡ LIVE QUIZ BATTLE: {title}",
                content=f"Instructor {current_user.name} opened a Live Quiz Arena! Enter Game PIN {pin} to compete.",
                type='info'
            )
            db.session.add(notif)

        db.session.commit()

        flash(f"⚡ Live Quiz Battle Created! Game PIN: {pin} (Timer: {timer}s)", "success")
        return redirect(url_for('instructor.host_battle_lobby', session_id=session.id))
    
    sessions = QuizBattleSession.query.filter_by(host_id=current_user.id).order_by(QuizBattleSession.created_at.desc()).all()
    return render_template('instructor/quiz_battle_host.html', active_page='battle', sessions=sessions)

@instructor_bp.route('/quiz-battle/host/lobby/<int:session_id>')
@login_required
@role_required('instructor')
def host_battle_lobby(session_id):
    from ..models import QuizBattleSession, QuizBattleParticipant, QuizBattleQuestion, QuizBattleSubmission
    session = QuizBattleSession.query.get_or_404(session_id)
    if session.host_id != current_user.id:
        abort(403)
    
    participants = QuizBattleParticipant.query.filter_by(session_id=session.id).order_by(QuizBattleParticipant.score.desc()).all()
    questions = QuizBattleQuestion.query.filter_by(session_id=session.id).order_by(QuizBattleQuestion.order_num.asc()).all()
    
    # Active question text
    active_q = None
    if session.current_question > 0 and session.current_question <= len(questions):
        active_q = questions[session.current_question - 1]

    # Calculate choice distribution live stats
    opt_a_count = QuizBattleSubmission.query.filter_by(session_id=session.id, question_order=session.current_question, selected_option='a').count()
    opt_b_count = QuizBattleSubmission.query.filter_by(session_id=session.id, question_order=session.current_question, selected_option='b').count()
    opt_c_count = QuizBattleSubmission.query.filter_by(session_id=session.id, question_order=session.current_question, selected_option='c').count()
    opt_d_count = QuizBattleSubmission.query.filter_by(session_id=session.id, question_order=session.current_question, selected_option='d').count()
    total_votes = opt_a_count + opt_b_count + opt_c_count + opt_d_count

    vote_counts = {
        'a': opt_a_count,
        'b': opt_b_count,
        'c': opt_c_count,
        'd': opt_d_count,
        'total': total_votes
    }

    return render_template('instructor/quiz_battle_arena.html', 
                           active_page='battle', 
                           session=session, 
                           participants=participants, 
                           questions=questions, 
                           active_q=active_q,
                           vote_counts=vote_counts)

@instructor_bp.route('/quiz-battle/host/lobby/<int:session_id>/start', methods=['POST'])
@login_required
@role_required('instructor')
def start_quiz_battle(session_id):
    from datetime import datetime
    from ..models import QuizBattleSession
    session = QuizBattleSession.query.get_or_404(session_id)
    if session.host_id != current_user.id:
        abort(403)
    
    session.status = 'active'
    session.current_question = 1
    session.question_start_time = datetime.utcnow()
    db.session.commit()
    flash(f"🚀 LIVE GAME STARTED! Timer: {session.timer_seconds}s per question.", "success")
    return redirect(url_for('instructor.host_battle_lobby', session_id=session.id))

@instructor_bp.route('/quiz-battle/host/lobby/<int:session_id>/add-question', methods=['POST'])
@login_required
@role_required('instructor')
def add_battle_question(session_id):
    from ..models import QuizBattleSession, QuizBattleQuestion
    session = QuizBattleSession.query.get_or_404(session_id)
    if session.host_id != current_user.id:
        abort(403)
    
    q_text = request.form.get('question_text')
    opt_a = request.form.get('option_a')
    opt_b = request.form.get('option_b')
    opt_c = request.form.get('option_c')
    opt_d = request.form.get('option_d')
    correct = request.form.get('correct_option', 'a').lower()

    if q_text and opt_a and opt_b and opt_c and opt_d:
        count = QuizBattleQuestion.query.filter_by(session_id=session.id).count()
        q = QuizBattleQuestion(
            session_id=session.id,
            order_num=count + 1,
            question_text=q_text,
            option_a=opt_a,
            option_b=opt_b,
            option_c=opt_c,
            option_d=opt_d,
            correct_option=correct
        )
        session.total_questions = count + 1
        db.session.add(q)
        db.session.commit()
        flash(f"✅ Question #{count + 1} added successfully!", "success")
    
    return redirect(url_for('instructor.host_battle_lobby', session_id=session.id))

@instructor_bp.route('/quiz-battle/host/lobby/<int:session_id>/ai-generate', methods=['POST'])
@login_required
@role_required('instructor')
def ai_generate_battle_questions(session_id):
    from ..models import QuizBattleSession, QuizBattleQuestion
    session = QuizBattleSession.query.get_or_404(session_id)
    if session.host_id != current_user.id:
        abort(403)
    
    topic = request.form.get('topic', 'General Programming & Tech')
    
    # Auto-generate 3 AI Questions
    ai_qs = [
        {
            "q": f"Which of the following is a core concept in {topic}?",
            "a": "Data Structures", "b": "CSS Selectors", "c": "SQL Triggers", "d": "HTTP Cookies", "correct": "a"
        },
        {
            "q": f"What is the best practice when handling errors in {topic}?",
            "a": "Ignore Exceptions", "b": "Try-Catch Error Handling", "c": "Global Fallbacks", "d": "Memory Dumps", "correct": "b"
        },
        {
            "q": f"What is the worst-case time complexity of Bubble Sort?",
            "a": "O(1)", "b": "O(N log N)", "c": "O(N^2)", "d": "O(N)", "correct": "c"
        }
    ]
    
    count = QuizBattleQuestion.query.filter_by(session_id=session.id).count()
    for idx, item in enumerate(ai_qs):
        q = QuizBattleQuestion(
            session_id=session.id,
            order_num=count + idx + 1,
            question_text=item["q"],
            option_a=item["a"],
            option_b=item["b"],
            option_c=item["c"],
            option_d=item["d"],
            correct_option=item["correct"]
        )
        db.session.add(q)
    
    session.total_questions = count + len(ai_qs)
    db.session.commit()
    flash(f"✨ AI generated 3 new questions for '{topic}'!", "success")
    return redirect(url_for('instructor.host_battle_lobby', session_id=session.id))

@instructor_bp.route('/quiz-battle/host/lobby/<int:session_id>/next', methods=['POST'])
@login_required
@role_required('instructor')
def next_battle_question(session_id):
    from datetime import datetime
    from ..models import QuizBattleSession, QuizBattleQuestion
    session = QuizBattleSession.query.get_or_404(session_id)
    if session.host_id != current_user.id:
        abort(403)
    
    total = QuizBattleQuestion.query.filter_by(session_id=session.id).count()
    if total == 0:
        total = session.total_questions

    if session.current_question < total:
        session.current_question += 1
        session.status = 'active'
        session.question_start_time = datetime.utcnow()
        flash(f"⚡ Question {session.current_question} is now LIVE!", "info")
    else:
        session.status = 'finished'
        flash("🏆 Live Quiz Battle Completed! Winner crowned on the podium.", "success")
    
    db.session.commit()
    return redirect(url_for('instructor.host_battle_lobby', session_id=session.id))


@instructor_bp.route('/schedules', methods=['GET', 'POST'])
@login_required
@role_required('instructor')
def schedules():
    my_courses = Course.query.filter_by(instructor_id=current_user.id).all()
    if not my_courses:
        course1 = Course(
            title="Introduction to Computer Science",
            description="Foundations of programming, algorithms, and computational thinking.",
            instructor_id=current_user.id,
            tenant_id=current_user.tenant_id
        )
        course2 = Course(
            title="Web Application Development",
            description="Building high-performance modern web apps with HTML, CSS, and JS.",
            instructor_id=current_user.id,
            tenant_id=current_user.tenant_id
        )
        db.session.add(course1)
        db.session.add(course2)
        db.session.commit()
        my_courses = [course1, course2]
    my_course_ids = [c.id for c in my_courses]

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'propose_schedule':
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

            tot_classes = CourseSchedule.calculate_total_classes(s_date, e_date, days_of_week)

            sched = CourseSchedule(
                course_id=course_id,
                instructor_id=current_user.id,
                title=title,
                days_of_week=days_of_week,
                start_time=start_time,
                end_time=end_time,
                start_date=s_date,
                end_date=e_date,
                total_classes=tot_classes,
                completed_classes=0,
                room_or_link=room_or_link,
                status='pending_approval',  # Requires Admin Approval
                created_by_id=current_user.id
            )
            db.session.add(sched)
            db.session.commit()

            # Create notification for admin
            if current_user.tenant_id:
                admins = User.query.filter_by(role='admin', tenant_id=current_user.tenant_id).all()
            else:
                admins = User.query.filter_by(role='admin', tenant_id=current_user.tenant_id).all()
            for adm in admins:
                db.session.add(Notification(
                    user_id=adm.id,
                    title="New Schedule Approval Request",
                    content=f"Instructor {current_user.name} submitted a new schedule proposal '{title}' for Admin review.",
                    type="info"
                ))
            db.session.commit()

            flash(f"📩 Schedule '{title}' submitted successfully! Pending Admin Approval.", "success")
            return redirect(url_for('instructor.schedules'))

        elif action == 'edit_schedule':
            sched_id = request.form.get('schedule_id')
            sched = CourseSchedule.query.get_or_404(sched_id)
            if sched.instructor_id != current_user.id and sched.course.instructor_id != current_user.id:
                flash("❌ Unauthorized access to this schedule.", "error")
                return redirect(url_for('instructor.schedules'))
                
            course_id = request.form.get('course_id')
            title = request.form.get('title', '').strip()
            days_of_week = request.form.get('days_of_week', '').strip()
            start_time = request.form.get('start_time', '').strip()
            end_time = request.form.get('end_time', '').strip()
            start_date_str = request.form.get('start_date')
            end_date_str = request.form.get('end_date')
            room_or_link = request.form.get('room_or_link', '').strip()

            s_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else sched.start_date
            e_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else sched.end_date
            
            sched.course_id = course_id
            sched.title = title
            sched.days_of_week = days_of_week
            sched.start_time = start_time
            sched.end_time = end_time
            sched.start_date = s_date
            sched.end_date = e_date
            sched.room_or_link = room_or_link
            sched.total_classes = CourseSchedule.calculate_total_classes(s_date, e_date, days_of_week)
            sched.status = 'pending_approval'
            
            db.session.commit()
            flash(f"✏️ Schedule '{title}' updated successfully and re-submitted for Admin Approval!", "success")
            return redirect(url_for('instructor.schedules'))

        elif action == 'delete_schedule':
            sched_id = request.form.get('schedule_id')
            sched = CourseSchedule.query.get_or_404(sched_id)
            if sched.instructor_id != current_user.id and sched.course.instructor_id != current_user.id:
                flash("❌ Unauthorized access.", "error")
                return redirect(url_for('instructor.schedules'))
                
            db.session.delete(sched)
            db.session.commit()
            flash("🗑️ Schedule deleted successfully!", "success")
            return redirect(url_for('instructor.schedules'))

    my_schedules = CourseSchedule.query.filter(
        (CourseSchedule.instructor_id == current_user.id) | (CourseSchedule.course_id.in_(my_course_ids))
    ).order_by(CourseSchedule.created_at.desc()).all() if my_course_ids else []

    return render_template(
        'instructor/schedules.html',
        courses=my_courses,
        schedules=my_schedules
    )


@instructor_bp.route('/events', methods=['GET', 'POST'])
@login_required
@role_required('instructor')
def events():
    my_courses = Course.query.filter_by(instructor_id=current_user.id).all()
    my_course_ids = [c.id for c in my_courses]

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'propose_event':
            title = request.form.get('title').strip()
            event_type = request.form.get('event_type', 'workshop')
            course_id = request.form.get('course_id')
            course_id = int(course_id) if course_id and course_id != 'all' else None
            date_str = request.form.get('event_date')
            start_time = request.form.get('start_time', '02:00 PM').strip()
            end_time = request.form.get('end_time', '04:00 PM').strip()
            location_or_link = request.form.get('location_or_link', 'Online Room').strip()
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
                status='pending_approval'  # Requires Admin Approval
            )
            db.session.add(ev)
            db.session.commit()

            # Notify Admin
            if current_user.tenant_id:
                admins = User.query.filter_by(role='admin', tenant_id=current_user.tenant_id).all()
            else:
                admins = User.query.filter_by(role='admin', tenant_id=current_user.tenant_id).all()
            for adm in admins:
                db.session.add(Notification(
                    user_id=adm.id,
                    title="New Event Review Request",
                    content=f"Instructor {current_user.name} uploaded event '{title}' awaiting Admin approval.",
                    type="info"
                ))
            db.session.commit()

            flash(f"📩 Event '{title}' submitted! Sent to Admin for review & publishing.", "success")
            return redirect(url_for('instructor.events'))

        elif action == 'edit_event':
            event_id = request.form.get('event_id')
            ev = Event.query.get(event_id)
            if ev and ev.created_by_id == current_user.id:
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
                db.session.commit()
                flash(f"✏️ Event '{ev.title}' updated successfully!", "success")
            return redirect(url_for('instructor.events'))

        elif action == 'delete_event':
            event_id = request.form.get('event_id')
            ev = Event.query.get(event_id)
            if ev and ev.created_by_id == current_user.id:
                db.session.delete(ev)
                db.session.commit()
                flash("🗑️ Event deleted.", "info")
            return redirect(url_for('instructor.events'))

    my_events = Event.query.filter(
        (Event.created_by_id == current_user.id) | (Event.course_id.in_(my_course_ids) if my_course_ids else False)
    ).order_by(Event.event_date.asc()).all()

    today = datetime.utcnow().date()
    expired_any = False
    for ev in my_events:
        if ev.event_date < today and ev.status not in ('expired', 'rejected'):
            ev.status = 'expired'
            expired_any = True
    if expired_any:
        db.session.commit()

    active_my_events = [e for e in my_events if e.status != 'expired']
    expired_my_events = [e for e in my_events if e.status == 'expired']
    all_published_events = Event.query.filter_by(status='published', tenant_id=current_user.tenant_id).order_by(Event.event_date.asc()).all()

    return render_template(
        'instructor/events.html',
        courses=my_courses,
        my_events=active_my_events,
        expired_events=expired_my_events,
        all_published_events=all_published_events
    )


@instructor_bp.route('/attendance', methods=['GET', 'POST'])
@login_required
@role_required('instructor')
def attendance():
    from ..utils import auto_mark_absent_for_closed_sessions
    auto_mark_absent_for_closed_sessions()

    my_courses = Course.query.filter_by(instructor_id=current_user.id).all()
    my_course_ids = [c.id for c in my_courses]

    selected_course_id = request.args.get('course_id', type=int)
    if not selected_course_id and my_courses:
        selected_course_id = my_courses[0].id

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'create_session':
            course_id = request.form.get('course_id')
            title = request.form.get('title', 'Class Lecture Attendance').strip()
            pin_code = request.form.get('pin_code', '').strip()
            session_date_str = request.form.get('session_date', '').strip()

            if int(course_id) not in my_course_ids:
                flash("Unauthorized course access.", "error")
                return redirect(url_for('instructor.attendance'))

            sess_date = datetime.utcnow().date()
            if session_date_str:
                try:
                    sess_date = datetime.strptime(session_date_str, '%Y-%m-%d').date()
                except Exception:
                    pass

            if not pin_code:
                import random
                pin_code = str(random.randint(100000, 999999))

            sess = AttendanceSession(
                course_id=course_id,
                instructor_id=current_user.id,
                title=title,
                session_date=sess_date,
                pin_code=pin_code,
                status='open'
            )
            db.session.add(sess)
            db.session.commit()
            flash(f"✅ Attendance Session Created! PIN Code: {pin_code}", "success")
            return redirect(url_for('instructor.attendance', course_id=course_id))

        elif action == 'close_session':
            session_id = request.form.get('session_id')
            sess = AttendanceSession.query.get(session_id)
            if sess and sess.course_id in my_course_ids:
                sess.status = 'closed'
                db.session.commit()
                auto_mark_absent_for_closed_sessions(session_id=sess.id)
                flash("🔴 Attendance session closed. Unmarked enrolled students auto-marked ABSENT.", "info")
            return redirect(url_for('instructor.attendance'))

        elif action == 'mark_student_attendance':
            course_id = request.form.get('course_id')
            roll_number = request.form.get('roll_number', '').strip()
            rec_status = request.form.get('status', 'present')

            enr = Enrollment.query.filter((Enrollment.roll_number == roll_number) | (Enrollment.id == roll_number)).first()
            student = enr.user if enr else User.query.filter((User.roll_number == roll_number) | (User.id == roll_number)).first()

            if not student:
                flash(f"⚠️ Student with Roll No '{roll_number}' not found!", "error")
                return redirect(url_for('instructor.attendance'))

            target_date = datetime.utcnow().date()
            sess = AttendanceSession.query.filter_by(course_id=course_id, session_date=target_date).first()
            if not sess:
                sess = AttendanceSession(
                    course_id=course_id,
                    instructor_id=current_user.id,
                    title=f"Class Attendance - {target_date}",
                    session_date=target_date,
                    pin_code="INST-MANUAL",
                    status='open'
                )
                db.session.add(sess)
                db.session.commit()

            rec = AttendanceRecord.query.filter_by(session_id=sess.id, user_id=student.id).first()
            if not rec:
                rec = AttendanceRecord(
                    session_id=sess.id,
                    user_id=student.id,
                    status=rec_status,
                    method='instructor_override',
                    marked_at=datetime.utcnow()
                )
                db.session.add(rec)
            else:
                rec.status = rec_status
                rec.method = 'instructor_override'

            db.session.commit()
            flash(f"✅ Marked {rec_status.upper()} for student {student.name}!", "success")
            return redirect(url_for('instructor.attendance', course_id=course_id))

    # Calculate Student Rosters & Telemetry per course
    course_rosters = []
    for c in my_courses:
        enrollments = Enrollment.query.filter_by(course_id=c.id).all()
        sessions = AttendanceSession.query.filter_by(course_id=c.id).all()
        total_sess_count = len(sessions)
        session_ids = [s.id for s in sessions]

        students_telemetry = []
        for enr in enrollments:
            st = enr.user
            roll_no = enr.get_roll_number()
            records = AttendanceRecord.query.filter(
                AttendanceRecord.session_id.in_(session_ids),
                AttendanceRecord.user_id == st.id
            ).all() if session_ids else []

            p_count = sum(1 for r in records if r.status == 'present')
            a_count = sum(1 for r in records if r.status == 'absent')
            l_count = sum(1 for r in records if r.status in ['late', 'excused'])

            rate = round((p_count / total_sess_count * 100)) if total_sess_count > 0 else 100

            students_telemetry.append({
                'user': st,
                'enrollment': enr,
                'roll_number': roll_no,
                'present_count': p_count,
                'absent_count': a_count,
                'leave_count': l_count,
                'total_sessions': total_sess_count,
                'rate': rate
            })

        course_rosters.append({
            'course': c,
            'students': students_telemetry,
            'total_enrolled': len(enrollments),
            'sessions': sessions
        })

    active_sessions = AttendanceSession.query.filter(
        AttendanceSession.instructor_id == current_user.id,
        AttendanceSession.status == 'open'
    ).all()

    return render_template(
        'instructor/attendance.html',
        my_courses=my_courses,
        course_rosters=course_rosters,
        active_sessions=active_sessions,
        selected_course_id=selected_course_id
    )
@instructor_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@role_required('instructor')
def profile():
    import os
    from datetime import datetime
    from werkzeug.utils import secure_filename
    from flask import current_app

    if request.method == 'POST':
        new_name = request.form.get('full_name', '').strip()
        new_email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        bio = request.form.get('bio', '').strip()
        current_password = request.form.get('current_password', '').strip()
        new_password = request.form.get('new_password', '').strip()

        # Check email uniqueness if changed
        if new_email != current_user.email:
            existing = User.query.filter_by(email=new_email).first()
            if existing:
                flash("⚠️ This email address is already in use by another user.", "error")
                return redirect(url_for('instructor.profile'))

        # Handle Profile Picture Upload
        pic_file = request.files.get('avatar')
        if pic_file and pic_file.filename:
            filename = secure_filename(f"avatar_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{pic_file.filename}")
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'avatars')
            os.makedirs(upload_folder, exist_ok=True)
            pic_file.save(os.path.join(upload_folder, filename))
            current_user.avatar_url = f"/static/uploads/avatars/{filename}"

        current_user.name = new_name
        current_user.email = new_email
        current_user.phone = phone
        current_user.bio = bio
        
        # Handle password change with old password verification
        if new_password:
            if not current_password or not current_user.check_password(current_password):
                flash("⚠️ Incorrect Current Password! Please enter your valid current password to authorize this change.", "error")
                return redirect(url_for('instructor.profile'))
            current_user.set_password(new_password)
        
        db.session.commit()
        flash("🎉 Profile details updated successfully!", "success")
        return redirect(url_for('instructor.profile'))

    return render_template('instructor/profile.html')

@instructor_bp.route('/assignments', methods=['GET', 'POST'])
@login_required
@role_required('instructor')
def assignments():
    courses = Course.query.filter_by(instructor_id=current_user.id).all()
    course_ids = [c.id for c in courses]
    
    if request.method == 'POST':
        course_id = request.form.get('course_id', type=int)
        title = request.form.get('title')
        content_type = request.form.get('content_type', 'lab') # 'lab' or 'text'
        content = request.form.get('content')
        duration = request.form.get('duration', default=10, type=int)
        due_date_str = request.form.get('due_date')
        
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                due_date = None
        
        if course_id and title and content_type:
            course = Course.query.get_or_404(course_id)
            if course.instructor_id != current_user.id:
                abort(403)
                
            order = len(course.lessons) + 1
            new_lesson = Lesson(
                course_id=course.id,
                order=order,
                title=title,
                content_type=content_type,
                content=content,
                duration=duration,
                due_date=due_date
            )
            db.session.add(new_lesson)
            db.session.commit()
            flash(f"Assignment '{title}' created successfully.", "success")
            return redirect(url_for('instructor.assignments'))
            
    assignments = Lesson.query.filter(Lesson.course_id.in_(course_ids), Lesson.content_type.in_(['lab', 'text'])).all() if course_ids else []
    return render_template('instructor/assignments.html', courses=courses, assignments=assignments, active_page='assignments')

@instructor_bp.route('/assignments/<int:lesson_id>/delete', methods=['POST'])
@login_required
@role_required('instructor')
def delete_assignment(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    if lesson.course.instructor_id != current_user.id:
        abort(403)
    db.session.delete(lesson)
    db.session.commit()
    flash("Assignment deleted successfully.", "success")
    return redirect(url_for('instructor.assignments'))

@instructor_bp.route('/assignments/<int:lesson_id>/edit', methods=['POST'])
@login_required
@role_required('instructor')
def edit_assignment(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    if lesson.course.instructor_id != current_user.id:
        abort(403)
        
    title = request.form.get('title')
    content = request.form.get('content')
    duration = request.form.get('duration', default=10, type=int)
    due_date_str = request.form.get('due_date')
    
    if title:
        lesson.title = title
        lesson.content = content
        lesson.duration = duration
        if due_date_str:
            try:
                lesson.due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                lesson.due_date = None
        else:
            lesson.due_date = None
            
        db.session.commit()
        flash("Assignment updated successfully.", "success")
        
    return redirect(url_for('instructor.assignments'))


@instructor_bp.route('/resources', methods=['GET', 'POST'])
@login_required
@role_required('instructor')
def resources():
    db.create_all()
    # Fetch instructor's taught courses
    courses = Course.query.filter_by(instructor_id=current_user.id).all()
    if not courses:
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
            flash("❌ Please select a course and enter a resource title.", "danger")
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
            flash(f"✅ Resource '{title}' published successfully for your students!", "success")
            return redirect(url_for('instructor.resources'))

    course_ids = [c.id for c in courses]
    resources_list = CourseResource.query.filter(CourseResource.course_id.in_(course_ids)).order_by(CourseResource.created_at.desc()).all() if course_ids else []
    return render_template('instructor/resources.html', resources=resources_list, courses=courses, active_page='resources')


@instructor_bp.route('/resources/<int:id>/edit', methods=['POST'])
@login_required
@role_required('instructor')
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
    return redirect(url_for('instructor.resources'))


@instructor_bp.route('/resources/<int:id>/delete', methods=['POST'])
@login_required
@role_required('instructor')
def delete_resource(id):
    res = CourseResource.query.get_or_404(id)
    db.session.delete(res)
    db.session.commit()
    flash("🗑️ Course resource deleted successfully.", "success")
    return redirect(url_for('instructor.resources'))


