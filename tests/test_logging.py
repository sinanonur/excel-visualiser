"""
Test logging functionality
"""
import sys
import os
import tempfile
import logging
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Import app to trigger logging setup
import app as backend_app


def test_logging_is_configured():
    """Test that logging is properly configured"""
    # Get root logger
    root_logger = logging.getLogger()

    # Should have handlers
    assert len(root_logger.handlers) > 0, "Logger should have handlers"
    print(f"✅ Logger has {len(root_logger.handlers)} handler(s)")

    # Should have console and file handlers
    handler_types = [type(h).__name__ for h in root_logger.handlers]
    assert 'StreamHandler' in handler_types, "Should have console handler"
    assert 'RotatingFileHandler' in handler_types, "Should have file handler"
    print(f"✅ Handler types: {', '.join(handler_types)}")


def test_log_file_location():
    """Test that log file is in platform-independent location"""
    # Log directory should be in temp
    temp_dir = tempfile.gettempdir()
    log_dir = os.path.join(temp_dir, "excel_visualizer_logs")

    # Find the RotatingFileHandler
    root_logger = logging.getLogger()
    file_handlers = [h for h in root_logger.handlers
                     if type(h).__name__ == 'RotatingFileHandler']

    assert len(file_handlers) > 0, "Should have at least one file handler"

    file_handler = file_handlers[0]
    log_file_path = file_handler.baseFilename

    # Should be under temp directory
    assert log_file_path.startswith(temp_dir), \
        f"Log file {log_file_path} should be under {temp_dir}"

    print(f"✅ Log file location is platform-independent: {log_file_path}")


def test_logging_works():
    """Test that logging actually works"""
    logger = backend_app.logger

    # Test different log levels
    logger.info("Test INFO message")
    logger.warning("Test WARNING message")
    logger.error("Test ERROR message")
    logger.debug("Test DEBUG message")

    print("✅ Logging functions work without errors")


def test_log_format():
    """Test that log messages have proper format"""
    root_logger = logging.getLogger()

    # Check console handler format
    console_handlers = [h for h in root_logger.handlers
                       if type(h).__name__ == 'StreamHandler']

    if console_handlers:
        formatter = console_handlers[0].formatter
        assert formatter is not None, "Console handler should have formatter"

        # Format should include timestamp, level, and message
        fmt = formatter._fmt
        assert '%(asctime)s' in fmt, "Format should include timestamp"
        assert '%(levelname)s' in fmt, "Format should include log level"
        assert '%(message)s' in fmt, "Format should include message"

        print(f"✅ Log format includes required fields")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("Testing Logging Functionality")
    print("="*60 + "\n")

    test_logging_is_configured()
    test_log_file_location()
    test_logging_works()
    test_log_format()

    print("\n" + "="*60)
    print("✅ All logging tests passed!")
    print("="*60)
