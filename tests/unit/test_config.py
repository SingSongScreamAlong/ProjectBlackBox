"""
Simple unit tests for configuration modules
Tests that don't require external dependencies
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_config_module_exists():
    """Test that config module can be imported"""
    try:
        from relay_agent.config import Config
        assert Config is not None
        print("✅ Config module imports successfully")
        return True
    except ImportError as e:
        print(f"❌ Config module import failed: {e}")
        return False

def test_config_properties():
    """Test that config has expected properties"""
    try:
        from relay_agent.config import Config
        config = Config()
        
        # Test properties exist
        assert hasattr(config, 'BACKEND_URL')
        assert hasattr(config, 'SERVER_URL')
        assert hasattr(config, 'NODE_ENV')
        assert hasattr(config, 'is_production')
        
        print("✅ Config has all expected properties")
        return True
    except Exception as e:
        print(f"❌ Config properties test failed: {e}")
        return False

def test_environment_defaults():
    """Test that config provides defaults"""
    try:
        from relay_agent.config import Config
        config = Config()
        
        # Should have defaults
        assert config.BACKEND_URL is not None
        assert config.SERVER_URL is not None
        assert config.NODE_ENV in ['development', 'production', 'test']
        
        print("✅ Config provides valid defaults")
        return True
    except Exception as e:
        print(f"❌ Environment defaults test failed: {e}")
        return False

if __name__ == '__main__':
    print("Running relay agent configuration tests...")
    print()
    
    results = []
    results.append(test_config_module_exists())
    results.append(test_config_properties())
    results.append(test_environment_defaults())
    
    print()
    print(f"Tests passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("✅ All configuration tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        sys.exit(1)
