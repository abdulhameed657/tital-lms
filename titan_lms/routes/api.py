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

@api_bp.route('/notifications/latest')
def notifications_latest():
    if not current_user.is_authenticated:
        return jsonify({"authenticated": False, "notifications": []})
        
    notifs = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(10).all()
    
    return jsonify({
        "authenticated": True,
        "unread_count": Notification.query.filter_by(user_id=current_user.id, is_read=False).count(),
        "notifications": [{
            "id": n.id,
            "title": n.title,
            "content": n.content,
            "is_read": n.is_read,
            "type": getattr(n, 'type', 'info'),
            "link": getattr(n, 'link', '#') or '#',
            "created_at": n.created_at.strftime('%b %d, %H:%M') if n.created_at else ''
        } for n in notifs]
    })

@api_bp.route('/messages/send', methods=['POST'])
def send_live_message():
    from flask import request
    from ..models import User
    
    if not current_user.is_authenticated:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
        
    data = request.get_json(silent=True) or request.form
    recipient_id = data.get('recipient_id')
    content = data.get('content')
    
    if not recipient_id or not content:
        return jsonify({"status": "error", "message": "Recipient and content are required"}), 400
        
    recipient = User.query.get(recipient_id)
    if not recipient:
        return jsonify({"status": "error", "message": "Recipient not found"}), 404
        
    if current_user.role not in ['admin', 'superadmin'] and recipient.role in ['admin', 'superadmin']:
        return jsonify({"status": "error", "message": "Messaging Admins and Superadmins is disabled."}), 403
        
    msg = Message(
        sender_id=current_user.id,
        recipient_id=int(recipient_id),
        content=content
    )
    db.session.add(msg)
    
    notif = Notification(
        user_id=int(recipient_id),
        title="New Inbox Message",
        content=f"You received a message from {current_user.name}.",
        type="info"
    )
    db.session.add(notif)
    db.session.commit()
    
    return jsonify({
        "status": "success",
        "message": {
            "id": msg.id,
            "sender_id": msg.sender_id,
            "recipient_id": msg.recipient_id,
            "content": msg.content,
            "created_at": msg.created_at.strftime('%b %d at %I:%M %p') if msg.created_at else ''
        }
    })

@api_bp.route('/messages/thread/<int:contact_id>')
def get_message_thread(contact_id):
    from ..models import User
    
    if not current_user.is_authenticated:
        return jsonify({"authenticated": False, "messages": []})
        
    contact = User.query.get(contact_id)
    if not contact:
        return jsonify({"status": "error", "message": "Contact not found"}), 404
        
    thread = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.recipient_id == contact_id)) |
        ((Message.sender_id == contact_id) & (Message.recipient_id == current_user.id))
    ).order_by(Message.created_at.asc()).all()
    
    for m in thread:
        if m.recipient_id == current_user.id and not m.is_read:
            m.is_read = True
    db.session.commit()
    
    return jsonify({
        "authenticated": True,
        "contact": {
            "id": contact.id,
            "name": contact.name,
            "role": contact.role
        },
        "messages": [{
            "id": m.id,
            "sender_id": m.sender_id,
            "is_mine": (m.sender_id == current_user.id),
            "content": m.content,
            "created_at": m.created_at.strftime('%b %d at %I:%M %p') if m.created_at else ''
        } for m in thread]
    })


