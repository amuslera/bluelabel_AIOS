import os
import sys
import subprocess

# Add the project root to sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Run Streamlit with the correct working directory and PYTHONPATH
env = os.environ.copy()
env["PYTHONPATH"] = project_root

subprocess.run(
    ["streamlit", "run", "app/ui/streamlit_app.py"],
    env=env,
    cwd=project_root
) 