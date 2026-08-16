import os
import sys
import urllib.parse

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Werkzeug 3.0+ compatibility monkey patch for Flask-Login and Flask-WTF on Vercel
import werkzeug.urls
if not hasattr(werkzeug.urls, 'url_quote'):
    werkzeug.urls.url_quote = urllib.parse.quote
if not hasattr(werkzeug.urls, 'url_unquote'):
    werkzeug.urls.url_unquote = urllib.parse.unquote
if not hasattr(werkzeug.urls, 'url_encode'):
    werkzeug.urls.url_encode = urllib.parse.urlencode

from titan_lms import create_app, db

app = create_app()

with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        print("DB Init Error:", e)

# Export WSGI handler for Vercel
handler = app
app = app
