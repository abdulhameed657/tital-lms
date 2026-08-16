import os
if not os.environ.get('GEMINI_API_KEY'):
    os.environ['GEMINI_API_KEY'] = 'AQ.Ab8RN6LG-_gX43KeqjTwECnJoJnRCHCKKkrEY363QMZ3BXn8AA'
    os.environ['GOOGLE_API_KEY'] = 'AQ.Ab8RN6LG-_gX43KeqjTwECnJoJnRCHCKKkrEY363QMZ3BXn8AA'

from titan_lms import create_app, db
from titan_lms.models import User

app = create_app()

with app.app_context():
    # Check if superadmin already exists
    existing = User.query.filter_by(email='superadmin@gmail.com').first()
    if existing:
        print(f"Super Admin already exists! (id={existing.id}, role={existing.role})")
        # Update role to admin if not already
        if existing.role != 'admin':
            existing.role = 'admin'
            db.session.commit()
            print("Role updated to admin.")
        # Update password
        existing.set_password('adminsuper123')
        db.session.commit()
        print("Password updated.")
    else:
        superadmin = User(
            name='Super Admin',
            email='superadmin@gmail.com',
            role='admin',
            verified=True,
            bio='Platform Super Administrator'
        )
        superadmin.set_password('adminsuper123')
        db.session.add(superadmin)
        db.session.commit()
        print(f"Super Admin created successfully!")
        print(f"  Email: superadmin@gmail.com")
        print(f"  Password: adminsuper123")
        print(f"  Role: admin")
        print(f"  ID: {superadmin.id}")
