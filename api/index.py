import os
import sys
import traceback

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from titan_lms import create_app, db
    app = create_app()

    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print("DB Init Error:", e)

except Exception as err:
    err_trace = traceback.format_exc()
    from flask import Flask
    app = Flask(__name__)

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def vercel_debug_catch_all(path):
        return f"""
        <div style="font-family: monospace; padding: 20px; background: #0f172a; color: #f87171; border-radius: 12px; margin: 20px;">
            <h2>⚠️ Titan LMS Vercel Runtime Exception Log</h2>
            <pre style="white-space: pre-wrap; word-break: break-all; background: #1e293b; color: #38bdf8; padding: 15px; rounded: 8px;">{err_trace}</pre>
        </div>
        """, 500
