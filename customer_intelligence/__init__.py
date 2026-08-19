from pathlib import Path
import sys

# Project root = RetailMind_Member2
PROJECT_ROOT = Path.cwd().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

print("Project root:", PROJECT_ROOT)