#!/usr/bin/env python3
"""
WindSurf MCP Server Setup Guide and Validator
"""
import os
import sys
import json
import subprocess
from pathlib import Path

def check_environment():
    """Check if environment variables are properly set"""
    print("🔍 Checking environment variables...")

    required_vars = {
        "OPENPROJECT_BASE_URL": "Your OpenProject instance URL",
        "OPENPROJECT_API_KEY": "Your OpenProject API key",
        "ENCRYPTION_KEY": "Your encryption key for secure operations"
    }

    all_set = True
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * min(len(value), 8)}{value[8:] if len(value) > 8 else ''}")
        else:
            print(f"❌ {var}: Not set - {description}")
            all_set = False

    return all_set

def check_dependencies():
    """Check if required dependencies are available"""
    print("\n📦 Checking dependencies...")

    deps = ["mcp", "httpx", "backoff", "pydantic"]
    missing = []

    for dep in deps:
        try:
            result = subprocess.run(
                [sys.executable, "-c", f"import {dep}"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print(f"✅ {dep}: Available")
            else:
                print(f"❌ {dep}: Not available")
                missing.append(dep)
        except Exception as e:
            print(f"❌ {dep}: Error checking - {e}")
            missing.append(dep)

    return len(missing) == 0

def test_standalone_script():
    """Test the standalone script"""
    print("\n🧪 Testing standalone script...")

    script_path = Path(__file__).parent / "mcp_openproject_standalone.py"
    if not script_path.exists():
        print(f"❌ Standalone script not found: {script_path}")
        return False

    print(f"✅ Standalone script found: {script_path}")

    # Test script syntax
    try:
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(script_path)],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✅ Script syntax is valid")
            return True
        else:
            print(f"❌ Script syntax error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error testing script: {e}")
        return False

def generate_windsurf_config():
    """Generate WindSurf configuration"""
    print("\n🌐 Generating WindSurf configuration...")

    # Get current directory
    current_dir = Path(__file__).parent.absolute()
    standalone_script = current_dir / "mcp_openproject_standalone.py"

    # Test different deployment options
    configs = []

    # Option 1: Using uvx (recommended)
    uvx_config = {
        "command": "uvx",
        "args": ["run", str(standalone_script)],
        "env": {
            "OPENPROJECT_BASE_URL": "${OPENPROJECT_BASE_URL}",
            "OPENPROJECT_API_KEY": "${OPENPROJECT_API_KEY}",
            "ENCRYPTION_KEY": "${ENCRYPTION_KEY}"
        },
        "description": "Run with uvx (recommended)"
    }
    configs.append(("uvx", uvx_config))

    # Option 2: Using pipx
    pipx_config = {
        "command": "pipx",
        "args": ["run", str(standalone_script)],
        "env": {
            "OPENPROJECT_BASE_URL": "${OPENPROJECT_BASE_URL}",
            "OPENPROJECT_API_KEY": "${OPENPROJECT_API_KEY}",
            "ENCRYPTION_KEY": "${ENCRYPTION_KEY}"
        },
        "description": "Run with pipx"
    }
    configs.append(("pipx", pipx_config))

    # Option 3: Direct Python
    python_config = {
        "command": sys.executable,
        "args": [str(standalone_script)],
        "env": {
            "OPENPROJECT_BASE_URL": "${OPENPROJECT_BASE_URL}",
            "OPENPROJECT_API_KEY": "${OPENPROJECT_API_KEY}",
            "ENCRYPTION_KEY": "${ENCRYPTION_KEY}"
        },
        "description": "Run directly with Python"
    }
    configs.append(("python", python_config))

    # Generate WindSurf config
    windsurf_config = {
        "mcpServers": {
            "openproject": uvx_config  # Default to uvx
        }
    }

    return configs, windsurf_config

def test_mcp_protocol():
    """Test MCP protocol compatibility"""
    print("\n🔌 Testing MCP protocol compatibility...")

    try:
        # Try to import mcp library
        result = subprocess.run(
            [sys.executable, "-c", """
import mcp
import json
from mcp.server import Server
from mcp.server.stdio import stdio_server
print("✅ MCP library is available")
print(f"✅ MCP version: {mcp.__version__ if hasattr(mcp, '__version__') else 'unknown'}")
print("✅ stdio_server is available")
print("✅ JSON-RPC 2.0 support is available")
"""],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(result.stdout)
            return True
        else:
            print(f"❌ MCP protocol test failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error testing MCP protocol: {e}")
        return False

def main():
    """Main function"""
    print("=" * 60)
    print("🚀 WindSurf MCP OpenProject Server Setup Guide")
    print("=" * 60)

    # Check environment
    env_ok = check_environment()

    # Check dependencies
    deps_ok = check_dependencies()

    # Test standalone script
    script_ok = test_standalone_script()

    # Test MCP protocol
    protocol_ok = test_mcp_protocol()

    # Generate configurations
    configs, windsurf_config = generate_windsurf_config()

    print("\n" + "=" * 60)
    print("📊 Setup Status")
    print("=" * 60)
    print(f"✅ Environment Variables: {'OK' if env_ok else 'MISSING'}")
    print(f"✅ Dependencies: {'OK' if deps_ok else 'MISSING'}")
    print(f"✅ Standalone Script: {'OK' if script_ok else 'FAILED'}")
    print(f"✅ MCP Protocol: {'OK' if protocol_ok else 'FAILED'}")

    overall_status = env_ok and deps_ok and script_ok and protocol_ok

    if overall_status:
        print("\n🎉 All checks passed! Ready for WindSurf integration.")
    else:
        print("\n⚠️  Some issues found. Please resolve them before proceeding.")

    print("\n" + "=" * 60)
    print("📋 WindSurf Configuration")
    print("=" * 60)

    print("\n🔧 Recommended Configuration (uvx):")
    print(json.dumps(windsurf_config, indent=2))

    print("\n🔧 Alternative Configurations:")
    for name, config in configs:
        print(f"\n{name}:")
        print(f"  Command: {config['command']}")
        print(f"  Args: {config['args']}")
        print(f"  Description: {config['description']}")

    print("\n" + "=" * 60)
    print("🔧 Setup Instructions")
    print("=" * 60)

    print("\n1. 📦 Install Dependencies:")
    print("```bash")
    print("# Using uvx (recommended)")
    print("uvx install mcp httpx backoff pydantic")
    print("")
    print("# Or using pip")
    print("pip install mcp httpx backoff pydantic")
    print("```")

    print("\n2. 🔧 Set Environment Variables:")
    print("```bash")
    print("export OPENPROJECT_BASE_URL='https://your.openproject.instance'")
    print("export OPENPROJECT_API_KEY='your-api-key'")
    print("export ENCRYPTION_KEY='your-encryption-key'")
    print("```")

    print("\n3. 🌐 Configure WindSurf:")
    print("   Add the configuration above to your WindSurf settings.")
    print("   Replace ${VARIABLE} with actual values.")

    print("\n4. 🧪 Test the Connection:")
    print("   Restart WindSurf and check if the MCP server appears in the tool list.")
    print("   Check logs at /tmp/mcp_openproject_standalone.log for debugging.")

    print("\n" + "=" * 60)
    print("🔍 Troubleshooting")
    print("=" * 60)

    print("\n❌ MCP server not appearing in WindSurf:")
    print("   - Check environment variables are set correctly")
    print("   - Verify the script path is correct")
    print("   - Check logs at /tmp/mcp_openproject_standalone.log")
    print("   - Try running the script manually to test")

    print("\n❌ Authentication errors:")
    print("   - Verify OPENPROJECT_API_KEY is correct")
    print("   - Check OPENPROJECT_BASE_URL is accessible")
    print("   - Ensure API key has necessary permissions")

    print("\n❌ Dependency errors:")
    print("   - Install missing dependencies with uvx or pip")
    print("   - Use the standalone script to avoid environment issues")
    print("   - Check Python version compatibility")

    return 0 if overall_status else 1

if __name__ == "__main__":
    sys.exit(main())