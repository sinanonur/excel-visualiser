#!/usr/bin/env python3
"""
Simple test runner for Excel Visualizer LLM functionality.
Run this to verify the LLM models are working correctly.
"""

import sys
import os

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

def run_basic_test():
    """Run a basic test of LLM functionality"""
    print("🚀 Excel Visualizer LLM Test")
    print("=" * 40)
    
    try:
        # Test imports
        from llm import TestLlm, GeminiLlm
        print("✅ LLM modules imported successfully")
        
        # Test TestLlm with simple data
        import pandas as pd
        test_df = pd.DataFrame({
            'Energy': [100, 150, 200],
            'Sugar': [5.0, 8.0, 12.0]
        })
        
        test_llm = TestLlm()
        code = test_llm.generate_plot_code(
            "Create a scatter plot for Energy vs Sugar", 
            test_df, 
            ['Energy', 'Sugar']
        )
        
        if code and len(code) > 100:
            print("✅ TestLlm generated plot code successfully")
        else:
            print("❌ TestLlm failed to generate adequate code")
            return False
            
        print("✅ Basic LLM test passed!")
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        print("Make sure you're running from the project root directory")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = run_basic_test()
    sys.exit(0 if success else 1)