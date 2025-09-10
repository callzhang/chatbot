"""
Alternative entry point for Streamlit Cloud deployment
"""

import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the main app
from app import *
