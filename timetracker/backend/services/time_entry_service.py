"""
TimeEntryService for managing time entries.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Set
from datetime import datetime
import uuid
import logging

from ...protocol.generated_schema import (
    TimeEntry, Response,
    GetTimeEntriesRequest, AddTimeEntryRequest,
    UpdateTimeEntryRequest, DeleteTimeEntryRequest,
    GetCategoriesRequest
)
from .storage_service import StorageServiceInterface

logger = logging.getLogger(__name__)


class TimeEntryServiceInterface(ABC):
    """Interface for TimeEntryService implementations."""
    
    @abstractmethod
    def get_time_entries(self, request: GetTimeEntriesRequest) -> Response:
        """Get all time entries."""
        pass
        
    @abstractmethod
    def add_time_entry(self, request: AddTimeEntryRequest) -> Response:
        """Add a new time entry."""
        pass
        
    @abstractmethod
    def update_time_entry(self, request: UpdateTimeEntryRequest) -> Response:
        """Update an existing time entry."""
        pass
        
    @abstractmethod
    def delete_time_entry(self, request: DeleteTimeEntryRequest) -> Response:
        """Delete a time entry."""
        pass
        
    @abstractmethod
    def get_categories(self, request: GetCategoriesRequest) -> Response:
        """Get all unique categories."""
        pass


class CSVTimeEntryService(TimeEntryServiceInterface):
    """Implementation of TimeEntryService that works with the storage service."""
    
    def __init__(self, storage_service: StorageServiceInterface):
        self._storage_service = storage_service
        
    def get_time_entries(self, request: GetTimeEntriesRequest) -> Response:
        """Get all time entries."""
        try:
            # Get entries from storage service
            entries = self._storage_service.get_entries()
            
            # Return a copy of entries with IDs
            entries_with_ids = []
            for idx, entry in enumerate(entries):
                entry_dict = entry.dict()
                entry_dict['id'] = str(idx)  # Use index as ID for display
                entries_with_ids.append(entry_dict)
                
            return Response(
                msg_type="SUCCESS",
                msg_id=str(uuid.uuid4()),
                request_id=request.msg_id,
                success=True,
                payload={"time_entries": entries_with_ids}
            )
        except Exception as e:
            logger.exception("Error getting time entries")
            return Response(
                msg_type="ERROR",
                msg_id=str(uuid.uuid4()),
                request_id=request.msg_id,
                success=False,
                error_message=str(e)
            )
        
    def add_time_entry(self, request: AddTimeEntryRequest) -> Response:
        """Add a new time entry."""
        try:
            entry_data = request.payload.get('time_entry', {})
            
            # Create a new TimeEntry with current timestamp if not provided
            timestamp = entry_data.get('end_time', datetime.now().isoformat())
            
            new_entry = TimeEntry(
                id=str(uuid.uuid4()),
                end_time=timestamp,
                category=entry_data.get('category', ''),
                description=entry_data.get('description', '')
            )
            
            # Get current entries and add the new one
            entries = self._storage_service.get_entries()
            entries.append(new_entry)
            self._storage_service.set_entries(entries)
            
            return Response(
                msg_type="SUCCESS",
                msg_id=str(uuid.uuid4()),
                request_id=request.msg_id,
                success=True,
                payload={"time_entry": new_entry.dict()}
            )
        except Exception as e:
            logger.exception("Error adding time entry")
            return Response(
                msg_type="ERROR",
                msg_id=str(uuid.uuid4()),
                request_id=request.msg_id,
                success=False,
                error_message=str(e)
            )
        
    def update_time_entry(self, request: UpdateTimeEntryRequest) -> Response:
        """Update an existing time entry."""
        try:
            entry_data = request.payload.get('time_entry', {})
            entry_id = entry_data.get('id')
            
            if not entry_id:
                return Response(
                    msg_type="ERROR",
                    msg_id=str(uuid.uuid4()),
                    request_id=request.msg_id,
                    success=False,
                    error_message="No entry ID provided"
                )
                
            # Get current entries from storage service
            entries = self._storage_service.get_entries()
            
            # Try to find by index or by ID
            try:
                idx = int(entry_id)
                if idx >= 0 and idx < len(entries):
                    # Create an updated entry
                    updated_entry = TimeEntry(
                        id=entries[idx].id,
                        end_time=entry_data.get('end_time', getattr(entries[idx], 'end_time', None)),
                        category=entry_data.get('category', entries[idx].category),
                        description=entry_data.get('description', entries[idx].description)
                    )
                    
                    # Update in list
                    entries[idx] = updated_entry
                    self._storage_service.set_entries(entries)
                    
                    return Response(
                        msg_type="SUCCESS",
                        msg_id=str(uuid.uuid4()),
                        request_id=request.msg_id,
                        success=True,
                        payload={"time_entry": updated_entry.dict()}
                    )
            except ValueError:
                # Not an integer ID, try as UUID
                for idx, entry in enumerate(entries):
                    if str(entry.id) == entry_id:
                        # Update the entry
                        updated_entry = TimeEntry(
                            id=entry_id,
                            end_time=entry_data.get('end_time', getattr(entry, 'end_time', None)),
                            category=entry_data.get('category', entry.category),
                            description=entry_data.get('description', entry.description)
                        )
                        
                        entries[idx] = updated_entry
                        self._storage_service.set_entries(entries)
                        
                        return Response(
                            msg_type="SUCCESS",
                            msg_id=str(uuid.uuid4()),
                            request_id=request.msg_id,
                            success=True,
                            payload={"time_entry": updated_entry.dict()}
                        )
            
            # If we get here, no entry was found
            return Response(
                msg_type="ERROR",
                msg_id=str(uuid.uuid4()),
                request_id=request.msg_id,
                success=False,
                error_message=f"Entry with ID {entry_id} not found"
            )
        except Exception as e:
            logger.exception("Error updating time entry")
            return Response(
                msg_type="ERROR",
                msg_id=str(uuid.uuid4()),
                request_id=request.msg_id,
                success=False,
                error_message=str(e)
            )
        
    def delete_time_entry(self, request: DeleteTimeEntryRequest) -> Response:
        """Delete a time entry."""
        try:
            entry_id = request.payload.get('entry_id')
            
            if not entry_id:
                return Response(
                    msg_type="ERROR",
                    msg_id=str(uuid.uuid4()),
                    request_id=request.msg_id,
                    success=False,
                    error_message="No entry ID provided"
                )
                
            # Get current entries
            entries = self._storage_service.get_entries()
            
            # Try to find by index or by ID
            try:
                idx = int(entry_id)
                if idx >= 0 and idx < len(entries):
                    # Delete by index
                    del entries[idx]
                    self._storage_service.set_entries(entries)
                    
                    return Response(
                        msg_type="SUCCESS",
                        msg_id=str(uuid.uuid4()),
                        request_id=request.msg_id,
                        success=True
                    )
            except ValueError:
                # Not an integer ID, try as UUID
                for idx, entry in enumerate(entries):
                    if str(entry.id) == entry_id:
                        # Delete the entry
                        del entries[idx]
                        self._storage_service.set_entries(entries)
                        
                        return Response(
                            msg_type="SUCCESS",
                            msg_id=str(uuid.uuid4()),
                            request_id=request.msg_id,
                            success=True
                        )
            
            # If we get here, no entry was found
            return Response(
                msg_type="ERROR",
                msg_id=str(uuid.uuid4()),
                request_id=request.msg_id,
                success=False,
                error_message=f"Entry with ID {entry_id} not found"
            )
        except Exception as e:
            logger.exception("Error deleting time entry")
            return Response(
                msg_type="ERROR",
                msg_id=str(uuid.uuid4()),
                request_id=request.msg_id,
                success=False,
                error_message=str(e)
            )
        
    def get_categories(self, request: GetCategoriesRequest) -> Response:
        """Get all unique categories."""
        try:
            entries = self._storage_service.get_entries()
            categories: Set[str] = set()
            
            for entry in entries:
                if entry.category:
                    categories.add(entry.category)
                    
            return Response(
                msg_type="SUCCESS",
                msg_id=str(uuid.uuid4()),
                request_id=request.msg_id,
                success=True,
                payload={"categories": sorted(list(categories))}
            )
        except Exception as e:
            logger.exception("Error getting categories")
            return Response(
                msg_type="ERROR",
                msg_id=str(uuid.uuid4()),
                request_id=request.msg_id,
                success=False,
                error_message=str(e)
            )