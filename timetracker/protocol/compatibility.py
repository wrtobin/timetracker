"""
Protocol compatibility module for TimeTracker.

This module handles protocol versioning and compatibility between different
versions of the frontend and backend components.
"""

import logging
from typing import Dict, List, Optional, Union, Any, Tuple

logger = logging.getLogger(__name__)

# The current protocol version
try:
    from .version import VERSION as CURRENT_PROTOCOL_VERSION
except ImportError:
    CURRENT_PROTOCOL_VERSION = "0.3.0"  # Default if version.py doesn't exist yet

# Dictionary of supported protocol version combinations
# Keys are (frontend_version, backend_version) tuples
# Values are compatibility handlers (if needed) or True (if directly compatible)
COMPATIBILITY_MAP = {
    # Same version is always compatible
    ("0.3.0", "0.3.0"): True,
    
    # For future versions, we'll add handlers
    # Example: ("0.3.0", "0.4.0"): upgrade_0_3_to_0_4,
}

def check_compatibility(frontend_version: str, backend_version: str) -> bool:
    """
    Check if the frontend and backend versions are compatible.
    
    Args:
        frontend_version: The frontend protocol version
        backend_version: The backend protocol version
        
    Returns:
        True if compatible, False otherwise
    """
    compatibility = COMPATIBILITY_MAP.get((frontend_version, backend_version))
    
    if compatibility is True:
        # Direct compatibility
        return True
    elif compatibility:
        # There's a compatibility handler function
        logger.info(
            f"Frontend version {frontend_version} and backend version {backend_version} "
            f"are compatible with conversion"
        )
        return True
    else:
        # No compatibility defined
        logger.warning(
            f"Frontend version {frontend_version} and backend version {backend_version} "
            f"are not compatible"
        )
        return False

def convert_message(
    message: Dict[str, Any],
    from_version: str,
    to_version: str
) -> Dict[str, Any]:
    """
    Convert a message from one protocol version to another.
    
    Args:
        message: The message to convert
        from_version: Source protocol version
        to_version: Target protocol version
        
    Returns:
        The converted message
    """
    # If versions match, no conversion needed
    if from_version == to_version:
        return message
        
    # Find the appropriate converter function
    handler = COMPATIBILITY_MAP.get((from_version, to_version))
    
    if not handler or handler is True:
        # No conversion needed or possible
        return message
        
    # Call the conversion handler
    return handler(message)

# For future use - placeholder for version upgrade functions
def upgrade_0_3_to_0_4(message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Upgrade a message from protocol v0.3.0 to v0.4.0.
    
    This is a placeholder for future implementation.
    
    Args:
        message: The message in v0.3.0 format
        
    Returns:
        The message converted to v0.4.0 format
    """
    # Clone the message to avoid modifying the original
    result = message.copy()
    
    # TODO: Implement conversion logic when v0.4.0 is defined
    
    return result