from titan_lms import create_app, db
from titan_lms.models import TeamMember

app = create_app()
with app.app_context():
    existing_names = [m.name for m in TeamMember.query.all()]
    print('Existing members:', existing_names)

    new_members = [
        {'name': 'Muhammad Aslam Shaikh', 'designation': 'FOUNDER & CHAIRMAN', 'image_url': '/static/muhammad_aslam_shaikh_portrait.png', 'initials': 'MS', 'order': 2},
        {'name': 'Dr. Sarah Chen', 'designation': 'HEAD OF AI RESEARCH', 'image_url': 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=500', 'initials': 'SC', 'order': 4},
        {'name': 'Marcus Vance', 'designation': 'CHIEF TECHNOLOGY OFFICER', 'image_url': 'https://images.unsplash.com/photo-1560250097-0b93528c311a?w=500', 'initials': 'MV', 'order': 5},
        {'name': 'Ammar Mughal', 'designation': 'LEAD DATA SCIENTIST', 'image_url': '/static/4.jpg', 'initials': 'AM', 'order': 6}
    ]

    for data in new_members:
        if data['name'] not in existing_names:
            m = TeamMember(**data)
            db.session.add(m)
            print('Added:', data['name'])
    
    db.session.commit()
    print('All Members in DB:', [(m.id, m.name, m.designation) for m in TeamMember.query.all()])
