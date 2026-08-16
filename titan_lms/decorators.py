from functools import wraps
from flask import abort, redirect, url_for
from flask_login import current_user

def role_required(roles):
    """
    Decorator to restrict access to routes based on user roles.
    Accepts a single role string or a list of role strings.
    """
    if isinstance(roles, str):
        roles = [roles]
        
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            if current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
