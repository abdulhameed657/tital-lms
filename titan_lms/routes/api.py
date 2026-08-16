from flask import Blueprint, jsonify
from flask_login import current_user
from ..models import Notification, Message, CourseResource, db
from sqlalchemy import func

api_bp = Blueprint('api', __name__)

@api_bp.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "Titan LMS API"})

@api_bp.route('/heartbeat')
def heartbeat():
    if not current_user.is_authenticated:
        return jsonify({"authenticated": False})
    
    unread_notifs = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    unread_msgs = Message.query.filter_by(recipient_id=current_user.id, is_read=False).count()
    total_resources = CourseResource.query.count()
    total_downloads = db.session.query(func.sum(CourseResource.downloads_count)).scalar() or 0
    
    return jsonify({
        "authenticated": True,
        "unread_notifications": unread_notifs,
        "unread_messages": unread_msgs,
        "total_resources": total_resources,
        "total_downloads": int(total_downloads),
        "user_id": current_user.id
    })
