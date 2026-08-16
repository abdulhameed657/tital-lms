import os
import sys
import traceback

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from titan_lms import create_app, db

app = create_app()

with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        print("DB Init Error:", e)

@app.errorhandler(500)
@app.errorhandler(Exception)
def handle_exception(e):
    tb = traceback.format_exc()
    return f"""
    <div style="font-family: monospace; padding: 25px; background: #0f172a; color: #f87171; border-radius: 12px; margin: 20px;">
        <h2>⚠️ Titan LMS Live Traceback Log</h2>
        <pre style="white-space: pre-wrap; word-break: break-all; background: #1e293b; color: #38bdf8; padding: 15px; border-radius: 8px;">{tb}</pre>
    </div>
    """, 200

handler = app
