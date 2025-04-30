"""
Version information for the TimeTracker backend.
"""

# Version of this backend
VERSION = "0.3.0"

# Protocol version(s) supported by this backend
SUPPORTED_PROTOCOL_VERSIONS = ["0.3.0"]

def get_version():
    """Return the current version."""
    return VERSION

def get_supported_protocol_versions():
    """Return the protocol versions supported by this backend."""
    return SUPPORTED_PROTOCOL_VERSIONS
