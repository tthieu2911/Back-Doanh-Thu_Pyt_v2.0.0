import subprocess
import sys
import webbrowser
import time
import os

def main():
    url = "http://localhost:8501"
    time.sleep(0.5)
    webbrowser.open(url)

    streamlit_cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        os.path.join(os.path.dirname(__file__), "app.py"),
        "--server.port", "8501",
        "--server.headless", "true"
    ]

    subprocess.run(streamlit_cmd)

if __name__ == "__main__":
    main()