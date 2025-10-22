# Python Version Requirements

## Required Python Version
- **Python 3.11** is required for this project
- Earlier versions may not be compatible with all dependencies
- Later versions (3.12+) may work but are not officially tested

## Why Python 3.11?
- pandas 2.0.3 has optimal performance with Python 3.11
- Flask and related dependencies are tested with Python 3.11
- Provides stable performance for data processing operations

## Installation Instructions

### Windows
1. Download Python 3.11 from [python.org/downloads](https://www.python.org/downloads/)
2. During installation, check "Add Python to PATH"
3. Verify installation: `python --version` should show 3.11.x

### Linux/macOS
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv

# macOS with Homebrew
brew install python@3.11
```

## Virtual Environment Setup
```bash
# Create virtual environment
python3.11 -m venv venv

# Activate (Linux/macOS)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt
```

## Verification
After setup, verify the correct Python version:
```bash
python --version
# Should output: Python 3.11.x
```