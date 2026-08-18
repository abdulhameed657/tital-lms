import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from titan_lms import create_app
from titan_lms.models import db, CourseResource, Course, User

app = create_app()

with app.app_context():
    db.create_all()
    print("Database tables created successfully!")

    # Check if resources already exist
    if CourseResource.query.count() == 0:
        courses = Course.query.all()
        admin_user = User.query.filter_by(role='admin').first() or User.query.first()

        if courses and admin_user:
            sample_resources = [
                {
                    "course_id": courses[0].id,
                    "title": "Complete Python & Data Structures Cheat Sheet 2026",
                    "resource_type": "PDF",
                    "file_url": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
                    "external_url": None,
                    "file_size": "2.8 MB",
                    "description": "Comprehensive reference guide covering Python syntax, data structures, complexity analysis, and algorithms.",
                    "downloads_count": 42
                },
                {
                    "course_id": courses[0].id,
                    "title": "Full-Stack Web Starter Kit & Boilerplate",
                    "resource_type": "Code",
                    "file_url": "https://github.com/archive/master.zip",
                    "external_url": "https://github.com",
                    "file_size": "14.5 MB",
                    "description": "Complete source code zip with authentication setup, API routes, database schemas, and Tailwind templates.",
                    "downloads_count": 89
                },
                {
                    "course_id": courses[0].id if len(courses) == 1 else courses[1].id,
                    "title": "Database Architecture & SQL Query Optimization Slides",
                    "resource_type": "Slide",
                    "file_url": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
                    "external_url": None,
                    "file_size": "5.1 MB",
                    "description": "Lecture slides on indexing strategies, B-Trees, transaction isolation levels, and relational modeling.",
                    "downloads_count": 31
                },
                {
                    "course_id": courses[0].id,
                    "title": "Official MDN Web Docs & JavaScript Reference",
                    "resource_type": "Link",
                    "file_url": None,
                    "external_url": "https://developer.mozilla.org",
                    "file_size": "External Link",
                    "description": "Curated link to official developer documentation for modern ES6+ features and Web APIs.",
                    "downloads_count": 115
                },
                {
                    "course_id": courses[0].id if len(courses) == 1 else courses[1].id,
                    "title": "System Design Handbook & Scalability Guide",
                    "resource_type": "Book",
                    "file_url": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
                    "external_url": None,
                    "file_size": "8.4 MB",
                    "description": "Full e-book guide on microservices architecture, message queues, load balancing, and distributed systems.",
                    "downloads_count": 67
                }
            ]

            for r in sample_resources:
                res = CourseResource(
                    tenant_id=courses[0].tenant_id,
                    course_id=r["course_id"],
                    uploader_id=admin_user.id,
                    title=r["title"],
                    resource_type=r["resource_type"],
                    file_url=r["file_url"],
                    external_url=r["external_url"],
                    file_size=r["file_size"],
                    description=r["description"],
                    downloads_count=r["downloads_count"]
                )
                db.session.add(res)
            db.session.commit()
            print("Sample course resources seeded successfully!")
