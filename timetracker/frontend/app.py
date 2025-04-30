"""
Application entry point and initialization.
"""

import os
import logging
import tkinter as tk
import uuid
from pathlib import Path

from ..protocol.message_bus import MessageBus
from ..backend.service_manager import ServiceManager
from .controllers.ui_controller import UIController
from .time_tracker_ui import TimeTrackerUI
from ..protocol.generated_schema import GetStorageListRequest, LoadStorageRequest

logger = logging.getLogger(__name__)


class Application:
    """Main application class for TimeTracker."""
    
    def __init__(self):
        """Initialize the application."""
        self.root = None
        self.message_bus = None
        self.service_manager = None
        self.ui_controller = None
        self.ui = None
        
    def run(self):
        """Run the application."""
        try:
            # Create the root window
            self.root = tk.Tk()
            
            # Initialize the message bus
            self.message_bus = MessageBus()
            
            # Initialize the service manager
            self.service_manager = ServiceManager()
            self.service_manager.initialize(self.message_bus)
            
            # Initialize the UI controller - only pass message_bus
            self.ui_controller = UIController(self.message_bus)
            
            # Initialize the UI
            self.ui = TimeTrackerUI(self.root, self.ui_controller)
            
            # Load last file if available, using message bus instead of direct calls
            self._load_last_file()
            
            # Run the main loop
            self.root.mainloop()
        except Exception as e:
            logger.exception(f"Error running application: {e}")
            
    def _load_last_file(self):
        """Load the last used file if available."""
        try:
            # Get list of recent files using the message bus
            request = GetStorageListRequest(
                msg_id=str(uuid.uuid4()),
                storage_type="file",
                limit=1
            )
            response = self.message_bus.send(request)
            
            if response and response.success:
                storage_list = response.payload.get("storage_list", [])
                if storage_list:
                    # Get the most recent file and load it
                    most_recent_file = storage_list[0]
                    storage_id = most_recent_file.get("storage_id")
                    
                    if storage_id and os.path.exists(storage_id):
                        load_request = LoadStorageRequest(
                            msg_id=str(uuid.uuid4()),
                            storage_id=storage_id,
                            storage_type="file"
                        )
                        load_response = self.message_bus.send(load_request)
                        
                        # If load was successful, tell the UI controller to update its state
                        if load_response and load_response.success:
                            logger.info(f"Successfully loaded file: {storage_id}")
                            # Make sure UI controller knows about the current file
                            self.ui_controller.set_current_file(storage_id)
                            # Ensure UI refreshes entries after loading
                            if self.ui:
                                self.ui._refresh_entries()
                                self.ui._update_window_title()
                        else:
                            logger.warning(f"Failed to load file: {storage_id}")
                    else:
                        logger.warning(f"Most recent file does not exist: {storage_id}")
                else:
                    logger.info("No recent files found.")
            else:
                logger.warning("Failed to get storage list.")
            
        except Exception as e:
            logger.exception(f"Error loading last file: {e}")
            

def create_and_run_app(debug_mode=False):
    """Initialize and run the application."""
    app = Application()
    app.run()


if __name__ == "__main__":
    create_and_run_app()