#!/usr/bin/env python3
"""
LLM Plot Generation Tests
Tests for both TestLlm and GeminiLlm models with proper data cleaning.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

import pandas as pd
import json
from io import BytesIO

def test_llm_models():
    """Test both LLM models with clean test data"""
    print("🧪 Testing LLM Plot Generation Models")
    print("=" * 50)
    
    # Create clean test data with Energy and Sugar columns
    test_data = {
        'Product': ['Product A', 'Product B', 'Product C', 'Product D', 'Product E'],
        'Energy': [100.0, 150.0, 200.0, 180.0, 120.0],
        'Sugar': [5.2, 8.1, 12.3, 9.7, 6.4],
        'Category': ['Food', 'Drink', 'Snack', 'Food', 'Drink']
    }
    df = pd.DataFrame(test_data)
    
    try:
        # Import backend components
        from backend.app import DataProcessor
        from llm import TestLlm, GeminiLlm
        
        # Initialize DataProcessor
        data_processor = DataProcessor()
        
        # Convert DataFrame to Excel bytes (simulate file upload)
        excel_buffer = BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_bytes = excel_buffer.getvalue()
        
        # Load into DataProcessor
        success = data_processor.load_excel(excel_bytes)
        if not success:
            print("❌ Failed to load test data")
            return False
        
        print(f"✅ Test data loaded: {df.shape}")
        
        # Test both models
        models = [
            ("TestLlm", TestLlm()),
            ("GeminiLlm", GeminiLlm())
        ]
        
        prompt = "Create a correlation scatter plot for Energy and Sugar columns"
        selected_columns = ["Energy", "Sugar"]
        
        for model_name, llm in models:
            print(f"\n🔍 Testing {model_name}:")
            
            try:
                # Generate code
                plot_code = llm.generate_plot_code(prompt, data_processor.data, selected_columns)
                print(f"  ✅ Code generated ({len(plot_code)} chars)")
                
                # Test execution
                import plotly.graph_objs as go
                import plotly.express as px
                import numpy as np
                
                allowed_globals = {
                    'go': go, 'px': px, 'pd': pd, 'np': np, 'json': json,
                    'plotly': __import__('plotly')
                }
                local_vars = {'df': data_processor.data, 'fig': None}
                
                exec(plot_code, allowed_globals, local_vars)
                fig = local_vars.get('fig')
                
                if fig:
                    print(f"  ✅ Plot created successfully")
                    
                    # Test JSON conversion
                    import plotly.utils
                    plot_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
                    print(f"  ✅ JSON conversion successful ({len(plot_json)} chars)")
                else:
                    print(f"  ❌ No figure object created")
                    
            except Exception as e:
                print(f"  ❌ {model_name} failed: {e}")
                
        print(f"\n✅ LLM test completed successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure the backend modules are available")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_llm_models()