"""
ServiceManager for managing backend services and handling message routing.
"""
import logging
from typing import Dict, Optional, Type, Tuple

from ..protocol.message_bus import MessageBus
from ..protocol.compatibility import check_compatibility
from ..protocol.version import VERSION as PROTOCOL_VERSION
from .version import VERSION as BACKEND_VERSION
from .services.time_entry_service import TimeEntryServiceInterface, CSVTimeEntryService
from .services.storage_service import StorageServiceInterface, FileStorageService

logger = logging.getLogger(__name__)


class ServiceManager:
    """
    Manages backend services and handles message routing.
    """
    
    def __init__(self):
        self._message_bus: Optional[MessageBus] = None
        self._time_entry_service: Optional[TimeEntryServiceInterface] = None
        self._storage_service: Optional[StorageServiceInterface] = None
        self._protocol_version: str = PROTOCOL_VERSION
        self._backend_version: str = BACKEND_VERSION
        
    def initialize(self, message_bus: MessageBus, frontend_version: Optional[str] = None) -> Tuple[bool, str]:
        """
        Initialize the service manager with a message bus.
        
        Args:
            message_bus: The message bus to use for communication
            frontend_version: The version of the frontend component
            
        Returns:
            A tuple of (success, error_message)
        """
        # Check version compatibility
        if frontend_version:
            is_compatible = check_compatibility(frontend_version, self._backend_version)
            if not is_compatible:
                error_msg = (
                    f"Incompatible versions: frontend {frontend_version}, "
                    f"backend {self._backend_version}, protocol {self._protocol_version}"
                )
                logger.error(error_msg)
                return False, error_msg
            
            # Log the protocol version being used
            logger.info(
                f"Using protocol version {self._protocol_version} "
                f"for frontend {frontend_version} and backend {self._backend_version}"
            )
        
        self._message_bus = message_bus
        self._initialize_services()
        self._register_handlers()
        return True, ""
        
    def _initialize_services(self) -> None:
        """Initialize backend services."""
        # Initialize storage service first, since time entry service will use it
        self._storage_service = FileStorageService()
        
        # Initialize time entry service with storage service
        self._time_entry_service = CSVTimeEntryService(self._storage_service)
        
    def _register_handlers(self) -> None:
        """Register message handlers with the message bus."""
        if not self._message_bus:
            logger.error("Cannot register handlers: message bus is not initialized")
            return
            
        # Register TimeEntryService handlers
        self._message_bus.register_handler(
            "GET_TIME_ENTRIES",
            self._time_entry_service.get_time_entries
        )
        self._message_bus.register_handler(
            "ADD_TIME_ENTRY",
            self._time_entry_service.add_time_entry
        )
        self._message_bus.register_handler(
            "UPDATE_TIME_ENTRY",
            self._time_entry_service.update_time_entry
        )
        self._message_bus.register_handler(
            "DELETE_TIME_ENTRY",
            self._time_entry_service.delete_time_entry
        )
        self._message_bus.register_handler(
            "GET_CATEGORIES",
            self._time_entry_service.get_categories
        )
        
        # Register StorageService handlers
        self._message_bus.register_handler(
            "LOAD_STORAGE",
            self._storage_service.load_storage
        )
        self._message_bus.register_handler(
            "SAVE_STORAGE",
            self._storage_service.save_storage
        )
        self._message_bus.register_handler(
            "SAVE_STORAGE_AS",
            self._storage_service.save_storage_as
        )
        self._message_bus.register_handler(
            "NEW_STORAGE",
            self._storage_service.new_storage
        )
        self._message_bus.register_handler(
            "GET_CURRENT_STORAGE",
            self._storage_service.get_current_storage
        )
        self._message_bus.register_handler(
            "GET_STORAGE_LIST",
            self._storage_service.get_storage_list
        )
        self._message_bus.register_handler(
            "HAS_UNSAVED_CHANGES",
            self._storage_service.has_unsaved_changes
        )
        self._message_bus.register_handler(
            "CLEAR_STORAGE",
            self._storage_service.clear_storage
        )
    
    @property
    def time_entry_service(self) -> TimeEntryServiceInterface:
        """Get the time entry service."""
        if not self._time_entry_service:
            raise RuntimeError("TimeEntryService is not initialized")
        return self._time_entry_service
    
    @property
    def storage_service(self) -> StorageServiceInterface:
        """Get the storage service."""
        if not self._storage_service:
            raise RuntimeError("StorageService is not initialized")
        return self._storage_service
        
    @property
    def protocol_version(self) -> str:
        """Get the protocol version being used."""
        return self._protocol_version