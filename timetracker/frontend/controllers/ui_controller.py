"""
UIController for handling frontend interactions with backend services.
"""

import os
import uuid
import logging
from typing import List, Dict, Any, Optional

from ...protocol.message_bus import MessageBus
from ...protocol.generated_schema import (
    TimeEntry, 
    GetTimeEntriesRequest,
    AddTimeEntryRequest,
    UpdateTimeEntryRequest,
    DeleteTimeEntryRequest,
    GetCategoriesRequest,
    LoadStorageRequest,
    SaveStorageRequest,
    SaveStorageAsRequest,
    NewStorageRequest,
    GetCurrentStorageRequest,
    GetStorageListRequest,
    HasUnsavedChangesRequest,
    ClearStorageRequest,
    Response,
    StorageListFilterPayload
)

logger = logging.getLogger(__name__)


class UIController:
    """
    Controller for handling interactions between UI and backend services.
    """
    
    def __init__(self, message_bus: MessageBus):
        """
        Initialize the UIController.
        
        Args:
            message_bus: The message bus for communication
        """
        self._message_bus = message_bus
        
    def get_time_entries(self) -> List[Dict[str, Any]]:
        """
        Get all time entries.
        
        Returns:
            List of time entry dictionaries
        """
        # Create and send request through message bus
        request = GetTimeEntriesRequest(msg_id=str(uuid.uuid4()))
        response = self._message_bus.send(request)
        
        if not response or not response.success:
            logger.error(f"Failed to get time entries: {response.error_message if response else 'No response'}")
            return []
            
        return response.payload.get("time_entries", [])
        
    def add_time_entry(self, timestamp: str, category: str, description: str) -> Optional[str]:
        """
        Add a new time entry.
        
        Args:
            timestamp: The timestamp of the entry
            category: The category of the entry
            description: The description of the entry
            
        Returns:
            Entry ID if successful, None if failed
        """
        # Create time entry
        time_entry = {
            "end_time": timestamp,  # Using end_time consistently
            "category": category,
            "description": description
        }
        
        # Create and send request through message bus
        request = AddTimeEntryRequest(msg_id=str(uuid.uuid4()), time_entry=time_entry)
        response = self._message_bus.send(request)
        
        if not response or not response.success:
            logger.error(f"Failed to add time entry: {response.error_message if response else 'No response'}")
            return None
            
        # Return the ID of the added entry
        return response.payload.get("time_entry", {}).get("id")
        
    def update_time_entry(self, entry_id: str, timestamp: str, category: str, description: str) -> bool:
        """
        Update an existing time entry.
        
        Args:
            entry_id: The ID of the entry to update
            timestamp: The timestamp of the entry
            category: The category of the entry
            description: The description of the entry
            
        Returns:
            True if successful, False if failed
        """
        # Create time entry
        time_entry = {
            "id": entry_id,
            "end_time": timestamp,  # Using end_time consistently
            "category": category,
            "description": description
        }
        
        # Create and send request through message bus
        request = UpdateTimeEntryRequest(msg_id=str(uuid.uuid4()), time_entry=time_entry)
        response = self._message_bus.send(request)
        
        if not response or not response.success:
            logger.error(f"Failed to update time entry: {response.error_message if response else 'No response'}")
            return False
            
        return True
        
    def delete_time_entry(self, entry_id: str) -> bool:
        """
        Delete a time entry.
        
        Args:
            entry_id: The ID of the entry to delete
            
        Returns:
            True if successful, False if failed
        """
        # Create and send request through message bus
        request = DeleteTimeEntryRequest(msg_id=str(uuid.uuid4()), entry_id=entry_id)
        response = self._message_bus.send(request)
        
        if not response or not response.success:
            logger.error(f"Failed to delete time entry: {response.error_message if response else 'No response'}")
            return False
            
        return True
        
    def get_categories(self) -> List[str]:
        """
        Get all unique categories.
        
        Returns:
            List of category strings
        """
        # Create and send request through message bus
        request = GetCategoriesRequest(msg_id=str(uuid.uuid4()))
        response = self._message_bus.send(request)
        
        if not response or not response.success:
            logger.error(f"Failed to get categories: {response.error_message if response else 'No response'}")
            return []
            
        return response.payload.get("categories", []) if response.payload else []
        
    def load_file(self, filepath: str) -> bool:
        """
        Load time entries from a file.
        
        Args:
            filepath: The path to the file
            
        Returns:
            True if successful, False if failed
        """
        # Create and send request through message bus
        request = LoadStorageRequest(
            msg_id=str(uuid.uuid4()),
            storage_id=filepath,
            storage_type="file"
        )
        response = self._message_bus.send(request)
        
        if not response or not response.success:
            logger.error(f"Failed to load file: {response.error_message if response else 'No response'}")
            return False
            
        return True
        
    def save_file(self, filepath: str) -> bool:
        """
        Save time entries to a file.
        
        Args:
            filepath: The path to the file
            
        Returns:
            True if successful, False if failed
        """
        # Create and send request through message bus
        request = SaveStorageRequest(
            msg_id=str(uuid.uuid4()),
            storage_id=filepath
        )
        response = self._message_bus.send(request)
        
        if not response or not response.success:
            logger.error(f"Failed to save file: {response.error_message if response else 'No response'}")
            return False
            
        return True
        
    def has_unsaved_changes(self) -> bool:
        """
        Check if there are unsaved changes.
        
        Returns:
            True if there are unsaved changes, False otherwise
        """
        # Create and send request through message bus
        request = HasUnsavedChangesRequest(msg_id=str(uuid.uuid4()))
        response = self._message_bus.send(request)
        
        if not response or not response.success:
            logger.error(f"Failed to check for unsaved changes: {response.error_message if response else 'No response'}")
            return False
            
        return response.payload.get("has_unsaved_changes", False) if response.payload else False
        
    def get_current_file(self) -> Optional[str]:
        """
        Get the current file path.
        
        Returns:
            The current file path, or None if no file is loaded
        """
        # Create and send request through message bus
        request = GetCurrentStorageRequest(msg_id=str(uuid.uuid4()))
        response = self._message_bus.send(request)
        
        if not response or not response.success:
            logger.error(f"Failed to get current file: {response.error_message if response else 'No response'}")
            return None
            
        storage_info = response.payload.get("storage_info", {}) if response.payload else {}
        if storage_info.get("storage_type") == "file":
            return storage_info.get("storage_id")
        return None
        
    def clear(self) -> bool:
        """
        Clear all entries and reset to a new file.
        
        Returns:
            True if successful, False if failed
        """
        # Create and send request through message bus
        request = ClearStorageRequest(msg_id=str(uuid.uuid4()))
        response = self._message_bus.send(request)
        
        if not response or not response.success:
            logger.error(f"Failed to clear storage: {response.error_message if response else 'No response'}")
            return False
            
        return True
        
    def get_recent_files(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get a list of recent files.
        
        Args:
            limit: Maximum number of recent files to return
            
        Returns:
            List of storage info dictionaries for recent files
        """
        # Import the required types
        from ...protocol.generated_schema import StorageListFilterPayload, FilterStorageType
        
        # Add debug logging
        logger.debug("Creating GetStorageListRequest with storage_type='file' and limit=%s", limit)
        
        # Create a properly typed StorageListFilterPayload object
        # Use literal "file" which will be converted to FilterStorageType by the model
        filter_payload = StorageListFilterPayload(storage_type="file", limit=limit)
        
        # Create the request with proper typing
        request = GetStorageListRequest(
            msg_id=str(uuid.uuid4()),
            # Use model_dump() for Pydantic v2 or dict() for Pydantic v1
            payload=filter_payload.dict() if hasattr(filter_payload, "dict") else filter_payload.model_dump()
        )
        
        # Debug log the request to verify payload is correctly set
        logger.debug(f"Request created: msg_type={request.msg_type}, payload={request.payload}")
        
        # Send the request
        response = self._message_bus.send(request)
        
        if not response or not response.success:
            logger.error(f"Failed to get recent files: {response.error_message if response else 'No response'}")
            return []
            
        return response.payload.get("storage_list", []) if response.payload else []