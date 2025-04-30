#!/usr/bin/env python3
"""
Time Tracker Application - Main Entry Point
"""
import logging
import sys
import argparse
import os

from timetracker.frontend.app import create_and_run_app

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
    
    # Set library loggers to a higher level to reduce noise
    logging.getLogger('PIL').setLevel(logging.WARNING)
    
    if debug:
        logging.info("Debug logging enabled")
    
    return debug

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Time Tracker Application")
    parser.add_argument('--debug', '-d', action='store_true', help='Enable debug mode with verbose logging')
    return parser.parse_args()

if __name__ == "__main__":
    try:
        # Parse command line arguments
        args = parse_args()
        
        # Configure logging
        debug_mode = configure_logging(args.debug)
        
        # Run the application
        create_and_run_app(debug_mode=debug_mode)
    except Exception as e:
        logging.exception(f"Fatal error: {e}")
        sys.exit(1)
