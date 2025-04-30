"""
Version information for the TimeTracker frontend.
"""

# Version of this frontend
VERSION = "0.3.0"

# Protocol version(s) supported by this frontend
SUPPORTED_PROTOCOL_VERSIONS = ["0.3.0"]

def get_version():
    """Return the current version."""
    return VERSION

def get_supported_protocol_versions():
    """Return the protocol versions supported by this frontend."""
    return SUPPORTED_PROTOCOL_VERSIONS
