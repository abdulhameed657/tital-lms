import os
import sys
import traceback

# Add project root directory to sys.path
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from flask import Flask, request, Response

app = Flask(__name__)

_titan_app = None

def get_titan_app():
    global _titan_app
    if _titan_app is None:
        from titan_lms import create_app
        _titan_app = create_app()
    return _titan_app

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def dispatch(path):
    try:
        titan_app = get_titan_app()
        with titan_app.request_context(request.environ):
            return titan_app.full_dispatch_request()
    except Exception:
        err_tb = traceback.format_exc()
        return Response(
            f"""
            <div style="font-family: monospace; padding: 25px; background: #0f172a; color: #f87171; border-radius: 12px; margin: 20px;">
                <h2>⚠️ Titan LMS Vercel Runtime Log</h2>
                <pre style="white-space: pre-wrap; word-break: break-all; background: #1e293b; color: #38bdf8; padding: 15px; border-radius: 8px;">{err_tb}</pre>
            </div>
            """,
            status=200,
            mimetype='text/html'
        )

# WSGI handler for Vercel
handler = app
