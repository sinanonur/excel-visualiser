#!/usr/bin/env python3

import requests
import sys
import time
import subprocess
import os

def test_upload():
    """Test the upload endpoint"""
    base_url = os.environ.get('BACKEND_URL', 'http://localhost:5001')
    url = f'{base_url}/upload'
    
    # Check if test_data.xlsx exists
    if not os.path.exists('test_data.xlsx'):
        print("❌ test_data.xlsx not found")
        return False
    
    try:
        with open('test_data.xlsx', 'rb') as f:
            files = {'file': ('test_data.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            response = requests.post(url, files=files, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:500]}...")  # First 500 chars
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Upload successful!")
                print(f"Columns: {data.get('columns')}")
                print(f"Shape: {data.get('shape')}")
                return True
            else:
                print("❌ Upload failed:", data.get('error'))
                return False
        else:
            print("❌ HTTP Error:", response.status_code)
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to backend server. Is it running on port 5001?")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing upload functionality...")
    if test_upload():
        print("🎉 Upload test passed!")
    else:
        print("💥 Upload test failed!")
        sys.exit(1)