#!/usr/bin/env python3
"""
Setup script for the Bybit Grid Trading Bot.

This script helps with initial setup, configuration validation,
and environment preparation.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any


def check_python_version() -> bool:
    """Check if Python version is 3.10 or higher."""
    version = sys.version_info
    if version.major == 3 and version.minor >= 10:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} is supported")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} is not supported")
        print("Please install Python 3.10 or higher")
        return False


def install_dependencies() -> bool:
    """Install required dependencies."""
    print("\n📦 Installing dependencies...")
    
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                      check=True, capture_output=True)
        print("✅ pip upgraded successfully")
        
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def create_directories() -> bool:
    """Create necessary directories."""
    print("\n📁 Creating directories...")
    
    directories = [
        "logs",
        "data",
        "backups",
        "temp"
    ]
    
    for directory in directories:
        path = Path(directory)
        try:
            path.mkdir(exist_ok=True)
            print(f"✅ Created directory: {directory}")
        except Exception as e:
            print(f"❌ Failed to create directory {directory}: {e}")
            return False
    
    return True


def setup_config_files() -> bool:
    """Setup configuration files."""
    print("\n⚙️ Setting up configuration files...")
    
    # Copy .env.example to .env if it doesn't exist
    env_example = Path("config/.env.example")
    env_file = Path("config/.env")
    
    if env_example.exists() and not env_file.exists():
        try:
            shutil.copy(env_example, env_file)
            print("✅ Created config/.env from template")
            print("⚠️  Please edit config/.env with your API credentials")
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
            return False
    elif env_file.exists():
        print("✅ config/.env already exists")
    else:
        print("❌ config/.env.example not found")
        return False
    
    # Check config.yaml
    config_file = Path("config/config.yaml")
    if config_file.exists():
        print("✅ config/config.yaml exists")
    else:
        print("❌ config/config.yaml not found")
        return False
    
    return True


def validate_config() -> bool:
    """Validate configuration."""
    print("\n🔍 Validating configuration...")
    
    try:
        from utils.config import load_config, validate_config
        
        config = load_config()
        validate_config(config)
        print("✅ Configuration is valid")
        return True
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        print("Please check your configuration files")
        return False


def test_api_connection() -> bool:
    """Test API connection."""
    print("\n🔗 Testing API connection...")
    
    try:
        import asyncio
        from api import BybitClient
        from utils.config import load_config
        
        async def test_connection():
            config = load_config()
            
            if not config.api_key or not config.api_secret:
                print("⚠️  API credentials not configured, skipping connection test")
                return True
            
            client = BybitClient(
                api_key=config.api_key,
                api_secret=config.api_secret,
                testnet=config.testnet
            )
            
            try:
                await client.connect()
                balance = await client.get_balance()
                print(f"✅ API connection successful")
                print(f"✅ Account balance: {balance.available_balance} USDT")
                return True
            except Exception as e:
                print(f"❌ API connection failed: {e}")
                return False
            finally:
                await client.disconnect()
        
        return asyncio.run(test_connection())
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False


def run_basic_tests() -> bool:
    """Run basic tests to ensure everything works."""
    print("\n🧪 Running basic tests...")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/", "-v", "--tb=short", "-x"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Basic tests passed")
            return True
        else:
            print("❌ Some tests failed")
            print(result.stdout)
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Failed to run tests: {e}")
        return False


def create_systemd_service() -> bool:
    """Create systemd service file (Linux only)."""
    if sys.platform != "linux":
        print("⚠️  Systemd service creation is only available on Linux")
        return True
    
    print("\n🔧 Creating systemd service...")
    
    service_content = f"""[Unit]
Description=Bybit Grid Trading Bot
After=network.target

[Service]
Type=simple
User={os.getenv('USER', 'trader')}
WorkingDirectory={Path.cwd()}
ExecStart={sys.executable} main.py
Restart=always
RestartSec=10
Environment=PYTHONPATH={Path.cwd()}

[Install]
WantedBy=multi-user.target
"""
    
    service_file = Path("bybit-grid-trader.service")
    try:
        with open(service_file, 'w') as f:
            f.write(service_content)
        
        print(f"✅ Service file created: {service_file}")
        print("To install the service:")
        print(f"  sudo cp {service_file} /etc/systemd/system/")
        print("  sudo systemctl daemon-reload")
        print("  sudo systemctl enable bybit-grid-trader")
        print("  sudo systemctl start bybit-grid-trader")
        return True
    except Exception as e:
        print(f"❌ Failed to create service file: {e}")
        return False


def print_next_steps():
    """Print next steps for the user."""
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit config/.env with your Bybit API credentials")
    print("2. Review and adjust config/config.yaml settings")
    print("3. Test the configuration:")
    print("   python main.py --mode status")
    print("4. Run the bot:")
    print("   python main.py")
    print("\n📚 Documentation:")
    print("- README.md - Getting started guide")
    print("- docs/STRATEGY_GUIDE.md - Strategy configuration")
    print("- docs/API_REFERENCE.md - API documentation")
    print("- docs/TROUBLESHOOTING.md - Problem solving")
    print("\n⚠️  Important:")
    print("- Always test on testnet first!")
    print("- Start with small amounts")
    print("- Monitor the bot regularly")
    print("- Have a risk management plan")


def main():
    """Main setup function."""
    print("🚀 Bybit Grid Trading Bot - Setup")
    print("=" * 50)
    
    steps = [
        ("Checking Python version", check_python_version),
        ("Installing dependencies", install_dependencies),
        ("Creating directories", create_directories),
        ("Setting up configuration", setup_config_files),
        ("Validating configuration", validate_config),
        ("Testing API connection", test_api_connection),
        ("Running basic tests", run_basic_tests),
        ("Creating systemd service", create_systemd_service)
    ]
    
    failed_steps = []
    
    for step_name, step_func in steps:
        print(f"\n🔄 {step_name}...")
        try:
            if not step_func():
                failed_steps.append(step_name)
        except Exception as e:
            print(f"❌ {step_name} failed with exception: {e}")
            failed_steps.append(step_name)
    
    if failed_steps:
        print(f"\n⚠️  Setup completed with {len(failed_steps)} issues:")
        for step in failed_steps:
            print(f"  - {step}")
        print("\nPlease resolve these issues before running the bot.")
        sys.exit(1)
    else:
        print_next_steps()
        sys.exit(0)


if __name__ == "__main__":
    main()
