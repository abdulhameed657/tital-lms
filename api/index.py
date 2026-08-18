import os
import sys

# Ensure root workspace is in sys.path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, root_dir)

from titan_lms import create_app

app = create_app()

@app.route('/api/health')
def health_check():
    return "OK - Titan LMS is Running on Vercel!", 200

@app.route('/api/debug-paths')
def debug_paths():
    """Temporary diagnostic: list actual files bundled by Vercel."""
    import json
    package_dir = os.path.join(root_dir, 'titan_lms')
    template_dir = os.path.join(package_dir, 'templates')
    
    result = {
        'root_dir': root_dir,
        'package_dir': package_dir,
        'template_dir': template_dir,
        'template_dir_exists': os.path.isdir(template_dir),
        'cwd': os.getcwd(),
    }
    
    # List top-level items in titan_lms/
    try:
        result['titan_lms_contents'] = os.listdir(package_dir)
    except Exception as e:
        result['titan_lms_contents'] = str(e)
    
    # List items in titan_lms/templates/
    try:
        result['templates_contents'] = os.listdir(template_dir)
    except Exception as e:
        result['templates_contents'] = str(e)
    
    # List items in titan_lms/templates/public/
    public_dir = os.path.join(template_dir, 'public')
    try:
        result['public_contents'] = os.listdir(public_dir)
    except Exception as e:
        result['public_contents'] = str(e)
    
    # List /var/task contents
    try:
        result['var_task_contents'] = os.listdir('/var/task')
    except Exception as e:
        result['var_task_contents'] = str(e)
    
    return json.dumps(result, indent=2), 200, {'Content-Type': 'application/json'}

if __name__ == "__main__":
    app.run()
