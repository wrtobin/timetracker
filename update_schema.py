#!/usr/bin/env python3
"""
Update Protocol Schema

This script regenerates the Pydantic models from the JSON schema.
It should be run before starting the application or as part of the build process.
"""
import logging
import sys
import argparse
import subprocess
import pathlib

def configure_logging(debug=False):
    """Configure the logging system."""
    log_level = logging.DEBUG if debug else logging.INFO
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return debug

def regenerate_schema():
    """Regenerate the Pydantic models from the JSON schema."""
    try:
        logging.info("Regenerating protocol schema models...")
        # Get the path to the schema.json file
        base_dir = pathlib.Path(__file__).parent
        schema_path = base_dir / "timetracker" / "protocol" / "schema.json"
        output_path = base_dir / "timetracker" / "protocol" / "generated_schema.py"
        
        # Ensure paths exist
        if not schema_path.exists():
            logging.error(f"Schema file not found: {schema_path}")
            return False
            
        # Run datamodel-codegen to regenerate the models
        # Using output-model-type pydantic_v2.BaseModel for Pydantic v2 compatibility
        # Using enum-field-as-literal all to avoid generating multiple enum classes
        # Using use-title-as-name to use title attributes from schema as class names
        command = [
            "datamodel-codegen",
            "--input", str(schema_path),
            "--output", str(output_path),
            "--input-file-type", "jsonschema",
            "--use-schema-description",
            "--output-model-type", "pydantic_v2.BaseModel",
            "--enum-field-as-literal", "all",
            "--use-title-as-name"
        ]
        
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode == 0:
            logging.info("Schema regeneration successful")
            return True
        else:
            logging.error(f"Schema regeneration failed: {result.stderr}")
            return False
    except Exception as e:
        logging.exception(f"Error regenerating schema: {e}")
        return False

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Update Protocol Schema")
    parser.add_argument('--debug', '-d', action='store_true', help='Enable debug mode with verbose logging')
    return parser.parse_args()

if __name__ == "__main__":
    try:
        # Parse command line arguments
        args = parse_args()
        
        # Configure logging
        configure_logging(args.debug)
        
        # Regenerate schema
        success = regenerate_schema()
        sys.exit(0 if success else 1)
    except Exception as e:
        logging.exception(f"Fatal error: {e}")
        sys.exit(1)