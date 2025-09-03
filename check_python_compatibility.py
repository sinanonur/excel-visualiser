#!/usr/bin/env python3
"""
Python 3.12 Compatibility Check for Excel Data Visualizer
This script verifies that all dependencies work correctly with Python 3.12
"""

import sys
import importlib

def check_python_version():
    """Check if Python version is compatible"""
    version_info = sys.version_info
    print(f"Python Version: {version_info.major}.{version_info.minor}.{version_info.micro}")
    
    if version_info >= (3, 7):
        if version_info >= (3, 12):
            print("✅ Python 3.12+ detected - Excellent!")
        else:
            print("✅ Python version is compatible")
        return True
    else:
        print("❌ Python 3.7+ is required")
        return False

def check_dependencies():
    """Check if all required dependencies can be imported"""
    dependencies = [
        'flask',
        'flask_cors',
        'pandas',
        'numpy',
        'plotly',
        'openpyxl',
        'sklearn',
        'matplotlib',
        'seaborn',
        'requests'
    ]
    
    failed_imports = []
    
    for dep in dependencies:
        try:
            module = importlib.import_module(dep)
            version = getattr(module, '__version__', 'unknown')
            print(f"✅ {dep}: {version}")
        except ImportError as e:
            print(f"❌ {dep}: {e}")
            failed_imports.append(dep)
    
    return len(failed_imports) == 0

def test_basic_functionality():
    """Test basic functionality of key libraries"""
    try:
        # Test pandas
        import pandas as pd
        df = pd.DataFrame({'test': [1, 2, 3]})
        assert len(df) == 3
        print("✅ Pandas basic operations work")
        
        # Test numpy
        import numpy as np
        arr = np.array([1, 2, 3])
        assert arr.sum() == 6
        print("✅ NumPy basic operations work")
        
        # Test plotly
        import plotly.graph_objs as go
        fig = go.Figure(data=go.Bar(x=['A', 'B'], y=[1, 2]))
        print("✅ Plotly basic operations work")
        
        # Test flask
        from flask import Flask
        app = Flask(__name__)
        print("✅ Flask basic operations work")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

def main():
    print("🔍 Checking Python 3.12 compatibility for Excel Data Visualizer...\n")
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    print("\n📦 Checking dependencies...")
    if not check_dependencies():
        print("\n❌ Some dependencies are missing. Please run: pip install -r requirements.txt")
        sys.exit(1)
    
    print("\n🧪 Testing basic functionality...")
    if not test_basic_functionality():
        sys.exit(1)
    
    print("\n🎉 All checks passed! Excel Data Visualizer is compatible with your Python installation.")
    
    if sys.version_info >= (3, 12):
        print("🌟 You're running Python 3.12+ which is fully supported!")

if __name__ == "__main__":
    main()