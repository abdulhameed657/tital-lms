import os
import sys
import json

# Ensure root workspace is in sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)

from titan_lms import create_app

app = create_app()

@app.route('/api/health')
def health_check():
    return "OK - Titan LMS is Running on Vercel!", 200

@app.route('/api/debug-paths')
def debug_paths():
    """Diagnostic: inspect Vercel container filesystem."""
    result = {
        'cwd': os.getcwd(),
        'api_index_file': os.path.abspath(__file__),
        'root_dir': root_dir,
    }
    
    # What's inside /var/task/titan_lms/?
    titan_pkg = os.path.join(root_dir, 'titan_lms')
    try:
        result['titan_lms_contents'] = sorted(os.listdir(titan_pkg))
    except Exception as e:
        result['titan_lms_contents'] = str(e)
    
    # What's inside /var/task/titan_lms/templates/?
    tpl_dir = os.path.join(titan_pkg, 'templates')
    try:
        result['templates_exists'] = os.path.isdir(tpl_dir)
        result['templates_contents'] = sorted(os.listdir(tpl_dir))
    except Exception as e:
        result['templates_exists'] = False
        result['templates_contents'] = str(e)
    
    # What's inside /var/task/titan_lms/templates/public/?
    pub_dir = os.path.join(tpl_dir, 'public')
    try:
        result['public_exists'] = os.path.isdir(pub_dir)
        result['public_contents'] = sorted(os.listdir(pub_dir))
    except Exception as e:
        result['public_exists'] = False
        result['public_contents'] = str(e)
    
    # What's inside /var/task/titan_lms/static/?
    static_dir = os.path.join(titan_pkg, 'static')
    try:
        result['static_exists'] = os.path.isdir(static_dir)
        result['static_contents'] = sorted(os.listdir(static_dir))
    except Exception as e:
        result['static_exists'] = False
        result['static_contents'] = str(e)
    
    # Flask app template search paths
    try:
        loader = app.jinja_env.loader
        result['jinja_searchpath'] = getattr(loader, 'searchpath', 'unknown')
    except Exception as e:
        result['jinja_searchpath'] = str(e)
    
    return json.dumps(result, indent=2), 200, {'Content-Type': 'application/json'}

if __name__ == "__main__":
    app.run()
