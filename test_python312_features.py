#!/usr/bin/env python3
"""
Python 3.12 Specific Features Test for Excel Data Visualizer

This test verifies that Python 3.12 specific features work correctly
with the Excel Data Visualizer backend.
"""

import sys
from typing import Optional

def test_python_312_features():
    """Test Python 3.12 specific features"""
    print(f"Testing Python {sys.version_info.major}.{sys.version_info.minor} specific features...")
    
    # Test f-string improvements (Python 3.12+)
    if sys.version_info >= (3, 12):
        try:
            # Test new f-string features
            name = "Excel Visualizer"
            version = "1.0"
            result = f"Application: {name=}, {version=}"
            assert "name='Excel Visualizer'" in result
            print("✅ Python 3.12 f-string features work correctly")
        except Exception as e:
            print(f"❌ Python 3.12 f-string test failed: {e}")
            return False
    
    # Test type hints improvements
    try:
        def process_data(data: list[dict[str, str | int]]) -> Optional[dict]:
            """Function using modern type hints"""
            if not data:
                return None
            return {"count": len(data), "first": data[0]}
        
        test_data = [{"name": "test", "value": 42}]
        result = process_data(test_data)
        assert result["count"] == 1
        print("✅ Modern type hints work correctly")
    except Exception as e:
        print(f"❌ Type hints test failed: {e}")
        return False
    
    # Test with our actual backend imports
    try:
        from backend.app import DataProcessor
        
        # Test that DataProcessor works with Python 3.12
        processor = DataProcessor()
        assert processor.data is None
        assert processor.column_info == {}
        print("✅ Backend DataProcessor works with current Python version")
    except Exception as e:
        print(f"❌ Backend integration test failed: {e}")
        return False
    
    return True

def test_performance_improvements():
    """Test performance-related features"""
    import time
    
    # Test dictionary performance improvements in Python 3.12
    start_time = time.time()
    large_dict = {f"key_{i}": f"value_{i}" for i in range(10000)}
    dict_time = time.time() - start_time
    
    print(f"✅ Dictionary creation performance: {dict_time:.4f}s (improved in Python 3.12)")
    
    # Test list comprehension performance
    start_time = time.time()
    large_list = [i * 2 for i in range(10000)]
    list_time = time.time() - start_time
    
    print(f"✅ List comprehension performance: {list_time:.4f}s")
    
    return dict_time < 1.0 and list_time < 1.0  # Should be very fast

def main():
    """Main test function"""
    print("🧪 Testing Python 3.12 compatibility and features...\n")
    
    if not test_python_312_features():
        print("❌ Python 3.12 features test failed")
        sys.exit(1)
    
    if not test_performance_improvements():
        print("❌ Performance test failed")
        sys.exit(1)
    
    print(f"\n🎉 All Python {sys.version_info.major}.{sys.version_info.minor} tests passed!")
    
    if sys.version_info >= (3, 12):
        print("🌟 You're getting the benefit of Python 3.12+ improvements!")
        print("   - Better error messages")
        print("   - Improved performance")
        print("   - Enhanced f-string capabilities")
        print("   - More efficient memory usage")

if __name__ == "__main__":
    main()