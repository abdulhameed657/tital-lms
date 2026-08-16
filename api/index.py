import os
import sys

# Ensure root folder is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from titan_lms import create_app

app = create_app()
