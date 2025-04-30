#!/usr/bin/env python3
"""
Build script for creating a standalone TimeTracker executable
"""
import os
import sys
import shutil
import subprocess
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_schema():
    """Generate the protocol schema from JSON schema file"""
    logger.info("Generating protocol schema models...")
    
    schema_path = Path("timetracker") / "protocol" / "schema.json"
    output_path = Path("timetracker") / "protocol" / "generated_schema.py"
    
    # Ensure the schema file exists
    if not schema_path.exists():
        logger.error(f"Schema file not found: {schema_path}")
        return False
        
    # Run datamodel-codegen to generate the models
    cmd = [
        "datamodel-codegen",
        "--input", str(schema_path),
        "--output", str(output_path),
        "--input-file-type", "jsonschema",
        "--use-schema-description",
        "--output-model-type", "pydantic_v2.BaseModel",
        "--enum-field-as-literal", "all",
        "--use-title-as-name"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("Schema regeneration successful")
            return True
        else:
            logger.error(f"Schema regeneration failed: {result.stderr}")
            return False
    except Exception as e:
        logger.exception(f"Error regenerating schema: {e}")
        return False

def build_executable():
    """Build the TimeTracker executable using PyInstaller"""
    logger.info("Building TimeTracker executable...")
    
    # Ensure we have the assets directory for the icon
    assets_dir = Path("assets")
    if not assets_dir.exists():
        assets_dir.mkdir()
        logger.info("Created assets directory")
    
    # Check if icon exists, if not create placeholder text file
    icon_path = assets_dir / "timetracker.ico"
    if not icon_path.exists():
        logger.warning(f"Warning: No icon found at {icon_path}")
        logger.warning("Please add an icon file to use for the executable.")
    
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
        logger.info("Build complete! Executable can be found in the dist folder.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Build failed with error: {e}")
        return False
    
    return True

def main():
    # Make sure PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        logger.error("PyInstaller is required but not installed.")
        logger.error("Install it with: pip install pyinstaller")
        return 1
    
    # Make sure datamodel-code-generator is installed
    try:
        import datamodel_code_generator
    except ImportError:
        logger.error("datamodel-code-generator is required but not installed.")
        logger.error("Install it with: pip install datamodel-code-generator")
        return 1
        
    # First, generate the protocol schema
    logger.info("Step 1: Generating protocol schema")
    if not generate_schema():
        logger.error("Failed to generate protocol schema. Build aborted.")
        return 1
    
    # Then, build the executable
    logger.info("Step 2: Building executable")
    if build_executable():
        return 0
    
    return 1

if __name__ == "__main__":
    sys.exit(main())
