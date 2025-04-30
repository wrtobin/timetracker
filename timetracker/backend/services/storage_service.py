"""
Storage service for managing file operations and other backends.
"""
from abc import ABC, abstractmethod
import os
import csv
import uuid
import json
import logging
import appdirs
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

from ...protocol.generated_schema import (
    StorageInfo, TimeEntry, Response, 
    LoadStorageRequest, SaveStorageRequest, SaveStorageAsRequest,
    NewStorageRequest, GetCurrentStorageRequest, GetStorageListRequest,
    HasUnsavedChangesRequest, ClearStorageRequest
)

logger = logging.getLogger(__name__)


class StorageServiceInterface(ABC):
    """Interface for storage service implementations."""
    
    @abstractmethod
    def load_storage(self, request: LoadStorageRequest) -> Response:
        """Load data from a storage location."""
        pass
        
    @abstractmethod
    def save_storage(self, request: SaveStorageRequest) -> Response:
        """Save data to the current storage location."""
        pass
        
    @abstractmethod
    def save_storage_as(self, request: SaveStorageAsRequest) -> Response:
        """Save data to a new storage location."""
        pass
        
    @abstractmethod
    def new_storage(self, request: NewStorageRequest) -> Response:
        """Create a new empty storage."""
        pass
        
    @abstractmethod
    def get_current_storage(self, request: GetCurrentStorageRequest) -> Response:
        """Get information about the current storage."""
        pass
        
    @abstractmethod
    def get_storage_list(self, request: GetStorageListRequest) -> Response:
        """Get a list of available storages."""
        pass
        
    @abstractmethod
    def has_unsaved_changes(self, request: HasUnsavedChangesRequest) -> Response:
        """Check if there are unsaved changes."""
        pass
        
    @abstractmethod
    def clear_storage(self, request: ClearStorageRequest) -> Response:
        """Clear the current storage."""
        pass
    
    @abstractmethod
    def set_entries(self, entries: List[TimeEntry]) -> None:
        """Set the current entries (used by TimeEntryService)."""
        pass
    
    @abstractmethod
    def get_entries(self) -> List[TimeEntry]:
        """Get the current entries (used by TimeEntryService)."""
        pass


