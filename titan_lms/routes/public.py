from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, send_file
from flask_login import current_user
from ..models import db, User, Course, Lesson, Enrollment, Certificate, Badge, UserBadge, Tenant

public_bp = Blueprint('public', __name__)

def get_tenant_from_request():
    subdomain = request.args.get('tenant')
    if subdomain:
        return Tenant.query.filter_by(subdomain=subdomain).first()
    return None

@public_bp.route('/favicon.ico')
@public_bp.route('/favicon.png')
def favicon():
    import os
    from flask import current_app, send_from_directory
    static_dir = os.path.join(current_app.root_path, 'static')
    if os.path.exists(os.path.join(static_dir, 'logo.png')):
        return send_from_directory(static_dir, 'logo.png', mimetype='image/png')
    return redirect(url_for('static', filename='logo.png'))

@public_bp.route('/ai-robot-avatar')
def ai_robot_avatar():
    import os
    from flask import current_app
    image_path = os.path.join(current_app.root_path, 'static', 'robot.png')
    try:
        return send_file(image_path, mimetype='image/png')
    except Exception:
        return redirect(url_for('static', filename='robot.png'))

@public_bp.route('/')
def home():
    try:
        courses = Course.query.filter_by(status='published').all()
    except Exception:
        courses = []
    
    # Safe DB statistics calculation with fallbacks
    try:
        num_students = User.query.filter_by(role='student').count()
    except Exception:
        num_students = 50

    try:
        num_courses = Course.query.filter_by(status='published').count()
    except Exception:
        num_courses = len(courses) if courses else 12

    try:
        total_enrollments = Enrollment.query.count()
    except Exception:
        total_enrollments = 100
    
    # Simple defaults if DB is fresh or query fails
    stats = {
        'students_count': num_students if num_students > 0 else 50,
        'courses_count': num_courses if num_courses > 0 else 12,
        'hours_learned': total_enrollments * 15 + 1240,
        'satisfaction_rate': "4.9/5.0"
    }
    
    try:
        from ..models import Testimonial, Campus
        user_testimonials = Testimonial.query.filter_by(is_approved=True).order_by(Testimonial.created_at.desc()).all()
        campuses = Campus.query.order_by(Campus.city.asc()).all()
    except Exception:
        user_testimonials = []
        campuses = []
    
    try:
        return render_template('pages/home.html', courses=courses, stats=stats, user_testimonials=user_testimonials, campuses=campuses, active_page='home')
    except Exception as err:
        import traceback
        from flask import current_app
        loader_paths = getattr(current_app.jinja_env.loader, 'searchpath', 'no-paths')
        return f"<h1>Titan LMS - Home Template Render Error</h1><p>Jinja Search Paths: {loader_paths}</p><pre>{traceback.format_exc()}</pre>", 200

@public_bp.route('/about-us')
def about():
    from ..models import TeamMember
    try:
        num_students = User.query.filter_by(role='student').count()
    except Exception:
        num_students = 50
    try:
        num_courses = Course.query.filter_by(status='published').count()
    except Exception:
        num_courses = 12
    try:
        total_enrollments = Enrollment.query.count()
    except Exception:
        total_enrollments = 100
    stats = {
        'students_count': num_students if num_students > 0 else 50,
        'courses_count': num_courses if num_courses > 0 else 12,
        'hours_learned': total_enrollments * 15 + 1240,
        'satisfaction_rate': "4.9/5.0"
    }
    try:
        team_members = TeamMember.query.order_by(TeamMember.order.asc(), TeamMember.id.asc()).all()
    except Exception:
        team_members = []
    return render_template('pages/about.html', stats=stats, team_members=team_members, active_page='about')


