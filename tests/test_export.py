"""
Test export functionality
"""
import sys
import os
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import pandas as pd
from io import BytesIO
from app import DataProcessor


def test_csv_export():
    """Test CSV export functionality"""
    # Create test data
    processor = DataProcessor()
    test_data = pd.DataFrame({
        'name': ['Alice', 'Bob', 'Charlie'],
        'age': [25, 30, 35],
        'city': ['NY', 'LA', 'SF']
    })
    processor.data = test_data
    processor.original_data = test_data.copy()
    processor.detect_column_types()

    # Export to CSV
    buffer = BytesIO()
    processor.data.to_csv(buffer, index=False, encoding='utf-8')
    buffer.seek(0)

    # Read back and verify
    result_df = pd.read_csv(buffer)
    assert len(result_df) == 3
    assert list(result_df.columns) == ['name', 'age', 'city']
    assert result_df['name'].tolist() == ['Alice', 'Bob', 'Charlie']

    print("✅ CSV export test passed")


def test_excel_export():
    """Test Excel export functionality"""
    # Create test data
    processor = DataProcessor()
    test_data = pd.DataFrame({
        'product': ['A', 'B', 'C'],
        'price': [10.5, 20.0, 15.75],
        'quantity': [100, 200, 150]
    })
    processor.data = test_data
    processor.original_data = test_data.copy()
    processor.detect_column_types()

    # Export to Excel
    buffer = BytesIO()
    processor.data.to_excel(buffer, index=False, engine='openpyxl')
    buffer.seek(0)

    # Read back and verify
    result_df = pd.read_excel(buffer, engine='openpyxl')
    assert len(result_df) == 3
    assert list(result_df.columns) == ['product', 'price', 'quantity']
    assert result_df['price'].tolist() == [10.5, 20.0, 15.75]

    print("✅ Excel export test passed")


def test_filtered_data_export():
    """Test export with filtered data"""
    # Create test data
    processor = DataProcessor()
    test_data = pd.DataFrame({
        'category': ['A', 'B', 'A', 'C', 'B'],
        'value': [10, 20, 30, 40, 50]
    })
    processor.data = test_data
    processor.original_data = test_data.copy()
    processor.detect_column_types()

    # Apply filter
    filters = {
        'category': {
            'type': 'categorical',
            'values': ['A']
        }
    }
    processor.apply_filters(filters)

    # Verify filtered data
    assert len(processor.data) == 2
    assert processor.data['category'].tolist() == ['A', 'A']
    assert processor.data['value'].tolist() == [10, 30]

    # Export filtered data
    buffer = BytesIO()
    processor.data.to_csv(buffer, index=False)
    buffer.seek(0)

    # Read back and verify only filtered data is exported
    result_df = pd.read_csv(buffer)
    assert len(result_df) == 2
    assert result_df['category'].tolist() == ['A', 'A']

    print("✅ Filtered data export test passed")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("Testing Export Functionality")
    print("="*60 + "\n")

    test_csv_export()
    test_excel_export()
    test_filtered_data_export()

    print("\n" + "="*60)
    print("✅ All export tests passed!")
    print("="*60)