class FileStorageService(StorageServiceInterface):
    """Implementation of StorageService that uses file storage."""
    
    def __init__(self):
        self._entries: List[TimeEntry] = []
        self._current_file: Optional[str] = None
        self._has_unsaved_changes: bool = False
        self._recent_files: List[str] = []
        self._max_recent_files: int = 5
        
        # Set up config directory and file for persistence
        self.app_name = "TimeTracker"
        self.app_author = "TimeTracker"
        self.config_dir = Path(appdirs.user_config_dir(self.app_name, self.app_author))
        self.config_file = self.config_dir / "backend_settings.json"
        
        # Load recent files from persistent storage
        self._load_settings()
    
    def _load_settings(self):
        """Load settings from storage."""
        try:
            # Create config directory if it doesn't exist
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # Load config if it exists
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    
                self._recent_files = config.get('recent_files', [])
                self._max_recent_files = config.get('max_recent_files', 5)
                
                # Filter to only valid files that still exist
                self._recent_files = [f for f in self._recent_files if os.path.exists(f)]
                logger.info(f"Loaded {len(self._recent_files)} recent files from config")
            else:
                logger.info("No config file found, using defaults")
                self._recent_files = []
                self._max_recent_files = 5
        except Exception as e:
            logger.exception(f"Error loading settings: {e}")
            # Use defaults if loading fails
            self._recent_files = []
            self._max_recent_files = 5
    
    def _save_settings(self):
        """Save settings to persistent storage."""
        try:
            # Create config directory if it doesn't exist
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # Save config
            config = {
                'recent_files': self._recent_files,
                'max_recent_files': self._max_recent_files
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
                
            logger.info(f"Saved {len(self._recent_files)} recent files to config")
        except Exception as e:
            logger.exception(f"Error saving settings: {e}")
    
    def set_entries(self, entries: List[TimeEntry]) -> None:
        """Set the current entries."""
        self._entries = entries.copy()
        self._has_unsaved_changes = True
    
    def get_entries(self) -> List[TimeEntry]:
        """Get the current entries."""
        return self._entries.copy()
    
    def load_storage(self, request: LoadStorageRequest) -> Response:
        """Load data from a file."""
        try:
            storage_id = request.payload.get('storage_id')
            storage_type = request.payload.get('storage_type', 'file')
            
            if storage_type != 'file':
                return Response(
                    msg_type="ERROR",
                    msg_id=str(uuid.uuid4()),
                    request_id=request.msg_id,
                    success=False,
                    error_message=f"Unsupported storage type: {storage_type}"
                )
            
            if not os.path.exists(storage_id):
                return Response(
                    msg_type="ERROR",
                    msg_id=str(uuid.uuid4()),
                    request_id=request.msg_id,
                    success=False,
                    error_message=f"File not found: {storage_id}"
                )
                
            entries = []
            with open(storage_id, newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None)  # Skip header
                
                for row in reader:
                    if len(row) == 2:  # Old format with only timestamp and description
                        entries.append(TimeEntry(
                            id=str(uuid.uuid4()),
                            start_time=row[0],
                            description=row[1],
                            category=""
                        ))
                    elif len(row) >= 3:  # New format with timestamp, category, description
                        entries.append(TimeEntry(
                            id=str(uuid.uuid4()),
                            start_time=row[0],
                            category=row[1],
                            description=row[2]
                        ))
            
            self._entries = entries
            self._current_file = storage_id
            self._has_unsaved_changes = False
            
            # Add to recent files
            self._add_to_recent_files(storage_id)
            
            # Create storage info for response
            storage_info = StorageInfo(
                storage_id=storage_id,
                storage_type="file",
                display_name=os.path.basename(storage_id),
                modified=False
            )
            
            return Response(
                msg_type="SUCCESS",
                msg_id=str(uuid.uuid4()),
                request_id=request.msg_id,
                success=True,
                payload={"storage_info": storage_info.dict()}
            )
        except Exception as e:
            logger.exception(f"Error loading from file: {storage_id}")
            return Response(
                msg_type="ERROR",
                msg_id=str(uuid.uuid4()),
                request_id=request.msg_id,
                success=False,
                error_message=str(e)
            )
    
    def save_storage(self, request: SaveStorageRequest) -> Response:
        """Save data to the current storage location."""
        try:
            storage_id = request.payload.get('storage_id', self._current_file)
            
            if not storage_id:
                return Response(
                    msg_type="ERROR",
                    msg_id=str(uuid.uuid4()),
                    request_id=request.msg_id,
                    success=False,
                    error_message="No current storage to save to"
                )
                
            result = self._save_to_file(storage_id)
            if not result:
                return Response(
                    msg_type="ERROR",
                    msg_id=str(uuid.uuid4()),
                    request_id=request.msg_id,
                    success=False,
                    error_message=f"Error saving to file: {storage_id}"
                )
                
            # Create storage info for response
            storage_info = StorageInfo(
                storage_id=storage_id,
                storage_type="file",
                display_name=os.path.basename(storage_id),
                modified=False
            )
            
            return Response(
                msg_type="SUCCESS",
                msg_id=str(uuid.uuid4()),
                request_id=request.msg_id,
                success=True,
                payload={"storage_info": storage_info.dict()}
            )
        except Exception as e:
            logger.exception(f"Error saving to file: {storage_id if 'storage_id' in locals() else 'unknown'}")
            return Response(
                msg_type="ERROR",
                msg_id=str(uuid.uuid4()),
                request_id=request.msg_id,
                success=False,
                error_message=str(e)
            )
    
    def save_storage_as(self, request: SaveStorageAsRequest) -> Response:
        """Save data to a new storage location."""
        try:
            storage_id = request.payload.get('storage_id')
            storage_type = request.payload.get('storage_type', 'file')
            
            if storage_type != 'file':
                return Response(
                    msg_type="ERROR",
                    msg_id=str(uuid.uuid4()),
                    request_id=request.msg_id,
                    success=False,
                    error_message=f"Unsupported storage type: {storage_type}"
                )
                
            if not storage_id:
                return Response(
                    msg_type="ERROR",
                    msg_id=str(uuid.uuid4()),
                    request_id=request.msg_id,
                    success=False,
                    error_message="No storage ID provided"
                )
                
            result = self._save_to_file(storage_id)
            if not result:
                return Response(
                    msg_type="ERROR",
                    msg_id=str(uuid.uuid4()),
                    request_id=request.msg_id,
                    success=False,
                    error_message=f"Error saving to file: {storage_id}"
                )
                
            # Add to recent files
            self._add_to_recent_files(storage_id)
                
            # Create storage info for response
            storage_info = StorageInfo(
                storage_id=storage_id,
                storage_type="file",
                display_name=os.path.basename(storage_id),
                modified=False
            )
            
            return Response(
                msg_type="SUCCESS",
                msg_id=str(uuid.uuid4()),
                request_id=request.msg_id,
                success=True,
                payload={"storage_info": storage_info.dict()}
            )
        except Exception as e:
            logger.exception(f"Error saving to file: {storage_id if 'storage_id' in locals() else 'unknown'}")
            return Response(
                msg_type="ERROR",
                msg_id=str(uuid.uuid4()),
                request_id=request.msg_id,
                success=False,
                error_message=str(e)
            )
    
    def new_storage(self, request: NewStorageRequest) -> Response:
        """Create a new empty storage."""
        try:
            storage_type = request.payload.get('storage_type', 'file')
            
            if storage_type != 'file':
                return Response(
                    msg_type="ERROR",
                    msg_id=str(uuid.uuid4()),
                    request_id=request.msg_id,
                    success=False,
                    error_message=f"Unsupported storage type: {storage_type}"
                )
                
            # Clear entries and set current file to None
            self._entries = []
            self._current_file = None
            self._has_unsaved_changes = False
            
            # Create storage info for response (temporary storage)
            storage_info = StorageInfo(
                storage_id="",
                storage_type="memory",
                display_name="New storage",
                modified=False
            )
            
            return Response(
                msg_type="SUCCESS",
                msg_id=str(uuid.uuid4()),
                request_id=request.msg_id,
                success=True,
                payload={"storage_info": storage_info.dict()}
            )
        except Exception as e:
            logger.exception("Error creating new storage")
            return Response(
                msg_type="ERROR",
                msg_id=str(uuid.uuid4()),
                request_id=request.msg_id,
                success=False,
                error_message=str(e)
            )
    
    def get_current_storage(self, request: GetCurrentStorageRequest) -> Response:
        """Get information about the current storage."""
        try:
            if not self._current_file:
                # Return temp storage info
                storage_info = StorageInfo(
                    storage_id="",
                    storage_type="memory",
                    display_name="Unsaved storage",
                    modified=self._has_unsaved_changes
                )
            else:
                storage_info = StorageInfo(
                    storage_id=self._current_file,
                    storage_type="file",
                    display_name=os.path.basename(self._current_file),
                    modified=self._has_unsaved_changes
                )
            
            return Response(
                msg_type="SUCCESS",
                msg_id=str(uuid.uuid4()),
                request_id=request.msg_id,
                success=True,
                payload={"storage_info": storage_info.dict()}
            )
        except Exception as e:
            logger.exception("Error getting current storage info")
            return Response(
                msg_type="ERROR",
                msg_id=str(uuid.uuid4()),
                request_id=request.msg_id,
                success=False,
                error_message=str(e)
            )
    
    def get_storage_list(self, request: GetStorageListRequest) -> Response:
        """Get a list of recent files."""
        try:
            storage_type = request.payload.get('storage_type', 'all')
            limit = request.payload.get('limit', self._max_recent_files)
            
            # For now, only file type is supported
            if storage_type not in ['file', 'all']:
                return Response(
                    msg_type="SUCCESS",
                    msg_id=str(uuid.uuid4()),
                    request_id=request.msg_id,
                    success=True,
                    payload={"storage_list": []}
                )
                
            # Filter to only valid files that still exist
            valid_files = [f for f in self._recent_files if os.path.exists(f)]
            self._recent_files = valid_files  # Update stored list
            
            # Limit the number of files
            recent_files = valid_files[:limit]
            
            # Convert to StorageInfo objects
            storage_list = []
            for file_path in recent_files:
                storage_list.append(StorageInfo(
                    storage_id=file_path,
                    storage_type="file",
                    display_name=os.path.basename(file_path),
                    modified=False
                ).dict())
                
            return Response(
                msg_type="SUCCESS",
                msg_id=str(uuid.uuid4()),
                request_id=request.msg_id,
                success=True,
                payload={"storage_list": storage_list}
            )
        except Exception as e:
            logger.exception("Error getting storage list")
            return Response(
                msg_type="ERROR",
                msg_id=str(uuid.uuid4()),
                request_id=request.msg_id,
                success=False,
                error_message=str(e)
            )
    
    def has_unsaved_changes(self, request: HasUnsavedChangesRequest) -> Response:
        """Check if there are unsaved changes."""
        try:
            return Response(
                msg_type="SUCCESS",
                msg_id=str(uuid.uuid4()),
                request_id=request.msg_id,
                success=True,
                payload={"has_unsaved_changes": self._has_unsaved_changes}
            )
        except Exception as e:
            logger.exception("Error checking unsaved changes")
            return Response(
                msg_type="ERROR",
                msg_id=str(uuid.uuid4()),
                request_id=request.msg_id,
                success=False,
                error_message=str(e)
            )
    
    def clear_storage(self, request: ClearStorageRequest) -> Response:
        """Clear the current storage."""
        try:
            # Reset state
            self._entries = []
            self._current_file = None
            self._has_unsaved_changes = False
            
            # Create storage info for response (temporary storage)
            storage_info = StorageInfo(
                storage_id="",
                storage_type="memory",
                display_name="New storage",
                modified=False
            )
            
            return Response(
                msg_type="SUCCESS",
                msg_id=str(uuid.uuid4()),
                request_id=request.msg_id,
                success=True,
                payload={"storage_info": storage_info.dict()}
            )
        except Exception as e:
            logger.exception("Error clearing storage")
            return Response(
                msg_type="ERROR",
                msg_id=str(uuid.uuid4()),
                request_id=request.msg_id,
                success=False,
                error_message=str(e)
            )
    
    def _save_to_file(self, filepath: str) -> bool:
        """Save entries to a file."""
        try:
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "category", "description"])
                
                for entry in self._entries:
                    writer.writerow([
                        entry.start_time,
                        entry.category or "",
                        entry.description or ""
                    ])
            
            self._current_file = filepath
            self._has_unsaved_changes = False
            return True
        except Exception as e:
            logger.exception(f"Error saving to file: {filepath}")
            return False
    
    def _add_to_recent_files(self, filepath: str) -> None:
        """Add a file to the recent files list."""
        # Remove if already in list
        if filepath in self._recent_files:
            self._recent_files.remove(filepath)
            
        # Add to front of list
        self._recent_files.insert(0, filepath)
        
        # Trim if needed
        if len(self._recent_files) > self._max_recent_files:
            self._recent_files = self._recent_files[:self._max_recent_files]
            
        # Save updated recent files list
        self._save_settings()