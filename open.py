# Open.py
import subprocess
import sys
import os

def run_streamlit():
    # Get the absolute path to app.py
    base_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(base_dir, "app.py")
    # Run Streamlit without opening a terminal window
    # 'start' will open it in the background (Windows only)
    subprocess.Popen(
        f'start /B streamlit run "{app_path}"',
        shell=True,
        creationflags=subprocess.CREATE_NO_WINDOW
    )

if __name__ == "__main__":
    run_streamlit()