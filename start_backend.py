#!/usr/bin/env python3

import subprocess
import sys
import os

def install_requirements():
    """Install Python requirements if needed"""
    print("Installing Python requirements...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Python requirements installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Python requirements: {e}")
        return False
    return True

def start_flask_app():
    """Start the Flask backend"""
    print("Starting Flask backend server...")
    try:
        os.chdir("backend")
        subprocess.run([sys.executable, "app.py"])
    except KeyboardInterrupt:
        print("\n🛑 Flask server stopped.")
    except Exception as e:
        print(f"❌ Failed to start Flask server: {e}")

if __name__ == "__main__":
    print("🚀 Starting Excel Visualizer Backend...")
    
    if install_requirements():
        start_flask_app()
    else:
        print("❌ Cannot start backend due to dependency installation failure.")
        sys.exit(1)