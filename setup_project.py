#!/usr/bin/env python3
"""
Setup script for TimeTracker development environment
"""
import os
import sys
import subprocess
import platform
from pathlib import Path

def create_virtual_env():
    """Create and activate a virtual environment"""
    # Check if virtual environment exists already
    venv_dir = Path(".venv")
    if venv_dir.exists():
        print("Virtual environment already exists.")
        return True
        
    print("Creating virtual environment...")
    try:
        # Create virtual environment
        subprocess.run([sys.executable, "-m", "venv", ".venv"], check=True)
        print("Virtual environment created successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to create virtual environment: {e}")
        return False
        
def install_dependencies():
    """Install dependencies from requirements.txt"""
    # Determine the correct pip command based on platform and virtual env
    if platform.system() == "Windows":
        pip_cmd = os.path.join(".venv", "Scripts", "pip")
    else:
        pip_cmd = os.path.join(".venv", "bin", "pip")
        
    # Check if requirements.txt exists
    if not os.path.exists("requirements.txt"):
        print("Error: requirements.txt not found!")
        return False
        
    print("Installing dependencies...")
    try:
        subprocess.run([pip_cmd, "install", "-U", "pip"], check=True)
        subprocess.run([pip_cmd, "install", "-r", "requirements.txt"], check=True)
        print("Dependencies installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        return False
        
def create_assets_directory():
    """Create assets directory for application resources"""
    assets_dir = Path("assets")
    if not assets_dir.exists():
        assets_dir.mkdir()
        print("Created assets directory")
        # Create a placeholder file for the icon
        placeholder = assets_dir / "README.txt"
        with open(placeholder, "w") as f:
            f.write("Place your application icon (timetracker.ico) here")
    else:
        print("Assets directory already exists")
    return True

def main():
    print("Setting up TimeTracker development environment...")
    
    # Create virtual environment
    if not create_virtual_env():
        return 1
        
    # Install dependencies
    if not install_dependencies():
        return 1
    
    # Create assets directory
    create_assets_directory()
    
    print("\nSetup complete! To activate the virtual environment:")
    if platform.system() == "Windows":
        print("  .venv\\Scripts\\activate")
    else:
        print("  source .venv/bin/activate")
    
    print("\nTo build the executable:")
    print("  python build.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
