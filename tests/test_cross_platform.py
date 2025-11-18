"""
Test cross-platform compatibility features
"""
import sys
import os
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import CACHE_DIR


def test_cache_directory_is_platform_independent():
    """Test that cache directory uses platform-independent temp directory"""
    # CACHE_DIR should use tempfile.gettempdir() which works on all platforms
    temp_dir = tempfile.gettempdir()

    # Cache dir should be under system temp directory
    assert CACHE_DIR.startswith(temp_dir), \
        f"Cache dir {CACHE_DIR} should start with {temp_dir}"

    # Cache dir should be named appropriately
    assert "excel_visualizer_cache" in CACHE_DIR, \
        f"Cache dir {CACHE_DIR} should contain 'excel_visualizer_cache'"

    # Should not be hardcoded to /tmp (Unix-only)
    assert not CACHE_DIR.startswith("/tmp") or temp_dir == "/tmp", \
        "Cache dir should not be hardcoded to /tmp unless that's the system temp"

    print(f"✅ Cache directory is platform-independent: {CACHE_DIR}")


def test_cache_directory_can_be_created():
    """Test that cache directory can be created on any platform"""
    # Import after CACHE_DIR is defined
    from app import get_cache

    # Try to get cache (which creates directory)
    try:
        cache = get_cache()
        cache.close()
        print(f"✅ Cache directory created successfully at: {CACHE_DIR}")

        # Verify it exists
        assert os.path.exists(CACHE_DIR), f"Cache dir should exist at {CACHE_DIR}"
        print(f"✅ Cache directory exists and is accessible")
    except Exception as e:
        raise AssertionError(f"Failed to create cache directory: {e}")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("Testing Cross-Platform Compatibility")
    print("="*60 + "\n")

    test_cache_directory_is_platform_independent()
    test_cache_directory_can_be_created()

    print("\n" + "="*60)
    print("✅ All cross-platform tests passed!")
    print("="*60)
