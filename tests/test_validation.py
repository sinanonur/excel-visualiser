"""
Test validation schemas and API endpoints
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from marshmallow import ValidationError
from app import (
    PlotConfigSchema, UpdateColumnTypeSchema, ExpandColumnSchema,
    FilterConfigSchema, LLMPlotConfigSchema, ExportDataSchema, ExportPlotSchema
)


def test_plot_config_schema():
    """Test plot configuration validation"""
    schema = PlotConfigSchema()

    # Valid data
    valid_data = {'type': 'scatter', 'columns': ['col1', 'col2']}
    result = schema.load(valid_data)
    assert result['type'] == 'scatter'
    assert result['columns'] == ['col1', 'col2']
    assert result['stacked'] is False  # Default value
    print("✅ PlotConfigSchema: Valid data test passed")

    # Invalid plot type
    try:
        invalid_data = {'type': 'invalid_type', 'columns': ['col1']}
        schema.load(invalid_data)
        assert False, "Should have raised ValidationError"
    except ValidationError as err:
        assert 'type' in err.messages
        print("✅ PlotConfigSchema: Invalid type test passed")

    # Missing required field
    try:
        schema.load({'type': 'scatter'})
        assert False, "Should have raised ValidationError"
    except ValidationError as err:
        assert 'columns' in err.messages
        print("✅ PlotConfigSchema: Missing field test passed")


def test_update_column_type_schema():
    """Test column type update validation"""
    schema = UpdateColumnTypeSchema()

    # Valid data
    valid_data = {'column': 'test_col', 'type': 'numeric'}
    result = schema.load(valid_data)
    assert result['column'] == 'test_col'
    assert result['type'] == 'numeric'
    print("✅ UpdateColumnTypeSchema: Valid data test passed")

    # Invalid type
    try:
        schema.load({'column': 'test', 'type': 'invalid'})
        assert False, "Should have raised ValidationError"
    except ValidationError as err:
        assert 'type' in err.messages
        print("✅ UpdateColumnTypeSchema: Invalid type test passed")


def test_llm_plot_config_schema():
    """Test LLM plot configuration validation"""
    schema = LLMPlotConfigSchema()

    # Valid data with defaults
    valid_data = {'prompt': 'Create a scatter plot'}
    result = schema.load(valid_data)
    assert result['prompt'] == 'Create a scatter plot'
    assert result['model'] == 'gemini'  # Default
    assert result['columns'] == []  # Default
    print("✅ LLMPlotConfigSchema: Valid data with defaults test passed")

    # Prompt too long
    try:
        schema.load({'prompt': 'x' * 5001})
        assert False, "Should have raised ValidationError"
    except ValidationError as err:
        assert 'prompt' in err.messages
        print("✅ LLMPlotConfigSchema: Prompt length validation test passed")

    # Invalid model
    try:
        schema.load({'prompt': 'test', 'model': 'invalid'})
        assert False, "Should have raised ValidationError"
    except ValidationError as err:
        assert 'model' in err.messages
        print("✅ LLMPlotConfigSchema: Invalid model test passed")


def test_export_data_schema():
    """Test export data validation"""
    schema = ExportDataSchema()

    # Valid CSV
    result = schema.load({'format': 'csv'})
    assert result['format'] == 'csv'
    print("✅ ExportDataSchema: CSV format test passed")

    # Valid Excel
    result = schema.load({'format': 'excel'})
    assert result['format'] == 'excel'
    print("✅ ExportDataSchema: Excel format test passed")

    # Invalid format
    try:
        schema.load({'format': 'json'})
        assert False, "Should have raised ValidationError"
    except ValidationError as err:
        assert 'format' in err.messages
        print("✅ ExportDataSchema: Invalid format test passed")


def test_export_plot_schema():
    """Test export plot validation"""
    schema = ExportPlotSchema()

    # Valid data with defaults
    valid_data = {'plot_data': {'data': []}, 'format': 'png'}
    result = schema.load(valid_data)
    assert result['format'] == 'png'
    assert result['width'] == 1200  # Default
    assert result['height'] == 800  # Default
    print("✅ ExportPlotSchema: Valid data with defaults test passed")

    # Custom dimensions
    valid_data = {'plot_data': {'data': []}, 'format': 'svg', 'width': 1600, 'height': 900}
    result = schema.load(valid_data)
    assert result['width'] == 1600
    assert result['height'] == 900
    print("✅ ExportPlotSchema: Custom dimensions test passed")

    # Width too large
    try:
        schema.load({'plot_data': {}, 'format': 'png', 'width': 5000})
        assert False, "Should have raised ValidationError"
    except ValidationError as err:
        assert 'width' in err.messages
        print("✅ ExportPlotSchema: Width validation test passed")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("Testing Validation Schemas")
    print("="*60 + "\n")

    test_plot_config_schema()
    print()
    test_update_column_type_schema()
    print()
    test_llm_plot_config_schema()
    print()
    test_export_data_schema()
    print()
    test_export_plot_schema()

    print("\n" + "="*60)
    print("✅ All validation tests passed!")
    print("="*60)
