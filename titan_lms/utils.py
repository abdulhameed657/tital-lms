import os
from datetime import datetime

def generate_pdf_certificate(student_name, course_title, issue_date="2026-07-22", verify_code="TITAN-8A9F3C"):
    """
    Generates a premium, verified PDF certificate for the graduate.
    Handles optional fpdf library or outputs a clean vector SVG-embedded PDF.
    """
    try:
        from fpdf import FPDF
        import tempfile

        pdf = FPDF(orientation='L', unit='mm', format='A4')
        pdf.add_page()
        
        # Outer Border
        pdf.set_line_width(1.5)
        pdf.set_draw_color(212, 175, 55) # Gold
        pdf.rect(6, 6, 285, 198)
        
        pdf.set_line_width(0.5)
        pdf.set_draw_color(10, 17, 40)
        pdf.rect(8, 8, 281, 194)
        
        # Header Banner
        pdf.set_fill_color(10, 17, 40)
        pdf.rect(8, 8, 281, 20, 'F')
        
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", style="B", size=16)
        pdf.set_y(13)
        pdf.cell(0, 10, "TITAN ACADEMY OF TECHNOLOGY & ENGINEERING", align="C", ln=True)
        
        pdf.set_y(42)
        pdf.set_text_color(10, 17, 40)
        pdf.set_font("Arial", style="B", size=28)
        pdf.cell(0, 15, "CERTIFICATE OF EXCELLENCE", align="C", ln=True)
        
        pdf.set_text_color(100, 100, 100)
        pdf.set_font("Arial", style="I", size=12)
        pdf.cell(0, 10, "This credential certifies that the student has successfully completed all curriculum requirements of:", align="C", ln=True)
        
        pdf.ln(5)
        pdf.set_text_color(0, 84, 203)
        pdf.set_font("Arial", style="B", size=22)
        pdf.cell(0, 12, str(course_title), align="C", ln=True)
        
        pdf.ln(5)
        pdf.set_text_color(212, 175, 55)
        pdf.set_font("Arial", style="B", size=26)
        pdf.cell(0, 14, str(student_name).upper(), align="C", ln=True)
        
        pdf.set_y(150)
        pdf.set_text_color(10, 17, 40)
        pdf.set_font("Arial", size=10)
        pdf.line(40, 148, 110, 148)
        pdf.line(180, 148, 250, 148)
        pdf.set_x(40)
        pdf.cell(70, 5, "Dean of Computer Science", align="C")
        pdf.set_x(180)
        pdf.cell(70, 5, "Titan Verification Board", align="C")
        
        pdf.set_y(172)
        pdf.set_text_color(115, 119, 134)
        pdf.set_font("Arial", style="B", size=9)
        pdf.cell(0, 5, f"VERIFIED CREDENTIAL ID: {verify_code}", align="C", ln=True)
        pdf.set_font("Arial", size=8)
        pdf.cell(0, 5, f"Issued on {issue_date} | Authenticated via Titan LMS Encryption Systems.", align="C", ln=True)

        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tf:
            tmp_path = tf.name
        pdf.output(tmp_path)
        with open(tmp_path, 'rb') as f:
            pdf_data = f.read()
        try:
            os.remove(tmp_path)
        except Exception:
            pass
        return pdf_data

    except Exception as e:
        # Zero-dependency Vector PDF document generator
        pdf_stream = (
            f"%PDF-1.4\n"
            f"1 0 obj\n<</Type /Catalog /Pages 2 0 R>>\nendobj\n"
            f"2 0 obj\n<</Type /Pages /Kids [3 0 R] /Count 1>>\nendobj\n"
            f"3 0 obj\n<</Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R /F2 5 0 R >> >> /MediaBox [0 0 842 595] /Contents 6 0 R>>\nendobj\n"
            f"4 0 obj\n<</Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold>>\nendobj\n"
            f"5 0 obj\n<</Type /Font /Subtype /Type1 /BaseFont /Helvetica>>\nendobj\n"
            f"6 0 obj\n<</Length 650>>\nstream\n"
            f"BT\n"
            f"/F1 22 Tf\n100 520 Td (TITAN ACADEMY OF TECHNOLOGY & ENGINEERING) Tj\n"
            f"0 -50 Td\n/F1 32 Tf (CERTIFICATE OF EXCELLENCE) Tj\n"
            f"0 -40 Td\n/F2 14 Tf (This credential certifies that the student has completed:) Tj\n"
            f"0 -40 Td\n/F1 24 Tf ({course_title}) Tj\n"
            f"0 -45 Td\n/F1 28 Tf ({student_name.upper()}) Tj\n"
            f"0 -80 Td\n/F2 12 Tf (Dean of Computer Science              Titan Verification Board) Tj\n"
            f"0 -60 Td\n/F1 11 Tf (VERIFIED CREDENTIAL ID: {verify_code}) Tj\n"
            f"0 -20 Td\n/F2 10 Tf (Issued on {issue_date} | Authenticated via Titan LMS) Tj\n"
            f"ET\n"
            f"endstream\nendobj\n"
            f"xref\n0 7\n0000000000 65535 f\n0000000009 00000 n\n0000000056 00000 n\n0000000111 00000 n\n0000000226 00000 n\n0000000300 00000 n\n0000000370 00000 n\n"
            f"trailer\n<</Size 7 /Root 1 0 R>>\nstartxref\n1080\n%%EOF"
        )
        return pdf_stream.encode('latin1')

def auto_mark_absent_for_closed_sessions(session_id=None):
    """
    Automatically closes expired attendance sessions (> 30 minutes or past date)
    and marks 'absent' for all enrolled students who did not check in.
    Admin can subsequently edit or override these absent records anytime.
    """
    from .models import db, AttendanceSession, AttendanceRecord, Enrollment
    from datetime import datetime, timedelta

    if session_id:
        sess_obj = AttendanceSession.query.get(session_id)
        sessions = [sess_obj] if sess_obj else []
    else:
        sessions = AttendanceSession.query.all()

    now = datetime.utcnow()
    for s in sessions:
        if not s:
            continue
        # Auto close open sessions if session_date is past or > 30 minutes (1800 sec) old
        if s.status == 'open':
            elapsed = (now - s.created_at).total_seconds() if s.created_at else 3600
            if s.session_date < now.date() or elapsed >= 1800:
                s.status = 'closed'

        if s.status == 'closed':
            enrollments = Enrollment.query.filter_by(course_id=s.course_id).all()
            for enr in enrollments:
                existing_record = AttendanceRecord.query.filter_by(session_id=s.id, user_id=enr.user_id).first()
                if not existing_record:
                    absent_rec = AttendanceRecord(
                        session_id=s.id,
                        user_id=enr.user_id,
                        status='absent',
                        marked_at=s.created_at or now,
                        method='auto_absent'
                    )
                    db.session.add(absent_rec)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()

