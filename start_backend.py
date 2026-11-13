#!/usr/bin/env python3
"""Start the Excel Visualizer backend.

From source: installs requirements.txt, then runs backend/app.py.
In the standalone package (PyInstaller): runs the bundled server directly.

Options are passed to the server, e.g. ``--shared`` lets other computers on
the network use the app (see ``python backend/app.py --help``).
"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def run_bundled(argv):
    # In a PyInstaller build sys.executable is this program, not Python, so
    # it must not start "python -m pip" or "python app.py": that re-launches
    # the package itself, endlessly. The server runs in this process instead.
    # PyInstaller bundles `app` and its imports because of this import
    # (backend.spec adds backend/ to the search path).
    from app import main as run_server
    run_server(argv)


def install_requirements():
    print("Installing Python requirements...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r",
                               os.path.join(HERE, "requirements.txt")])
    except subprocess.CalledProcessError as exc:
        print(f"Failed to install Python requirements: {exc}")
        return False
    return True


def run_from_source(argv):
    print("Starting Flask backend server...")
    try:
        subprocess.run([sys.executable, "app.py", *argv], cwd=os.path.join(HERE, "backend"))
    except KeyboardInterrupt:
        print("\nFlask server stopped.")


if __name__ == "__main__":
    arguments = sys.argv[1:]
    if getattr(sys, "frozen", False):
        run_bundled(arguments)
    elif install_requirements():
        run_from_source(arguments)
    else:
        print("Cannot start backend due to dependency installation failure.")
        sys.exit(1)
