import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    import strategies
    print("Import successful")
except Exception as e:
    import traceback
    traceback.print_exc()
