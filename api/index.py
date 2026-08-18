import os
import sys

# Ensure root workspace is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from titan_lms import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
