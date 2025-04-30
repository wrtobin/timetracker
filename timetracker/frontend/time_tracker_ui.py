"""
TimeTrackerUI class that handles all UI components but delegates business logic to the controller.
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import logging
from datetime import datetime, time, timedelta
import appdirs
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

from .controllers.ui_controller import UIController

logger = logging.getLogger(__name__)


class TimeTrackerUI:
    """
    TimeTrackerUI class that handles all UI components but delegates business logic to the controller.
    """
    
    def __init__(self, root: tk.Tk, controller: UIController):
        """
        Initialize the TimeTrackerUI.
        
        Args:
            root: The Tkinter root window
            controller: The UI controller for business logic
        """
        self.root = root
        self.controller = controller
        
        # Initialize UI state
        self._setup_config()
        self._initialize_ui()
        self._setup_ui_components()
        self._apply_theme()
        
        # Load last file if available
        self._load_last_file()
        
        # Start scheduling
        self._schedule_next_reminder()
        
    def _setup_config(self):
        """Setup application configuration."""
        # App configuration management
        self.app_name = "TimeTracker"
        self.app_author = "TimeTracker"
        self.config_dir = Path(appdirs.user_config_dir(self.app_name, self.app_author))
        self.config_file = self.config_dir / "settings.json"
        
        self.default_config = {
            "recent_files": [],
            "max_recent_files": 5,
            "theme_mode": "dark",
            "start_time": "07:00",
            "end_time": "19:00",
            "interval": 30,
            "auto_record_seconds": 60,
            "last_category": "",
            "last_description": "",
            "current_file": None,
        }
        
        self.config = self._load_config()
        
        # Theme settings
        self.theme_mode = self.config.get("theme_mode", "dark")
        
        # File tracking settings
        self.recent_files = self.config.get("recent_files", [])
        self.max_recent_files = self.config.get("max_recent_files", 5)
        
        # Last used values for form auto-population
        self.last_category = self.config.get("last_category", "")
        self.last_description = self.config.get("last_description", "")
        
        # Docking settings
        self.is_docked = False
        self.dock_side = "right"  # Options: left, right, top, bottom
        self.dock_reveal_size = 5  # pixels visible when docked and hidden
        self.dock_animation_steps = 10
        self.dock_animation_ms = 10
        self.dock_width = 600  # Default width for docked window
        self._animation_after_id = None
        self._hover_check_id = None
        
        # Timer-related attributes
        self._after_id = None
        self._countdown_after_id = None
        self._auto_record_timer = None
        self.next_reminder = None
        
        # Default reminder settings
        self.start_time = self._parse_time_setting("start_time", "07:00")
        self.end_time = self._parse_time_setting("end_time", "19:00")
        self.interval = self.config.get("interval", 30)  # minutes
        self.auto_record_seconds = self.config.get("auto_record_seconds", 60)
        
        # UI state tracking
        self.currently_editing = False  # track if user is actively editing
        self.editing_item_id = None
        
    def _parse_time_setting(self, config_key: str, default_value: str) -> time:
        """Parse time setting from config."""
        try:
            time_str = self.config.get(config_key, default_value)
            h, m = map(int, time_str.split(":"))
            return time(h, m)
        except:
            h, m = map(int, default_value.split(":"))
            return time(h, m)
            
    def _initialize_ui(self):
        """Initialize the basic UI window."""
        self.root.title("Time Tracker")
        self.root.geometry("600x400")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Create menus
        self._create_menus()
        
    def _setup_ui_components(self):
        """Set up UI components."""
        # Main frame with background color
        main_frame = ttk.Frame(self.root, style='Main.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True)
        self.main_frame = main_frame
        
        # Entry section at the top
        self._create_entry_section(main_frame)
        
        # Table view
        self._create_table_view(main_frame)
        
        # Status bar with countdown timer and progress bar
        self._create_status_bar()
        
        # Configure window events for docking behavior
        self.root.bind("<Enter>", self._on_mouse_enter)
        self.root.bind("<Leave>", self._on_mouse_leave)
        
        # Update category list
        self._update_category_list()
        
    def _create_menus(self):
        """Create application menus."""
        menubar = tk.Menu(self.root)
        
        # File menu
        filem = tk.Menu(menubar, tearoff=0)
        filem.add_command(label="New", command=self._new_file)
        filem.add_command(label="Open...", command=self._load_data)
        filem.add_command(label="Save", command=self._save_current_file, accelerator="Ctrl+S")
        filem.add_command(label="Save As...", command=self._save_data)
        filem.add_separator()
        
        # Recent files submenu
        self.recent_files_menu = tk.Menu(filem, tearoff=0)
        filem.add_cascade(label="Recent Files", menu=self.recent_files_menu)
        self._update_recent_files_menu()
        
        filem.add_separator()
        filem.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=filem)
        
        # Bind Ctrl+S to save
        self.root.bind("<Control-s>", self._save_current_file)
        
        # Settings menu
        settings = tk.Menu(menubar, tearoff=0)
        settings.add_command(label="Configure Reminders…", command=self._open_settings)
        settings.add_separator()
        
        # Add docking options to menu
        self.docking_menu = tk.Menu(settings, tearoff=0)
        self.docking_menu.add_command(label="Dock to Left", command=lambda: self._set_docking("left"))
        self.docking_menu.add_command(label="Dock to Right", command=lambda: self._set_docking("right"))
        self.docking_menu.add_command(label="Dock to Top", command=lambda: self._set_docking("top"))
        self.docking_menu.add_command(label="Dock to Bottom", command=lambda: self._set_docking("bottom"))
        self.docking_menu.add_separator()
        self.docking_menu.add_command(label="Undock Window", command=self._undock_window)
        settings.add_cascade(label="Docking Options", menu=self.docking_menu)
        
        settings.add_command(label="Toggle Dark/Light Mode", command=self._toggle_theme)
        menubar.add_cascade(label="Settings", menu=settings)
        
        self.root.config(menu=menubar)
    
    def _create_entry_section(self, parent):
        """Create the entry form section."""
        self.entry_frame = ttk.Frame(parent, style='Main.TFrame')
        
        # Category entry with combo box
        ttk.Label(self.entry_frame, text="Category:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.category_var = tk.StringVar(value=self.last_category)
        self.category_combo = ttk.Combobox(self.entry_frame, textvariable=self.category_var, width=20)
        self.category_combo.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # Description entry
        ttk.Label(self.entry_frame, text="Description:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.description_var = tk.StringVar(value=self.last_description)
        self.description_entry = ttk.Entry(self.entry_frame, textvariable=self.description_var, width=40)
        self.description_entry.grid(row=0, column=3, sticky=tk.W+tk.E, padx=5)
        
        # Save button
        self.save_btn = ttk.Button(self.entry_frame, text="Save", command=self._save_entry)
        self.save_btn.grid(row=0, column=4, padx=5)
        
        # Configure grid columns
        self.entry_frame.columnconfigure(3, weight=1)
        
        # Bind events for entry fields
        self.category_combo.bind("<KeyRelease>", self._on_entry_modified)
        self.description_entry.bind("<KeyRelease>", self._on_entry_modified)
        self.category_combo.bind("<<ComboboxSelected>>", self._on_entry_modified)
        
        # Enable validation and hotkeys
        self.root.bind("<Return>", self._save_entry)
        
        # Don't display entry section initially (will be shown on prompt)
        # Use pack_forget later after initial packing in main_frame
    
    def _create_table_view(self, parent):
        """Create the table view for time entries."""
        self.tree_frame = ttk.Frame(parent)
        self.tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.tree = ttk.Treeview(self.tree_frame, columns=("ts", "category", "description"), show="headings", style="Treeview")
        self.tree.heading("ts", text="Timestamp")
        self.tree.heading("category", text="Category")
        self.tree.heading("description", text="Description")
        self.tree.column("ts", width=150)
        self.tree.column("category", width=100)
        self.tree.column("description", width=320)
        
        # Add scrollbars to treeview
        y_scroll = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=y_scroll.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Enable editing by double-clicking on an item
        self.tree.bind("<Double-1>", self._on_tree_double_click)
    
    def _create_status_bar(self):
        """Create the status bar with countdown timer."""
        self.status_frame = ttk.Frame(self.root, style='StatusBar.TFrame')
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=5)
        
        # Progress bar for auto-record countdown
        self.progress_var = tk.DoubleVar(value=100)
        self.progress = ttk.Progressbar(
            self.status_frame, 
            orient="horizontal", 
            length=150, 
            mode="determinate", 
            variable=self.progress_var
        )
        self.progress.pack(side=tk.RIGHT, padx=(0, 10))
        
        # Countdown label
        self.countdown_label = ttk.Label(
            self.status_frame, 
            text="Next prompt: calculating...", 
            cursor="hand2",
            style="CountdownLabel.TLabel"
        )
        self.countdown_label.pack(side=tk.RIGHT, padx=(0, 10))
        
        # Make the countdown label clickable to trigger the prompt early
        self.countdown_label.bind("<Button-1>", self._trigger_prompt_early)
    
    def _apply_theme(self):
        """Apply the selected theme to the UI."""
        style = ttk.Style()
        
        if self.theme_mode == "dark":
            # Set base theme - use 'clam' as it's more customizable
            style.theme_use('clam')
            
            # Define colors
            bg_color = "#2E3440"  # Dark gray/blue background
            fg_color = "#ECEFF4"  # Light gray text
            accent_color = "#5E81AC"  # Blue accent
            selection_color = "#4C566A"  # Slightly lighter selection
            
            # Configure ttk styles
            style.configure("TFrame", background=bg_color)
            style.configure("Main.TFrame", background=bg_color)
            style.configure("StatusBar.TFrame", background=bg_color)
            
            style.configure("TLabel", background=bg_color, foreground=fg_color)
            style.configure("CountdownLabel.TLabel", background=bg_color, foreground="#88C0D0")
            style.configure("CountdownUrgent.TLabel", background=bg_color, foreground="#BF616A")  # Red
            style.configure("CountdownWarning.TLabel", background=bg_color, foreground="#EBCB8B")  # Yellow/Orange
            style.configure("CountdownNormal.TLabel", background=bg_color, foreground="#88C0D0")  # Blue
            
            style.configure("TButton", 
                background=accent_color, 
                foreground=fg_color, 
                borderwidth=0,
                focusthickness=0, 
                focuscolor=accent_color,
                padding=5)
            style.map("TButton", 
                background=[('active', "#81A1C1"), ('pressed', "#7B96B2")],
                foreground=[('active', "#FFFFFF")])
            
            # Configure entry fields
            style.configure("TEntry", 
                fieldbackground=selection_color, 
                foreground=fg_color,
                bordercolor=accent_color, 
                darkcolor=accent_color, 
                lightcolor=accent_color,
                borderwidth=1)
            
            # Configure combobox
            style.configure("TCombobox", 
                fieldbackground=selection_color, 
                background=selection_color, 
                foreground=fg_color,
                arrowcolor=fg_color,
                bordercolor=accent_color, 
                darkcolor=accent_color, 
                lightcolor=accent_color)
            style.map("TCombobox", 
                fieldbackground=[('readonly', selection_color)],
                background=[('readonly', selection_color)],
                foreground=[('readonly', fg_color)])
            
            # Configure treeview
            style.configure("Treeview", 
                background=selection_color, 
                foreground=fg_color,
                fieldbackground=selection_color, 
                bordercolor=accent_color)
            style.map("Treeview", 
                background=[('selected', accent_color)],
                foreground=[('selected', "#FFFFFF")])
            
            style.configure("Treeview.Heading", 
                background=bg_color, 
                foreground=fg_color,
                borderwidth=1)
            style.map("Treeview.Heading", 
                background=[('active', bg_color)])
                
            # Scrollbar styling
            style.configure("Vertical.TScrollbar", 
                background=bg_color, 
                arrowcolor=fg_color, 
                bordercolor=bg_color,
                troughcolor=bg_color)
            style.map("Vertical.TScrollbar", 
                background=[('active', accent_color), ('pressed', accent_color)])
            
            # Add style for drag grip
            style.configure("Grip.TFrame", 
                background="#81A1C1",
                borderwidth=0)

            # Configure root window
            self.root.configure(background=bg_color)
        else:
            # Light theme - use default theme
            style.theme_use('default')
            self.root.configure(background=None)
    
    def _load_last_file(self):
        """Load the last used file if available."""
        current_file = self.config.get("current_file")
        if current_file and os.path.exists(current_file):
            self._load_file(current_file)
    
    def _on_close(self):
        """Handle window close event."""
        # Cancel any pending animations
        if self._animation_after_id:
            self.root.after_cancel(self._animation_after_id)
        if self._hover_check_id:
            self.root.after_cancel(self._hover_check_id)
        if self._after_id:
            self.root.after_cancel(self._after_id)
        if self._countdown_after_id:
            self.root.after_cancel(self._countdown_after_id)
        if self._auto_record_timer:
            self.root.after_cancel(self._auto_record_timer)
            
        # Save application configuration
        self._save_application_config()
        
        # Close the app
        self.root.destroy()
        
    def _save_application_config(self):
        """Save application configuration to config file."""
        # Update config with current values
        self.config["theme_mode"] = self.theme_mode
        self.config["recent_files"] = self.recent_files
        self.config["max_recent_files"] = self.max_recent_files
        self.config["start_time"] = self.start_time.strftime("%H:%M")
        self.config["end_time"] = self.end_time.strftime("%H:%M")
        self.config["interval"] = self.interval
        self.config["auto_record_seconds"] = self.auto_record_seconds
        
        # Save form input history
        self.config["last_category"] = self.last_category
        self.config["last_description"] = self.last_description
        
        # Save the current file path
        self.config["current_file"] = self.controller.get_current_file()
        
        # Save to file
        self._save_config(self.config)
    
    def _load_config(self):
        """Load the configuration from the config file, or create default if it doesn't exist."""
        if not self.config_file.exists():
            self._save_config(self.default_config)
            return self.default_config
        
        try:
            with open(self.config_file, "r") as f:
                config = json.load(f)
            return config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return self.default_config
    
    def _save_config(self, config):
        """Save the configuration to the config file."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)  # Create config directory if it doesn't exist
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def _update_window_title(self):
        """Update the window title based on current file and modified status."""
        title = "Time Tracker"
        
        current_file = self.controller.get_current_file()
        if current_file:
            # Get the base filename without extension
            basename = os.path.splitext(os.path.basename(current_file))[0]
            title = f"Time Tracker - {basename}"
            
        if self.controller.has_unsaved_changes():
            title += " *"
            
        self.root.title(title)
    
    def _toggle_theme(self):
        """Toggle between dark and light theme."""
        if self.theme_mode == "dark":
            self.theme_mode = "light"
        else:
            self.theme_mode = "dark"
        self._apply_theme()
    
    def _new_file(self):
        """Create a new empty file."""
        # Check for unsaved changes first
        if self.controller.has_unsaved_changes() and self.tree.get_children():
            if not messagebox.askyesno("Unsaved Changes", 
                                     "You have unsaved changes. Create a new file anyway?"):
                return
                
        # Clear the treeview
        self.tree.delete(*self.tree.get_children())
        
        # Reset through controller
        self.controller.clear()
        
        # Update window title
        self._update_window_title()
    
    def _save_current_file(self, event=None):
        """Save to the current file or prompt for a location if none."""
        current_file = self.controller.get_current_file()
        if current_file:
            self._populate_backend_data()  # Make sure backend has current data
            success = self.controller.save_file(current_file)
            if success:
                self._update_window_title()
                self._add_to_recent_files(current_file)
            else:
                messagebox.showerror("Save Error", "Failed to save the file.")
            return success
        else:
            return self._save_data()
    
    def _save_data(self):
        """Save data to a new file location."""
        current_file = self.controller.get_current_file()
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files","*.csv")],
            initialfile="" if not current_file else os.path.basename(current_file)
        )
        if not path: 
            return False
            
        self._populate_backend_data()  # Make sure backend has current data
        success = self.controller.save_file(path)
        if success:
            self._update_window_title()
            self._add_to_recent_files(path)
        else:
            messagebox.showerror("Save Error", "Failed to save the file.")
        return success
    
    def _populate_backend_data(self):
        """Populate backend data from treeview before saving."""
        # This function would need to be implemented if we weren't keeping the backend
        # in sync with the UI automatically. Since we're using the controller for all 
        # operations, this is just a placeholder for future functionality.
        pass
    
    def _load_data(self):
        """Load data from a file."""
        # Check for unsaved changes first
        if self.controller.has_unsaved_changes() and self.tree.get_children():
            if not messagebox.askyesno("Unsaved Changes", 
                                     "You have unsaved changes. Load a new file anyway?"):
                return
                
        path = filedialog.askopenfilename(filetypes=[("CSV files","*.csv")])
        if not path: 
            return
            
        self._load_file(path)
    
    def _load_file(self, filepath):
        """Load data from the specified file path."""
        success = self.controller.load_file(filepath)
        
        if success:
            # Update treeview with entries from backend
            self._refresh_entries()
            
            # Update window title
            self._update_window_title()
            
            # Add to recent files
            self._add_to_recent_files(filepath)
            
            return True
        else:
            messagebox.showerror("Load Error", "Failed to load the file.")
            return False
    
    def _refresh_entries(self):
        """Refresh the treeview with entries from the backend."""
        # Clear the treeview
        self.tree.delete(*self.tree.get_children())
        
        # Get entries from backend via controller
        entries = self.controller.get_time_entries()
        
        # Add entries to treeview
        for entry in entries:
            timestamp = entry.get("end_time", "")
            self.tree.insert("", "end", iid=entry.get("id"), values=(
                timestamp,
                entry.get("category", ""),
                entry.get("description", "")
            ))
        
        # Update category list
        self._update_category_list()
    
    def _add_to_recent_files(self, filepath):
        """Add a file to the recent files list."""
        # Remove if already in list
        if filepath in self.recent_files:
            self.recent_files.remove(filepath)
            
        # Add to front of list
        self.recent_files.insert(0, filepath)
        
        # Trim if needed
        if len(self.recent_files) > self.max_recent_files:
            self.recent_files = self.recent_files[:self.max_recent_files]
            
        # Update menu
        self._update_recent_files_menu()
    
    def _update_recent_files_menu(self):
        """Update the recent files dropdown menu."""
        # Clear existing items
        self.recent_files_menu.delete(0, tk.END)
        
        # Add recent files
        if not self.recent_files:
            self.recent_files_menu.add_command(label="No recent files", state=tk.DISABLED)
        else:
            for path in self.recent_files:
                basename = os.path.basename(path)
                # Use lambda with default arg to avoid late binding issues
                self.recent_files_menu.add_command(
                    label=basename, 
                    command=lambda p=path: self._load_file(p)
                )
    
    def _update_category_list(self):
        """Update the category list in the combobox."""
        categories = self.controller.get_categories()
        self.category_combo['values'] = categories
    
    def _on_entry_modified(self, event=None):
        """Handle when the user modifies an entry field to reset the auto-record timer."""
        # Mark that user is actively editing
        self.currently_editing = True
        
        # Reset the auto-record countdown when the user makes changes
        self._start_auto_record_countdown(self.auto_record_seconds)
    
    def _on_tree_double_click(self, event=None):
        """Handle double-click on treeview item to edit it."""
        # Get the selected item
        item_id = self.tree.focus()
        if not item_id:
            return
            
        # Get the current values
        values = self.tree.item(item_id)['values']
        if not values or len(values) < 3:
            return
        
        # Show entry fields
        self.entry_frame.pack_forget()  # First remove it if it's already packed
        self.entry_frame.pack(in_=self.main_frame, fill=tk.X, padx=5, pady=5, before=self.tree_frame)
        
        # Set the current values
        self.category_var.set(values[1])
        self.description_var.set(values[2].replace(" [Auto-recorded]", ""))
        
        # Set the editing item ID
        self.editing_item_id = item_id
        self.currently_editing = True
        
        # Focus on category field
        self.category_combo.focus_force()
        
        # Start auto-record countdown
        self._start_auto_record_countdown(self.auto_record_seconds)
        
        # Bring window to front
        self.root.attributes('-topmost', True)
        self.root.attributes('-topmost', False)
        
        # Play notification sound to attract attention
        self.root.bell()
    
    def _save_entry(self, event=None):
        """Save the current entry data."""
        category = self.category_var.get().strip()
        description = self.description_var.get().strip()
        
        if not (category or description):  # Require at least one field to be filled
            messagebox.showwarning("Empty Entry", "Please enter at least a category or description.")
            return
            
        # Save as last entered values
        self.last_category = category
        self.last_description = description
        
        # If editing an existing item, update it but preserve the original timestamp
        if self.currently_editing and self.editing_item_id:
            # Get the existing values including the original timestamp
            existing_values = self.tree.item(self.editing_item_id)['values']
            original_timestamp = existing_values[0]  # Keep the original timestamp
            
            # Update through controller
            entry_id = self.editing_item_id  # In a real impl, would map to backend ID
            success = self.controller.update_time_entry(
                entry_id, original_timestamp, category, description
            )
            
            if success:
                # Update UI
                self.tree.item(self.editing_item_id, values=(original_timestamp, category, description))
            
            # Reset editing state
            self.currently_editing = False
            self.editing_item_id = None
        else:
            # Insert a new item with current timestamp
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Add through controller
            entry_id = self.controller.add_time_entry(ts, category, description)
            
            if entry_id:
                # Update UI
                self.tree.insert("", "end", values=(ts, category, description))
        
        # Clear the entry fields
        self.category_var.set("")
        self.description_var.set("")
        
        # Hide entry frame
        self.entry_frame.pack_forget()
        
        # Cancel auto-record timer
        if self._auto_record_timer:
            self.root.after_cancel(self._auto_record_timer)
            self._auto_record_timer = None
        
        # Update window title to reflect unsaved changes
        self._update_window_title()
        
        # Schedule next reminder
        self._schedule_next_reminder()
    
    def _start_auto_record_countdown(self, seconds):
        """Start the auto-record countdown with progress bar."""
        # Cancel existing timer if any
        if self._auto_record_timer:
            self.root.after_cancel(self._auto_record_timer)
            self._auto_record_timer = None
            
        # Reset progress bar to full
        self.progress_var.set(100)
        
        # Calculate the decrement amount for each second
        decrement_per_sec = 100 / seconds
        
        def update_progress_and_countdown(remaining_seconds, current_progress):
            if remaining_seconds <= 0:
                # Time's up, finalize the record
                self._auto_record_entry()
                return
                
            # Update progress bar
            new_progress = current_progress - decrement_per_sec
            self.progress_var.set(max(0, new_progress))
            
            # Schedule next update
            self._auto_record_timer = self.root.after(1000, lambda: 
                update_progress_and_countdown(remaining_seconds - 1, new_progress))
        
        # Start the countdown
        update_progress_and_countdown(seconds, 100)
    
    def _auto_record_entry(self):
        """Auto-record the current entry if user didn't save manually."""
        category = self.category_var.get().strip()
        description = self.description_var.get().strip()
        
        if category or description:  # Only auto-record if something was entered
            # Append [Auto-recorded] to description
            if description:
                description += " [Auto-recorded]"
            else:
                description = "[Auto-recorded]"
                
            # Save the entry
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Add through controller
            entry_id = self.controller.add_time_entry(ts, category, description)
            
            if entry_id:
                # Update UI
                self.tree.insert("", "end", values=(ts, category, description))
            
            # Save as last entered values
            self.last_category = category
            self.last_description = description
        
        # Clear the entry fields
        self.category_var.set("")
        self.description_var.set("")
        
        # Hide entry frame
        self.entry_frame.pack_forget()
        
        # Update window title to reflect unsaved changes
        self._update_window_title()
        
        # Schedule next reminder
        self._schedule_next_reminder()
    
    def _schedule_next_reminder(self):
        """Schedule the next reminder based on time settings."""
        # cancel any existing callback
        if self._after_id:
            self.root.after_cancel(self._after_id)
            self._after_id = None
            
        # Cancel any existing countdown update
        if self._countdown_after_id:
            self.root.after_cancel(self._countdown_after_id)
            self._countdown_after_id = None

        now = datetime.now()
        today_start = datetime.combine(now.date(), self.start_time)
        today_end = datetime.combine(now.date(), self.end_time)

        if now < today_start:
            # schedule at start
            delta = (today_start - now).total_seconds() * 1000
            self.next_reminder = today_start
        elif now > today_end:
            # schedule tomorrow's start
            tomorrow_start = today_start + timedelta(days=1)
            delta = (tomorrow_start - now).total_seconds() * 1000
            self.next_reminder = tomorrow_start
        else:
            # inside window: always schedule from current time
            next_time = now + timedelta(minutes=self.interval)
            if next_time > today_end:
                tomorrow_start = today_start + timedelta(days=1)
                delta = (tomorrow_start - now).total_seconds() * 1000
                self.next_reminder = tomorrow_start
            else:
                delta = (next_time - now).total_seconds() * 1000
                self.next_reminder = next_time

        # schedule and keep the ID
        self._after_id = self.root.after(int(delta), self._show_prompt)
        
        # Start updating the countdown
        self._update_countdown()
    
    def _update_countdown(self):
        """Update the countdown timer display."""
        if not self.next_reminder:
            self.countdown_label.configure(text="Next prompt: Not scheduled")
            return
            
        now = datetime.now()
        if now >= self.next_reminder:
            self.countdown_label.configure(text="Prompting now...")
            return
            
        # Calculate time difference
        time_diff = self.next_reminder - now
        hours, remainder = divmod(time_diff.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if time_diff.days > 0:
            countdown_text = f"Next prompt: {time_diff.days}d {hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            countdown_text = f"Next prompt: {hours:02d}:{minutes:02d}:{seconds:02d}"
            
        # Update label style based on time remaining
        if self.theme_mode == "dark":
            if time_diff.seconds < 60:  # Less than 1 minute
                self.countdown_label.configure(style="CountdownUrgent.TLabel")
            elif time_diff.seconds < 300:  # Less than 5 minutes
                self.countdown_label.configure(style="CountdownWarning.TLabel")
            else:
                self.countdown_label.configure(style="CountdownNormal.TLabel")
        else:
            # Light mode color scheme
            if time_diff.seconds < 60:  # Less than 1 minute
                self.countdown_label.configure(foreground="red")
            elif time_diff.seconds < 300:  # Less than 5 minutes
                self.countdown_label.configure(foreground="orange")
            else:
                self.countdown_label.configure(foreground="blue")
            
        self.countdown_label.configure(text=countdown_text)
        
        # Schedule the next update in 1 second
        self._countdown_after_id = self.root.after(1000, self._update_countdown)
    
    def _trigger_prompt_early(self, event=None):
        """Trigger the prompt early when countdown is clicked."""
        if self._after_id:
            self.root.after_cancel(self._after_id)
            self._after_id = None
            # Reset next_reminder to ensure proper scheduling when canceled
            self.next_reminder = None
            self._show_prompt()
    
    def _show_prompt(self):
        """Show time entry prompt in main window."""
        # Force window to foreground
        self.root.attributes('-topmost', True)
        self.root.attributes('-topmost', False)
        
        # Play notification sound
        self.root.bell()
        
        # Show the entry section
        self.entry_frame.pack_forget()  # First remove it if it's already packed
        self.entry_frame.pack(in_=self.main_frame, fill=tk.X, padx=5, pady=5, before=self.tree_frame)
        
        # Focus on the category combo box
        self.category_combo.focus_force()
        
        # Update category list
        self._update_category_list()
        
        # Pre-populate with last values
        self.category_var.set(self.last_category)
        self.description_var.set(self.last_description)
        
        # Start auto-record countdown
        self._start_auto_record_countdown(self.auto_record_seconds)
        
        # Schedule next reminder
        self._schedule_next_reminder()
    
    def _open_settings(self):
        """Open the settings dialog."""
        dlg = tk.Toplevel(self.root)
        dlg.title("Configure Reminders")
        dlg.grab_set()
        
        # Apply theme to dialog
        if self.theme_mode == "dark":
            bg_color = "#2E3440"
            fg_color = "#ECEFF4"
            dlg.configure(background=bg_color)
        
        # Settings frame
        settings_frame = ttk.Frame(dlg)
        settings_frame.pack(padx=15, pady=15, fill=tk.BOTH, expand=True)

        ttk.Label(settings_frame, text="Start (HH:MM)").grid(row=0, column=0, pady=5, padx=5, sticky=tk.W)
        s_ent = ttk.Entry(settings_frame)
        s_ent.grid(row=0, column=1, pady=5, padx=5, sticky=tk.EW)
        s_ent.insert(0, self.start_time.strftime("%H:%M"))

        ttk.Label(settings_frame, text="End   (HH:MM)").grid(row=1, column=0, pady=5, padx=5, sticky=tk.W)
        e_ent = ttk.Entry(settings_frame)
        e_ent.grid(row=1, column=1, pady=5, padx=5, sticky=tk.EW)
        e_ent.insert(0, self.end_time.strftime("%H:%M"))

        ttk.Label(settings_frame, text="Interval (min)").grid(row=2, column=0, pady=5, padx=5, sticky=tk.W)
        i_ent = ttk.Entry(settings_frame)
        i_ent.grid(row=2, column=1, pady=5, padx=5, sticky=tk.EW)
        i_ent.insert(0, str(self.interval))

        def save_and_close():
            try:
                h,m = map(int, s_ent.get().split(":"))
                self.start_time = time(h,m)
                h,m = map(int, e_ent.get().split(":"))
                self.end_time = time(h,m)
                self.interval = int(i_ent.get())
            except Exception as ex:
                messagebox.showerror("Bad value", ex)
                return
            dlg.destroy()
            self._schedule_next_reminder()

        btn_frame = ttk.Frame(settings_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="OK", command=save_and_close).pack(pady=5, padx=5)
        
    # Docking-related functions
    def _on_mouse_enter(self, event=None):
        """Handle mouse enter event for docked window."""
        if self.is_docked:
            self._show_window()
    
    def _on_mouse_leave(self, event=None):
        """Handle mouse leave event for docked window."""
        if not self.is_docked:
            return
            
        # Get mouse position
        mouse_x = self.root.winfo_pointerx()
        mouse_y = self.root.winfo_pointery()
        
        # Get window position and dimensions
        win_x = self.root.winfo_rootx()
        win_y = self.root.winfo_rooty()
        win_width = self.root.winfo_width()
        win_height = self.root.winfo_height()
        
        # Check if mouse is outside window
        if (mouse_x < win_x or mouse_x > win_x + win_width or
            mouse_y < win_y or mouse_y > win_y + win_height):
            self._hide_window()
    
    def _set_docking(self, side):
        """Dock the window to the specified side of the screen."""
        # Docking implementation would go here
        # For brevity, it's not included in this example
        pass
    
    def _undock_window(self):
        """Restore window to normal state."""
        # Undocking implementation would go here
        # For brevity, it's not included in this example
        pass
    
    def _show_window(self):
        """Animate window sliding into view."""
        # Show window animation would go here
        # For brevity, it's not included in this example
        pass
    
    def _hide_window(self):
        """Animate window sliding out of view but leave small part visible."""
        # Hide window animation would go here
        # For brevity, it's not included in this example
        pass