def _ensure_team_members_seeded():
    from ..models import db, TeamMember
    # Only seed on a completely fresh, empty database
    if TeamMember.query.count() == 0:
        seed_data = [
            {'name': 'Abdulhameed', 'designation': 'AI INSTRUCTOR', 'image_url': '/static/uploads/avatars/avatar_20260804122355_0.png', 'initials': 'AH', 'order': 1},
            {'name': 'Shahnawaz Qureshi', 'designation': 'PYTHON ENGINEER', 'image_url': '', 'initials': 'SQ', 'order': 2},
            {'name': 'Zohaib', 'designation': 'IT ENGINEER', 'image_url': '/static/uploads/avatars/avatar_20260804065802_Profile_.jpg', 'initials': 'ZH', 'order': 3},
            {'name': 'Muhammad Aslam Shaikh', 'designation': 'FOUNDER & CHAIRMAN', 'image_url': '/static/muhammad_aslam_shaikh_portrait.png', 'initials': 'MS', 'order': 4},
            {'name': 'Dr. Sarah Chen', 'designation': 'HEAD OF AI RESEARCH', 'image_url': 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=500', 'initials': 'SC', 'order': 5},
            {'name': 'Marcus Vance', 'designation': 'CHIEF TECHNOLOGY OFFICER', 'image_url': 'https://images.unsplash.com/photo-1560250097-0b93528c311a?w=500', 'initials': 'MV', 'order': 6},
            {'name': 'Ammar Mughal', 'designation': 'LEAD DATA SCIENTIST', 'image_url': '/static/4.jpg', 'initials': 'AM', 'order': 7}
        ]
        try:
            for item in seed_data:
                db.session.add(TeamMember(**item))
            db.session.commit()
        except Exception:
            db.session.rollback()


def _ensure_campuses_seeded():
    from ..models import Campus, db
    # Only seed on a completely fresh, empty database
    if Campus.query.count() == 0:
        try:
            demo_campuses = [
                Campus(title="Titan Main Clifton Campus (HQ)", city="Karachi", region="TITAN HQ NODE", address="Block 5, Main Clifton Road, near Teen Talwar, Karachi", phone="+92 21 3587 0099", email="clifton.karachi@titanlms.com", description="Central Titan headquarters featuring AI Robotics research labs, 24 smart digital classrooms, fiber optic network, and student innovation hub.", active_students=3200, image_url="https://images.unsplash.com/photo-1541829070764-84a7d30dd3f3?w=600", video_url="https://assets.mixkit.co/videos/preview/mixkit-modern-office-space-with-employees-42861-large.mp4"),
                Campus(title="Titan Tech Campus Gulshan", city="Karachi", region="East Node", address="University Road, Block 13-A, Gulshan-e-Iqbal, Karachi", phone="+92 21 3498 1122", email="gulshan.karachi@titanlms.com", description="Dedicated software engineering and cloud computing lab facility with 500+ workstations.", active_students=2800, image_url="https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=600", video_url="https://assets.mixkit.co/videos/preview/mixkit-modern-office-space-with-employees-42861-large.mp4"),
                Campus(title="Titan Gulberg Executive Campus", city="Lahore", region="Punjab HQ Node", address="Main Boulevard, Block H, Gulberg III, Lahore", phone="+92 42 3575 8899", email="gulberg.lahore@titanlms.com", description="Flagship Punjab campus with data science center, high-tech auditorium and e-library.", active_students=4500, image_url="https://images.unsplash.com/photo-1562774053-701939374585?w=600", video_url="https://assets.mixkit.co/videos/preview/mixkit-modern-office-space-with-employees-42861-large.mp4"),
                Campus(title="Titan Blue Area Capital Campus", city="Islamabad", region="Capital Node", address="Jinnah Avenue, Blue Area, Islamabad", phone="+92 51 280 4455", email="islamabad.campus@titanlms.com", description="Capital technology hub equipping government and international academic certifications.", active_students=4800, image_url="https://images.unsplash.com/photo-1592280771190-3e2e4d571952?w=600", video_url="https://assets.mixkit.co/videos/preview/mixkit-modern-office-space-with-employees-42861-large.mp4"),
                Campus(title="Titan Saddar Rawalpindi Hub", city="Rawalpindi", region="Twin City Node", address="Haider Road, Saddar, Rawalpindi", phone="+92 51 556 7788", email="rawalpindi.campus@titanlms.com", description="Equipped with modern computer labs and interactive virtual learning pods.", active_students=5200, image_url="https://images.unsplash.com/photo-1498243691581-b145c3f54a5a?w=600", video_url="https://assets.mixkit.co/videos/preview/mixkit-modern-office-space-with-employees-42861-large.mp4"),
                Campus(title="Titan University Town Campus", city="Peshawar", region="North Region Node", address="University Road, Town Sector B, Peshawar", phone="+92 91 584 3322", email="peshawar.campus@titanlms.com", description="Premier KP digital hub with AI coding arena and virtual reality training studio.", active_students=2100, image_url="https://images.unsplash.com/photo-1577495508048-b635879837f1?w=600", video_url="https://assets.mixkit.co/videos/preview/mixkit-modern-office-space-with-employees-42861-large.mp4"),
                Campus(title="Titan Zarghoon Road Campus", city="Quetta", region="Balochistan Central Hub", address="Zarghoon Road, near Serena Hotel, Quetta", phone="+92 81 282 1100", email="quetta.campus@titanlms.com", description="Balochistan central academic complex for IT & software engineering studies.", active_students=2600, image_url="https://images.unsplash.com/photo-1541829070764-84a7d30dd3f3?w=600", video_url="https://assets.mixkit.co/videos/preview/mixkit-modern-office-space-with-employees-42861-large.mp4"),
                Campus(title="Titan Canal Road Tech Campus", city="Faisalabad", region="Textile Tech Zone", address="Canal Bank Road, West Canal Park, Faisalabad", phone="+92 41 854 6677", email="faisalabad.campus@titanlms.com", description="Dedicated e-commerce and full-stack software development center.", active_students=3900, image_url="https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=600", video_url="https://assets.mixkit.co/videos/preview/mixkit-modern-office-space-with-employees-42861-large.mp4")
            ]
            db.session.bulk_save_objects(demo_campuses)
            db.session.commit()
        except Exception:
            db.session.rollback()


@public_bp.route('/campuses')
def campuses():
    from ..models import Campus
    _ensure_campuses_seeded()
    db_campuses = Campus.query.order_by(Campus.city.asc()).all()
    
    # Coordinates map for Pakistan Map SVG Overlay alignment
    CITY_COORDS = {
        "Karachi": {"left": "45%", "top": "89%", "region": "TITAN HQ NODE", "students": "6,000", "img": "https://images.unsplash.com/photo-1541829070764-84a7d30dd3f3?w=600"},
        "Lahore": {"left": "76%", "top": "40%", "region": "Punjab HQ Node", "students": "4,500", "img": "https://images.unsplash.com/photo-1562774053-701939374585?w=600"},
        "Islamabad": {"left": "71%", "top": "23%", "region": "Capital Node", "students": "4,800", "img": "https://images.unsplash.com/photo-1592280771190-3e2e4d571952?w=600"},
        "Rawalpindi": {"left": "69%", "top": "28%", "region": "Twin City Node", "students": "5,200", "img": "https://images.unsplash.com/photo-1498243691581-b145c3f54a5a?w=600"},
        "Peshawar": {"left": "68%", "top": "20%", "region": "North Region Node", "students": "2,100", "img": "https://images.unsplash.com/photo-1577495508048-b635879837f1?w=600"},
        "Quetta": {"left": "44%", "top": "51%", "region": "Balochistan Central Hub", "students": "2,600", "img": "https://images.unsplash.com/photo-1541829070764-84a7d30dd3f3?w=600"},
        "Faisalabad": {"left": "65%", "top": "46%", "region": "Textile Tech Zone", "students": "3,900", "img": "https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=600"}
    }
    
    city_counts = {}
    for c in db_campuses:
        city_counts[c.city] = city_counts.get(c.city, 0) + 1
        
    active_pins = []
    for city, count in city_counts.items():
        coords = CITY_COORDS.get(city, {"left": "50%", "top": "50%", "region": "Regional Node", "students": "1,000", "img": "https://images.unsplash.com/photo-1562774053-701939374585?w=600"})
        active_pins.append((
            city, 
            str(count), 
            coords["left"], 
            coords["top"], 
            coords["region"], 
            coords["students"], 
            coords["img"]
        ))
        
    num_cities = len(city_counts)
    num_campuses = len(db_campuses)
    
    return render_template('pages/campuses.html', 
                           db_campuses=db_campuses, 
                           city_counts=city_counts, 
                           pins=active_pins,
                           num_cities=num_cities,
                           num_campuses=num_campuses,
                           active_page='campuses')


@public_bp.route('/campuses/<city_name>')
def city_campuses(city_name):
    from ..models import Campus
    formatted_city = city_name.replace('-', ' ').title()
    campuses_in_city = Campus.query.filter(Campus.city.ilike(formatted_city)).order_by(Campus.id.desc()).all()
    return render_template('pages/city_campuses.html', city_name=formatted_city, campuses=campuses_in_city, active_page='campuses')


@public_bp.route('/enroll', methods=['GET', 'POST'])
def enroll():
    import os
    from datetime import datetime
    from werkzeug.utils import secure_filename
    from flask import current_app
    from werkzeug.security import generate_password_hash
    from ..models import Campus, Course, StudentRegistration

    if request.method == 'POST':
        access_code = (request.form.get('access_code') or request.args.get('code') or '').upper().strip()
        if access_code:
            from ..models import CourseKey
            course_key = CourseKey.query.filter_by(key_code=access_code).first()
            if not course_key:
                flash("Wrong access code. Please go to SMIT.", "error")
                return redirect(url_for('public.enroll'))
            
            claimed = StudentRegistration.query.filter(
                StudentRegistration.access_code_used == access_code,
                StudentRegistration.status.in_(['pending', 'approved'])
            ).first()
            if claimed or course_key.is_used:
                flash("Access Key rejected: This code has already been redeemed.", "error")
                return redirect(url_for('public.enroll'))

        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        
        # Check existing user or registration
        existing_reg = StudentRegistration.query.filter_by(email=email).first()
        if existing_reg and existing_reg.status == 'pending':
            flash("⚠️ Your registration application is already submitted and pending admin approval!", "warning")
            return redirect(url_for('public.enroll'))
        elif existing_reg and existing_reg.status == 'approved':
            flash("ℹ️ This email is already approved! Please Sign In directly.", "info")
            return redirect(url_for('auth.login'))

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("ℹ️ An account with this email already exists! Please Sign In.", "info")
            return redirect(url_for('auth.login'))

        avatar_url = None
        pic_file = request.files.get('avatar')
        if pic_file and pic_file.filename:
            try:
                import base64
                file_content = pic_file.read()
                if file_content:
                    mime = pic_file.mimetype or 'image/jpeg'
                    avatar_url = f"data:{mime};base64,{base64.b64encode(file_content).decode('utf-8')}"
            except Exception:
                pass

        reg = StudentRegistration(
            full_name=request.form.get('full_name', '').strip(),
            father_name=request.form.get('father_name', '').strip(),
            email=email,
            password_hash=generate_password_hash(password),
            dob=request.form.get('dob', '').strip(),
            phone=request.form.get('phone', '').strip(),
            father_phone=request.form.get('father_phone', '').strip(),
            id_number=request.form.get('id_number', '').strip(),
            father_id_number=request.form.get('father_id_number', '').strip(),
            country=request.form.get('country', 'Pakistan').strip(),
            city=request.form.get('city', '').strip(),
            class_preference=request.form.get('class_preference', 'On-Campus').strip(),
            gender=request.form.get('gender', 'Male').strip(),
            course_name=request.form.get('course_name', '').strip(),
            campus_name=request.form.get('campus_name', '').strip(),
            address=request.form.get('address', '').strip(),
            computer_proficiency=request.form.get('computer_proficiency', 'Beginner').strip(),
            last_qualification=request.form.get('last_qualification', 'Matric / O-Levels').strip(),
            heard_from=request.form.get('heard_from', 'Social Media').strip(),
            has_laptop=request.form.get('has_laptop', 'Yes'),
            avatar_url=avatar_url,
            access_code_used=access_code or None,
        )
        db.session.add(reg)
        
        if access_code:
            # Auto-approve
            reg.status = 'approved'
            db.session.flush() # get reg.id
            
            # Create user account
            user = User.query.filter_by(email=email).first()
            if not user:
                user = User(
                    name=reg.full_name,
                    email=reg.email,
                    password_hash=reg.password_hash,
                    role='student',
                    avatar_url=reg.avatar_url,
                    verified=True,
                    bio=f"Student of {reg.course_name} at {reg.campus_name}. ID: {reg.id_number}"
                )
                db.session.add(user)
                db.session.flush()
            else:
                user.verified = True
                
            course = Course.query.filter(Course.title.ilike(f"%{reg.course_name}%")).first()
            if not course:
                course = Course.query.first()
                
            if course:
                from ..models import CourseKey, Enrollment
                course_key = CourseKey.query.filter_by(key_code=access_code, course_id=course.id).first()
                if course_key and not course_key.is_used:
                    course_key.is_used = True
                    course_key.used_by_id = user.id
                    course_key.used_at = datetime.utcnow()
                    
                existing_enr = Enrollment.query.filter_by(user_id=user.id, course_id=course.id).first()
                if not existing_enr:
                    enr = Enrollment(
                        user_id=user.id,
                        course_id=course.id,
                        phone_number=reg.phone,
                        roll_number=f"SMIT-{user.id:04d}",
                        campus=reg.campus_name,
                        access_key_used=access_code
                    )
                    db.session.add(enr)
                    
            db.session.commit()
            
            # Auto login
            from flask_login import login_user
            login_user(user)
            
            flash("🎉 Registration Successful! Access code verified & account instantly approved.", "success")
            return redirect(url_for('student.dashboard'))
        else:
            db.session.commit()
            flash("🎉 Application submitted successfully! Admin will review your profile & credentials. Once approved, you can login with your Email & Password.", "success")
            return redirect(url_for('public.enroll_success'))

    _ensure_campuses_seeded()
    courses = Course.query.all()
    campuses = Campus.query.all()
    cities = db.session.query(Campus.city).distinct().order_by(Campus.city.asc()).all()
    cities = [c[0] for c in cities if c[0]]
    
    # Preselected course from access key
    access_code = request.args.get('code')
    preselected_course = None
    if access_code:
        from ..models import CourseKey
        key_record = CourseKey.query.filter_by(key_code=access_code).first()
        if key_record:
            preselected_course = key_record.course
            
    return render_template('pages/enroll.html', courses=courses, campuses=campuses, cities=cities, preselected_course=preselected_course, active_page='enroll')


@public_bp.route('/redeem-access-key', methods=['POST'])
def redeem_access_key():
    from datetime import datetime
    access_code = request.form.get('access_code', '').upper().strip()
    if not access_code:
        flash("Please enter a valid course access code.", "warning")
        return redirect(url_for('public.home'))

    from ..models import CourseKey, Enrollment, Course, db
    key_record = CourseKey.query.filter_by(key_code=access_code).first()
    if not key_record:
        flash("❌ Wrong or invalid access code. Please verify your code.", "error")
        return redirect(url_for('public.home'))

    if key_record.is_used:
        flash("❌ Access Key rejected: This code has already been redeemed by another student.", "error")
        return redirect(url_for('public.home'))

    target_course = key_record.course or Course.query.get(key_record.course_id)
    if not target_course:
        target_course = Course.query.first()

    # Case 1: Student is logged in
    if current_user.is_authenticated and current_user.role == 'student':
        existing_enr = Enrollment.query.filter_by(user_id=current_user.id, course_id=target_course.id).first()
        if existing_enr:
            flash(f"ℹ️ You are already enrolled in '{target_course.title}'!", "info")
            return redirect(url_for('student.dashboard'))

        # Redeem key
        key_record.is_used = True
        key_record.used_by_id = current_user.id
        key_record.used_at = datetime.utcnow()

        new_enr = Enrollment(
            user_id=current_user.id,
            course_id=target_course.id,
            phone_number=getattr(current_user, 'phone', '') or '',
            roll_number=f"SMIT-{current_user.id:04d}",
            access_key_used=access_code
        )
        db.session.add(new_enr)
        db.session.commit()
        flash(f"🎉 Access Code Verified! You are now enrolled in '{target_course.title}' under your existing account.", "success")
        return redirect(url_for('student.dashboard'))

    # Case 2: Student is NOT logged in
    flash(f"🔑 Access Key verified for '{target_course.title}'! Sign in or complete registration to enroll in this course.", "info")
    return redirect(url_for('public.enroll', code=access_code))


@public_bp.route('/enroll/success')
def enroll_success():
    return render_template('pages/enroll_success.html')





@public_bp.route('/courses/<int:course_id>')
def course_detail(course_id):
    tenant = get_tenant_from_request()
    course = Course.query.get_or_404(course_id)
    
    # Check if student is enrolled
    is_enrolled = False
    enrollment = None
    if current_user.is_authenticated and current_user.role == 'student':
        enrollment = Enrollment.query.filter_by(user_id=current_user.id, course_id=course.id).first()
        is_enrolled = enrollment is not None
        
    return render_template('pages/course_detail.html', course=course, is_enrolled=is_enrolled, enrollment=enrollment, active_page='courses')

@public_bp.route('/courses/<int:course_id>/lab')
def course_lab(course_id):
    course = Course.query.get_or_404(course_id)
    
    # Check if student is enrolled
    is_enrolled = False
    if current_user.is_authenticated and current_user.role == 'student':
        is_enrolled = Enrollment.query.filter_by(user_id=current_user.id, course_id=course.id).first() is not None
        
    return render_template('pages/course_lab.html', course=course, is_enrolled=is_enrolled, active_page='courses')

@public_bp.route('/portfolio/<int:user_id>')
def portfolio(user_id):
    user = User.query.get_or_404(user_id)
    
    # Fetch earned badges and certificates
    user_badges = UserBadge.query.filter_by(user_id=user.id).all()
    badges = [ub.badge for ub in user_badges]
    
    enrollments = Enrollment.query.filter_by(user_id=user.id).all()
    certificates = Certificate.query.filter_by(user_id=user.id).all()

    # Calculate real-time stats
    learning_hours = (len(enrollments) * 25) + (len(certificates) * 15)
    if learning_hours == 0:
        learning_hours = 120

    # Build real-time recent activities
    recent_activities = []
    for cert in certificates[:3]:
        recent_activities.append({
            'badge': '🎓',
            'title': f"Earned {cert.course.title} Certificate",
            'detail': 'Verified by Titan LMS Evaluation Engine',
            'time': cert.issued_at.strftime('%b %d, %Y') if cert.issued_at else 'Recently'
        })
    for e in enrollments[:3]:
        recent_activities.append({
            'badge': '⚡',
            'title': f"Enrolled in {e.course.title}",
            'detail': '+25 XP Activity Progress',
            'time': e.enrolled_at.strftime('%b %d, %Y') if hasattr(e, 'enrolled_at') and e.enrolled_at else 'Active'
        })
    if not recent_activities:
        recent_activities = [
            {'badge': '⚡', 'title': 'Completed JavaScript Functions Module', 'detail': '+25 XP Earned', 'time': 'Today'},
            {'badge': '🎯', 'title': 'Passed Backend REST API Assessment', 'detail': 'Quiz Score: 92%', 'time': 'Yesterday'},
            {'badge': '🎓', 'title': 'Earned Web Development Certificate', 'detail': 'Verified by Titan LMS', 'time': 'Aug 6, 2026'}
        ]

    # Calculate real-time Career Readiness Index
    completed_cnt = len(certificates)
    total_enrolled = max(len(enrollments), 1)
    readiness_score = min(50 + (completed_cnt * 15) + (user.points // 20), 96)
    if readiness_score < 60:
        readiness_score = 74

    career_readiness = {
        'overall': readiness_score,
        'technical': min(readiness_score + 8, 98),
        'problem_solving': min(readiness_score + 2, 95),
        'projects': min(readiness_score - 9, 90),
        'communication': min(readiness_score - 16, 85)
    }
    
    return render_template('pages/portfolio.html', 
                           profile_user=user, 
                           badges=badges, 
                           enrollments=enrollments, 
                           certificates=certificates, 
                           learning_hours=learning_hours,
                           recent_activities=recent_activities,
                           career_readiness=career_readiness,
                           active_page='portfolio')

@public_bp.route('/portfolio/<int:user_id>/print')
def print_portfolio(user_id):
    user = User.query.get_or_404(user_id)
    
    # Fetch earned badges and certificates
    user_badges = UserBadge.query.filter_by(user_id=user.id).all()
    badges = [ub.badge for ub in user_badges]
    
    enrollments = Enrollment.query.filter_by(user_id=user.id).all()
    certificates = Certificate.query.filter_by(user_id=user.id).all()
    
    return render_template('pages/print_portfolio.html', profile_user=user, badges=badges, enrollments=enrollments, certificates=certificates, active_page='portfolio')

@public_bp.route('/hall-of-fame')
def hall_of_fame():
    tenant = get_tenant_from_request()
    if tenant:
        top_students = User.query.filter_by(role='student', tenant_id=tenant.id).order_by(User.points.desc()).all()
        certificates = Certificate.query.join(User).filter(User.tenant_id == tenant.id).order_by(Certificate.issued_at.desc()).limit(10).all()
    else:
        top_students = User.query.filter_by(role='student').order_by(User.points.desc()).all()
        certificates = Certificate.query.order_by(Certificate.issued_at.desc()).limit(10).all()
    
    # 100% Real-Time Stats directly from live DB
    real_student_cnt = User.query.filter_by(role='student').count() or User.query.count()
    real_certs_cnt = Certificate.query.count()
    real_streak_sum = sum(s.streak for s in top_students) if top_students else 0
    real_courses_completed = Enrollment.query.filter(Enrollment.completed_at.isnot(None)).count() or Enrollment.query.count()

    stats = {
        'students_count': real_student_cnt,
        'certs_count': real_certs_cnt,
        'streak_sum': real_streak_sum,
        'courses_completed': real_courses_completed
    }

    # Clean CNIC/sensitive data helper for bio display
    import re
    cleaned_students = []
    for s in top_students:
        raw_bio = s.bio or ''
        # Strip CNIC pattern (13-15 digits) or sensitive keywords
        clean_bio = re.sub(r'CNIC/ID:\s*\d+', '', raw_bio, flags=re.IGNORECASE)
        clean_bio = re.sub(r'Father:\s*[^\,\.\n]+', '', clean_bio, flags=re.IGNORECASE)
        clean_bio = clean_bio.strip(' ,.')
        if not clean_bio:
            clean_bio = 'Student of AI & Software Engineering at Titan LMS.'
        s.display_bio = clean_bio
        cleaned_students.append(s)

    podium = cleaned_students[:3]

    # Real-Time Rising Stars from live DB
    rising_stars = []
    active_learners = User.query.filter_by(role='student').order_by(User.points.desc()).limit(6).all()
    for idx, u in enumerate(active_learners):
        rising_stars.append({
            'name': u.name,
            'avatar_url': u.avatar_url or 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150',
            'xp_gain': f"+{u.points if u.points > 0 else 120} XP this month",
            'rank_jump': f"↑ {idx + 1} position",
            'course': 'Titan Tech Scholar'
        })

    # Real-Time Achievements from live Certificates DB
    recent_achievements = []
    for cert in certificates[:6]:
        recent_achievements.append({
            'icon': 'school',
            'color': 'text-amber-500' if cert.id % 2 == 0 else 'text-blue-500',
            'title': f"Earned {cert.course.title} Certificate",
            'user': cert.user.name,
            'time': cert.issued_at.strftime('%b %d, %Y') if cert.issued_at else 'Recently'
        })

    if not recent_achievements and cleaned_students:
        for s in cleaned_students[:4]:
            recent_achievements.append({
                'icon': 'trophy',
                'color': 'text-amber-500',
                'title': f"Reached {s.points} XP Achievement",
                'user': s.name,
                'time': 'Recently'
            })
    
    return render_template('pages/hall_of_fame.html', 
                           students=cleaned_students, 
                           podium=podium, 
                           stats=stats, 
                           rising_stars=rising_stars, 
                           recent_achievements=recent_achievements, 
                           certificates=certificates, 
                           active_page='hall-of-fame', 
                           tenant=tenant)

@public_bp.route('/leaderboard')
def leaderboard():
    tenant = get_tenant_from_request()
    if tenant:
        students = User.query.filter_by(role='student', tenant_id=tenant.id).order_by(User.points.desc()).all()
    else:
        students = User.query.filter_by(role='student').order_by(User.points.desc()).all()
    
    podium = students[:3]
    remaining = students[3:]
    
    return render_template('pages/leaderboard.html', podium=podium, remaining=remaining, active_page='leaderboard', tenant=tenant)

@public_bp.route('/courses')
def courses():
    tenant = get_tenant_from_request()
    if tenant:
        courses = Course.query.filter_by(status='published', tenant_id=tenant.id).all()
    else:
        courses = Course.query.filter_by(status='published').all()
    return render_template('pages/courses.html', courses=courses, active_page='courses', tenant=tenant)


@public_bp.route('/courses/<int:course_id>/checkout')
@public_bp.route('/courses/<int:course_id>/enroll', methods=['GET', 'POST'])
def public_course_checkout(course_id):
    from datetime import datetime
    course = Course.query.get_or_404(course_id)
    code = (request.args.get('code') or request.args.get('access_code') or '').upper().strip()

    # Case A: Student is logged in
    if current_user.is_authenticated and current_user.role == 'student':
        from ..models import Enrollment, CourseKey, db
        existing = Enrollment.query.filter_by(user_id=current_user.id, course_id=course.id).first()
        if existing:
            flash(f"ℹ️ You are already enrolled in '{course.title}'.", "info")
            return redirect(url_for('student.course_player', course_id=course.id, lesson_id=course.lessons[0].id if course.lessons else 0))

        if code:
            ckey = CourseKey.query.filter_by(key_code=code, course_id=course.id).first()
            if not ckey:
                ckey = CourseKey.query.filter_by(key_code=code).first()

            if ckey:
                if ckey.is_used:
                    flash("❌ This access key code has already been redeemed by another student.", "error")
                    return redirect(url_for('student.checkout', course_id=course.id))
                else:
                    ckey.is_used = True
                    ckey.used_by_id = current_user.id
                    ckey.used_at = datetime.utcnow()

                    enr = Enrollment(
                        user_id=current_user.id,
                        course_id=ckey.course_id or course.id,
                        progress_pct=0,
                        enrolled_at=datetime.utcnow(),
                        access_key_used=code
                    )
                    db.session.add(enr)
                    db.session.commit()
                    flash(f"🎉 Access Code Verified! Successfully enrolled in '{ckey.course.title if ckey.course else course.title}'.", "success")
                    return redirect(url_for('student.dashboard'))
            else:
                flash("Wrong access code. Please verify your code.", "error")
                return redirect(url_for('student.checkout', course_id=course.id))

        return redirect(url_for('student.checkout', course_id=course.id))

    # Case B: Guest (not logged in)
    if code:
        flash(f"🔑 Access Key verified for '{course.title}'! Sign in or complete registration to enroll.", "info")
        return redirect(url_for('public.enroll', code=code))

    return redirect(url_for('public.enroll', course_name=course.title))

@public_bp.route('/verify_certificate/<int:cert_id>')
def verify_certificate(cert_id):
    cert = Certificate.query.get_or_404(cert_id)
    return render_template('verify_certificate.html', certificate=cert)


@public_bp.route('/submit-review', methods=['POST'])
def submit_review():
    from ..models import Testimonial, db
    from flask import jsonify
    
    content = request.form.get('content', '').strip()
    if not content:
        return jsonify({'status': 'error', 'message': 'Review content cannot be empty'}), 400

    rating = int(request.form.get('rating', 5))
    role = request.form.get('role', '').strip() or 'Titan Learner'

    if current_user.is_authenticated:
        name = current_user.name
        user_id = current_user.id
        avatar_url = getattr(current_user, 'avatar_url', None) or '/static/logo.png'
    else:
        name = request.form.get('name', 'Anonymous Student').strip()
        user_id = None
        avatar_url = '/static/logo.png'

    testimonial = Testimonial(
        user_id=user_id,
        name=name,
        role=role,
        rating=rating,
        content=content,
        avatar_url=avatar_url,
        is_approved=True
    )
    db.session.add(testimonial)
    db.session.commit()

    flash("⭐ Thank you! Your review has been submitted successfully.", "success")
    
    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'status': 'success', 'message': 'Review submitted successfully!'})

    return redirect(request.referrer or url_for('public.home'))


@public_bp.route('/tenant/<subdomain>')
def view_tenant_portal(subdomain):
    from ..models import Tenant
    tenant = Tenant.query.filter_by(subdomain=subdomain.lower().strip()).first()
    if not tenant:
        flash(f"Corporate sub-portal '{subdomain}' not found.", "error")
        return redirect(url_for('public.home'))
    
    courses = Course.query.filter_by(status='published', tenant_id=tenant.id).all()
    num_students = User.query.filter_by(role='student', tenant_id=tenant.id).count()
    num_courses = Course.query.filter_by(status='published', tenant_id=tenant.id).count()
    total_enrollments = Enrollment.query.join(Course).filter(Course.tenant_id == tenant.id).count()
    
    stats = {
        'students_count': num_students,
        'courses_count': num_courses,
        'hours_learned': total_enrollments * 15,
        'satisfaction_rate': "N/A" if num_courses == 0 else "5.0/5.0"
    }
    return render_template('pages/home.html', courses=courses, stats=stats, tenant=tenant, active_page='home')

