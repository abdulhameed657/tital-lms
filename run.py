import os
if not os.environ.get('GEMINI_API_KEY'):
    os.environ['GEMINI_API_KEY'] = 'AQ.Ab8RN6LG-_gX43KeqjTwECnJoJnRCHCKKkrEY363QMZ3BXn8AA'
    os.environ['GOOGLE_API_KEY'] = 'AQ.Ab8RN6LG-_gX43KeqjTwECnJoJnRCHCKKkrEY363QMZ3BXn8AA'

from titan_lms import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=True)


