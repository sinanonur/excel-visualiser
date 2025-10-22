#!/usr/bin/env python3

import requests
import json
import sys
import os

def test_filtering_endpoints():
    """Test the filtering functionality"""
    base_url = os.environ.get('BACKEND_URL', 'http://localhost:5001')
    
    print("🧪 Testing filtering functionality...")
    
    # First upload test data
    try:
        with open('test_data.xlsx', 'rb') as f:
            files = {'file': ('test_data.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            response = requests.post(f'{base_url}/upload', files=files, timeout=10)
        
        if response.status_code != 200:
            print("❌ Upload failed, cannot test filtering")
            return False
            
        print("✅ Test data uploaded")
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend server on port 5001")
        return False
    
    # Test filter options endpoint
    try:
        response = requests.get(f'{base_url}/filter-options/Department')
        if response.status_code == 200:
            options = response.json()
            print(f"✅ Filter options for Department: {options}")
        else:
            print("❌ Failed to get filter options")
            return False
    except Exception as e:
        print(f"❌ Error getting filter options: {e}")
        return False
    
    # Test applying categorical filter
    try:
        filter_config = {
            'filters': {
                'Department': {
                    'type': 'categorical',
                    'values': ['IT']
                }
            }
        }
        
        response = requests.post(f'{base_url}/apply-filters', json=filter_config)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Applied categorical filter: {result}")
        else:
            print("❌ Failed to apply categorical filter")
            return False
    except Exception as e:
        print(f"❌ Error applying filter: {e}")
        return False
    
    # Test filter status
    try:
        response = requests.get(f'{base_url}/filter-status')
        if response.status_code == 200:
            status = response.json()
            print(f"✅ Filter status: {status}")
        else:
            print("❌ Failed to get filter status")
            return False
    except Exception as e:
        print(f"❌ Error getting filter status: {e}")
        return False
    
    # Test clearing filters
    try:
        response = requests.post(f'{base_url}/clear-filters')
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Cleared filters: {result}")
        else:
            print("❌ Failed to clear filters")
            return False
    except Exception as e:
        print(f"❌ Error clearing filters: {e}")
        return False
    
    print("🎉 All filtering tests passed!")
    return True

if __name__ == "__main__":
    if test_filtering_endpoints():
        print("✨ Filtering functionality is working correctly!")
        sys.exit(0)
    else:
        print("💥 Some filtering tests failed!")
        sys.exit(1)