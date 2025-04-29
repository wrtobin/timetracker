#!/usr/bin/env python3
"""
Build script for creating a standalone TimeTracker executable
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

def build_executable():
    """Build the TimeTracker executable using PyInstaller"""
    print("Building TimeTracker executable...")
    
    # Ensure we have the assets directory for the icon
    assets_dir = Path("assets")
    if not assets_dir.exists():
        assets_dir.mkdir()
        print("Created assets directory")
    
    # Check if icon exists, if not create placeholder text file
    icon_path = assets_dir / "timetracker.ico"
    if not icon_path.exists():
        print(f"Warning: No icon found at {icon_path}")
        print("Please add an icon file to use for the executable.")
    
    # Clean up previous build artifacts
    dist_dir = Path("dist")
    build_dir = Path("build")
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    if build_dir.exists():
        shutil.rmtree(build_dir)
        
    # Build command construction
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name", "TimeTracker",
        "--add-data", "README.md;.",
        "--add-data", "TODO.md;.",
    ]
    
    # Add icon if it exists
    if icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])
    
    # Add the main script
    cmd.append("timetracker.py")
    
    # Execute PyInstaller
    try:
        subprocess.run(cmd, check=True)
        print(f"\nBuild complete! Executable can be found in the dist folder.")
    except subprocess.CalledProcessError as e:
        print(f"Build failed with error: {e}")
        return False
    
    return True

def main():
    # Make sure PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller is required but not installed.")
        print("Install it with: pip install pyinstaller")
        return 1
        
    # Build the executable
    if build_executable():
        return 0
    return 1

if __name__ == "__main__":
    sys.exit(main())
