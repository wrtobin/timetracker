#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv, os, json
from datetime import datetime, time, timedelta
import appdirs
from pathlib import Path

class TimeTrackerApp:
    def __init__(self, root):
        self.root = root
        root.title("Time Tracker")
        root.geometry("600x400")
        
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
        self.config = self.load_config()
        
        # Theme settings
        self.theme_mode = self.config.get("theme_mode", "dark")
        
        # Initialize UI theme immediately (this was missing)
        self.configure_theme()
        
        # File tracking settings
        self.current_file = self.config.get("current_file", None)
        self.has_unsaved_changes = False
        self.recent_files = self.config.get("recent_files", [])
        self.max_recent_files = self.config.get("max_recent_files", 5)
        
        # Last used values for form auto-population
        self.last_category = self.config.get("last_category", "")
        self.last_description = self.config.get("last_description", "")
        
        # Docking settings
        self.is_docked = False
        self.dock_side = "right"  # Options: left, right, top, bottom
        self.dock_reveal_size = 5  # pixels visible when docked and hidden - INCREASED from 2 to 5
        self.dock_animation_steps = 10
        self.dock_animation_ms = 10
        self.dock_width = 600  # Increased default width for docked window
        self._animation_after_id = None
        self._hover_check_id = None
        
        # Initialize timer-related attributes
        self._after_id = None
        self._countdown_after_id = None
        self._auto_record_timer = None
        self.next_reminder = None

        # Default settings
        self.start_time = time(7, 0)
        self.end_time   = time(19, 0)
        self.interval   = 30 # minutes
        self.auto_record_seconds = 60  # configurable auto-record timeout
        self.currently_editing = False  # track if user is actively editing

        # Menu
        menubar = tk.Menu(root)
        filem = tk.Menu(menubar, tearoff=0)
        filem.add_command(label="New", command=self.new_file)
        filem.add_command(label="Open...", command=self.load_data)
        filem.add_command(label="Save", command=self.save_current_file, accelerator="Ctrl+S")
        filem.add_command(label="Save As...", command=self.save_data)
        filem.add_separator()
        
        # Recent files submenu
        self.recent_files_menu = tk.Menu(filem, tearoff=0)
        filem.add_cascade(label="Recent Files", menu=self.recent_files_menu)
        
        filem.add_separator()
        filem.add_command(label="Exit", command=root.quit)
        menubar.add_cascade(label="File", menu=filem)

        # Bind Ctrl+S to save
        root.bind("<Control-s>", self.save_current_file)
        
        settings = tk.Menu(menubar, tearoff=0)
        settings.add_command(label="Configure Reminders…", command=self.open_settings)
        settings.add_separator()
        
        # Add docking options to menu
        self.docking_menu = tk.Menu(settings, tearoff=0)
        self.docking_menu.add_command(label="Dock to Left", command=lambda: self.set_docking("left"))
        self.docking_menu.add_command(label="Dock to Right", command=lambda: self.set_docking("right"))
        self.docking_menu.add_command(label="Dock to Top", command=lambda: self.set_docking("top"))
        self.docking_menu.add_command(label="Dock to Bottom", command=lambda: self.set_docking("bottom"))
        self.docking_menu.add_separator()
        self.docking_menu.add_command(label="Undock Window", command=self.undock_window)
        settings.add_cascade(label="Docking Options", menu=self.docking_menu)
        
        settings.add_command(label="Toggle Dark/Light Mode", command=self.toggle_theme)
        menubar.add_cascade(label="Settings", menu=settings)

        root.config(menu=menubar)

        # Main frame with background color
        main_frame = ttk.Frame(root, style='Main.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Entry section at the top
        self.entry_frame = ttk.Frame(main_frame, style='Main.TFrame')
        self.entry_frame.pack(fill=tk.X, padx=5, pady=5)
        
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
        self.save_btn = ttk.Button(self.entry_frame, text="Save", command=self.save_entry)
        self.save_btn.grid(row=0, column=4, padx=5)
        
        # Configure grid columns
        self.entry_frame.columnconfigure(3, weight=1)
        
        # Bind events for entry fields
        self.category_combo.bind("<KeyRelease>", self.on_entry_modified)
        self.description_entry.bind("<KeyRelease>", self.on_entry_modified)
        self.category_combo.bind("<<ComboboxSelected>>", self.on_entry_modified)
        
        # Enable validation and hotkeys
        self.root.bind("<Return>", self.save_entry)
        
        # Hide entry section initially (will be shown on prompt)
        self.entry_frame.pack_forget()

        # Table view - updated to have three columns
        self.tree_frame = ttk.Frame(main_frame)
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
        self.tree.bind("<Double-1>", self.on_tree_double_click)
        
        # Status bar with countdown timer and progress bar
        self.status_frame = ttk.Frame(root, style='StatusBar.TFrame')
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
        self.countdown_label.bind("<Button-1>", self.trigger_prompt_early)
        
        # Currently editing item ID (for updating existing entries)
        self.editing_item_id = None

        # Configure window events for docking behavior
        root.bind("<Enter>", self.on_mouse_enter)
        root.bind("<Leave>", self.on_mouse_leave)
        root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Update category list
        self.update_category_list()

        # Load the last used file if available
        if self.current_file and os.path.exists(self.current_file):
            self.load_file(self.current_file)

        # Kick off scheduling
        self.schedule_next()

    def on_close(self):
        """Handle window close event"""
        # Cancel any pending animations
        if self._animation_after_id:
            self.root.after_cancel(self._animation_after_id)
        if self._hover_check_id:
            self.root.after_cancel(self._hover_check_id)
            
        # Save application configuration
        self.save_application_config()
        
        # Close the app
        self.root.destroy()
        
    def save_application_config(self):
        """Save application configuration to config file"""
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
        self.config["current_file"] = self.current_file
        
        # Save to file
        self.save_config(self.config)
        
    def load_application_config(self):
        """Load application configuration from config file"""
        # Load settings from config
        self.theme_mode = self.config.get("theme_mode", "dark")
        self.recent_files = self.config.get("recent_files", [])
        self.max_recent_files = self.config.get("max_recent_files", 5)
        
        # Handle time settings
        try:
            start_time = self.config.get("start_time", "07:00")
            h, m = map(int, start_time.split(":"))
            self.start_time = time(h, m)
        except:
            self.start_time = time(7, 0)
            
        try:
            end_time = self.config.get("end_time", "19:00")
            h, m = map(int, end_time.split(":"))
            self.end_time = time(h, m)
        except:
            self.end_time = time(19, 0)
            
        self.interval = self.config.get("interval", 30)
        self.auto_record_seconds = self.config.get("auto_record_seconds", 60)
        
        # Update recent files menu
        self.update_recent_files_menu()

    def on_mouse_enter(self, event=None):
        """Handle mouse enter event for docked window"""
        if self.is_docked:
            self.show_window()
    
    def on_mouse_leave(self, event=None):
        """Handle mouse leave event for docked window"""
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
            self.hide_window()

    def get_monitor_geometry(self):
        """Get the geometry of the monitor the window is primarily located on"""
        try:
            # Try to use Python's screeninfo module if available
            try:
                import screeninfo
                monitors = screeninfo.get_monitors()
                
                # Get window position and center
                win_x = self.root.winfo_rootx()
                win_y = self.root.winfo_rooty()
                win_width = self.root.winfo_width()
                win_height = self.root.winfo_height()
                win_center_x = win_x + win_width // 2
                win_center_y = win_y + win_height // 2
                
                # Find which monitor contains the center of the window
                for m in monitors:
                    if (m.x <= win_center_x < m.x + m.width and
                        m.y <= win_center_y < m.y + m.height):
                        return m.x, m.y, m.width, m.height
                
                # If no monitor found, use the primary monitor
                for m in monitors:
                    if hasattr(m, 'is_primary') and m.is_primary:
                        return m.x, m.y, m.width, m.height
                
                # Fallback to the first monitor
                m = monitors[0]
                return m.x, m.y, m.width, m.height
                
            except ImportError:
                # Fallback method using tkinter's winfo functions
                screen_width = self.root.winfo_screenwidth()
                screen_height = self.root.winfo_screenheight()
                
                # Get window geometry
                win_geom = self.root.geometry()
                parts = win_geom.split('+')
                if len(parts) >= 3:
                    win_x = int(parts[1])
                    win_y = int(parts[2])
                else:
                    win_x = self.root.winfo_x()
                    win_y = self.root.winfo_y()
                    
                win_width = self.root.winfo_width()
                win_height = self.root.winfo_height()
                win_center_x = win_x + win_width // 2
                win_center_y = win_y + win_height // 2
                
                # Simple checks for multi-monitor setups
                # These are estimates and will only work for common layouts
                # Left-right layout
                if win_center_x > screen_width:
                    # Window is on a monitor to the right
                    return screen_width, 0, screen_width, screen_height
                elif win_center_x < 0:
                    # Window is on a monitor to the left
                    return win_center_x - (win_width // 2), 0, screen_width, screen_height
                else:
                    # Window is on the primary monitor
                    return 0, 0, screen_width, screen_height
        except Exception as e:
            print(f"Error detecting monitor: {e}")
            # Default to primary monitor dimensions
            return 0, 0, self.root.winfo_screenwidth(), self.root.winfo_screenheight()
            
    def set_docking(self, side):
        """Dock the window to the specified side of the screen"""
        self.dock_side = side
        self.is_docked = True
        
        # Make window stay on top when docked
        self.root.attributes('-topmost', True)
        
        # Remove window manager decorations but allow resizing
        self.root.overrideredirect(True)
        
        # Store original geometry for undocking
        self.original_geometry = self.root.geometry()
        
        # Get current monitor dimensions and position
        mon_x, mon_y, mon_width, mon_height = self.get_monitor_geometry()
        
        # Calculate new position based on dock side
        if side == "left":
            self.root.geometry(f"{self.dock_width}x{mon_height}+{mon_x}+{mon_y}")
        elif side == "right":
            self.root.geometry(f"{self.dock_width}x{mon_height}+{mon_x + mon_width - self.dock_width}+{mon_y}")
        elif side == "top":
            self.root.geometry(f"{mon_width}x300+{mon_x}+{mon_y}")
        elif side == "bottom":
            self.root.geometry(f"{mon_width}x300+{mon_x}+{mon_y + mon_height - 300}")
        
        # Add resize grip and edges for resizing
        self.create_resize_elements()
        
        # Initial hide (leaving small part visible)
        self.hide_window()
    
    def create_resize_elements(self):
        """Create resize handles and drag grip for the docked window"""
        # Clear existing elements
        if hasattr(self, 'drag_grip'):
            self.drag_grip.destroy()
        
        # Create container for resize edges
        if hasattr(self, 'resize_frame'):
            self.resize_frame.destroy()
        
        self.resize_frame = ttk.Frame(self.root)
        self.resize_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create main content frame
        self.docked_content = ttk.Frame(self.resize_frame)
        self.docked_content.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Move existing widgets to the content frame
        # But exclude special widgets like menus and frames that can't be repacked
        for widget in list(self.root.winfo_children()):
            if (widget != self.resize_frame and 
                widget != self.status_frame and 
                not isinstance(widget, tk.Menu) and
                hasattr(widget, 'pack')):
                try:
                    widget.pack_forget()
                    if hasattr(widget, 'grid_forget'):
                        widget.grid_forget()
                    if hasattr(widget, 'place_forget'):
                        widget.place_forget()
                    widget.pack(in_=self.docked_content, fill=tk.BOTH, expand=True)
                except (tk.TclError, Exception) as e:
                    print(f"Could not repack widget {widget}: {e}")
        
        # Create drag grip based on dock side
        if self.dock_side in ("left", "right"):
            grip_width = 5
            grip_side = tk.RIGHT if self.dock_side == "left" else tk.LEFT
            
            self.drag_grip = ttk.Frame(self.resize_frame, style="Grip.TFrame", width=grip_width, cursor="sb_h_double_arrow")
            self.drag_grip.pack(side=grip_side, fill=tk.Y)
            
            # Add resize border on opposite side for width adjustment
            resize_side = tk.LEFT if self.dock_side == "left" else tk.RIGHT
            resize_cursor = "sb_h_double_arrow"
            
            self.resize_edge = ttk.Frame(self.resize_frame, width=4, cursor=resize_cursor)
            self.resize_edge.pack(side=resize_side, fill=tk.Y)
            
        else:  # Top or bottom
            grip_height = 5
            grip_side = tk.BOTTOM if self.dock_side == "top" else tk.TOP
            
            self.drag_grip = ttk.Frame(self.resize_frame, style="Grip.TFrame", height=grip_height, cursor="sb_v_double_arrow")
            self.drag_grip.pack(side=grip_side, fill=tk.X)
            
            # Add resize border on opposite side for height adjustment
            resize_side = tk.TOP if self.dock_side == "top" else tk.BOTTOM
            resize_cursor = "sb_v_double_arrow"
            
            self.resize_edge = ttk.Frame(self.resize_frame, height=4, cursor=resize_cursor)
            self.resize_edge.pack(side=resize_side, fill=tk.X)
        
        # Bind drag events
        self.drag_grip.bind("<ButtonPress-1>", self.start_drag)
        self.drag_grip.bind("<B1-Motion>", self.on_drag)
        
        # Bind resize events
        self.resize_edge.bind("<ButtonPress-1>", self.start_resize)
        self.resize_edge.bind("<B1-Motion>", self.on_resize)
    
    def start_drag(self, event):
        """Record initial position for drag operation"""
        self.drag_start_x = event.x_root
        self.drag_start_y = event.y_root
        self.window_start_x = self.root.winfo_x()
        self.window_start_y = self.root.winfo_y()
    
    def on_drag(self, event):
        """Handle window drag operation"""
        if not hasattr(self, 'drag_start_x'):
            return
            
        dx = event.x_root - self.drag_start_x
        dy = event.y_root - self.drag_start_y
        
        new_x = self.window_start_x + dx
        new_y = self.window_start_y + dy
        
        # Keep window on screen while dragging
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        
        # Constrain to screen bounds
        new_x = max(0, min(new_x, screen_width - window_width))
        new_y = max(0, min(new_y, screen_height - window_height))
        
        self.root.geometry(f"+{new_x}+{new_y}")
    
    def start_resize(self, event):
        """Start window resize operation"""
        self.resize_start_x = event.x_root
        self.resize_start_y = event.y_root
        self.window_start_width = self.root.winfo_width()
        self.window_start_height = self.root.winfo_height()
        self.window_start_x = self.root.winfo_x()
        self.window_start_y = self.root.winfo_y()
    
    def on_resize(self, event):
        """Handle window resize operation"""
        if not hasattr(self, 'resize_start_x'):
            return
            
        dx = event.x_root - self.resize_start_x
        dy = event.y_root - self.resize_start_y
        
        # Get monitor dimensions
        mon_x, mon_y, mon_width, mon_height = self.get_monitor_geometry()
        
        if self.dock_side == "left":
            new_width = self.window_start_width + dx
            # Constrain minimum width
            new_width = max(200, new_width)
            # Constrain maximum width
            new_width = min(new_width, mon_width - self.window_start_x)
            self.root.geometry(f"{new_width}x{self.window_start_height}")
            
        elif self.dock_side == "right":
            new_width = self.window_start_width - dx
            # Constrain minimum width
            new_width = max(200, new_width)
            # Constrain maximum width
            new_width = min(new_width, self.window_start_x + self.window_start_width - mon_x)
            new_x = self.window_start_x + dx
            self.root.geometry(f"{new_width}x{self.window_start_height}+{new_x}+{self.window_start_y}")
            
        elif self.dock_side == "top":
            new_height = self.window_start_height + dy
            # Constrain minimum height
            new_height = max(100, new_height)
            # Constrain maximum height
            new_height = min(new_height, mon_height - self.window_start_y)
            self.root.geometry(f"{self.window_start_width}x{new_height}")
            
        elif self.dock_side == "bottom":
            new_height = self.window_start_height - dy
            # Constrain minimum height
            new_height = max(100, new_height)
            # Constrain maximum height
            new_height = min(new_height, self.window_start_y + self.window_start_height - mon_y)
            new_y = self.window_start_y + dy
            self.root.geometry(f"{self.window_start_width}x{new_height}+{new_y}")

    def undock_window(self):
        """Restore window to normal state"""
        if not self.is_docked:
            return
            
        # Cancel any pending animations
        if self._animation_after_id:
            self.root.after_cancel(self._animation_after_id)
        if self._hover_check_id:
            self.root.after_cancel(self._hover_check_id)
        
        # Restore normal window attributes
        self.root.attributes('-topmost', False)
        self.root.overrideredirect(False)
        
        # Remove resize elements
        if hasattr(self, 'resize_frame'):
            # Move content back to root
            for widget in list(self.docked_content.winfo_children()):
                widget.pack_forget()
                widget.pack(in_=self.root, fill=tk.BOTH, expand=True)
            
            self.resize_frame.destroy()
            
        # Remove the drag grip if it exists
        if hasattr(self, 'drag_grip'):
            self.drag_grip.destroy()
            
        # Restore original geometry if available
        if hasattr(self, 'original_geometry'):
            self.root.geometry(self.original_geometry)
        else:
            self.root.geometry("600x400")
            
        self.is_docked = False
        
        # Ensure status frame is correctly positioned
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=5)
    
    def show_window(self):
        """Animate window sliding into view"""
        if not self.is_docked or self._animation_after_id:
            return
            
        # Get monitor dimensions
        mon_x, mon_y, mon_width, mon_height = self.get_monitor_geometry()
        
        # Get current position and size
        win_x = self.root.winfo_x()
        win_y = self.root.winfo_y()
        win_width = self.root.winfo_width()
        win_height = self.root.winfo_height()
        
        # Calculate target position based on dock side
        if self.dock_side == "left":
            target_x = mon_x  # Use monitor X position
            current_pos = win_x
            step = (target_x - current_pos) // self.dock_animation_steps
            
            def animate_step(step_count):
                new_x = win_x + (step * step_count)
                if step_count >= self.dock_animation_steps or new_x <= target_x:
                    self.root.geometry(f"+{target_x}+{win_y}")
                    self._animation_after_id = None
                else:
                    self.root.geometry(f"+{new_x}+{win_y}")
                    self._animation_after_id = self.root.after(
                        self.dock_animation_ms, 
                        lambda: animate_step(step_count + 1)
                    )
                    
        elif self.dock_side == "right":
            target_x = mon_x + mon_width - win_width  # Use monitor width
            current_pos = win_x
            step = (target_x - current_pos) // self.dock_animation_steps
            
            def animate_step(step_count):
                new_x = win_x + (step * step_count)
                if step_count >= self.dock_animation_steps or new_x >= target_x:
                    self.root.geometry(f"+{target_x}+{win_y}")
                    self._animation_after_id = None
                else:
                    self.root.geometry(f"+{new_x}+{win_y}")
                    self._animation_after_id = self.root.after(
                        self.dock_animation_ms, 
                        lambda: animate_step(step_count + 1)
                    )
                    
        elif self.dock_side == "top":
            target_y = mon_y  # Use monitor Y position
            current_pos = win_y
            step = (target_y - current_pos) // self.dock_animation_steps
            
            def animate_step(step_count):
                new_y = win_y + (step * step_count)
                if step_count >= self.dock_animation_steps or new_y <= target_y:
                    self.root.geometry(f"+{win_x}+{target_y}")
                    self._animation_after_id = None
                else:
                    self.root.geometry(f"+{win_x}+{new_y}")
                    self._animation_after_id = self.root.after(
                        self.dock_animation_ms, 
                        lambda: animate_step(step_count + 1)
                    )
                    
        elif self.dock_side == "bottom":
            target_y = mon_y + mon_height - win_height  # Use monitor height
            current_pos = win_y
            step = (target_y - current_pos) // self.dock_animation_steps
            
            def animate_step(step_count):
                new_y = win_y + (step * step_count)
                if step_count >= self.dock_animation_steps or new_y >= target_y:
                    self.root.geometry(f"+{win_x}+{target_y}")
                    self._animation_after_id = None
                else:
                    self.root.geometry(f"+{win_x}+{new_y}")
                    self._animation_after_id = self.root.after(
                        self.dock_animation_ms, 
                        lambda: animate_step(step_count + 1)
                    )
        
        # Start animation
        self._animation_after_id = self.root.after(0, lambda: animate_step(1))
    
    def hide_window(self):
        """Animate window sliding out of view but leave small part visible"""
        if not self.is_docked or self._animation_after_id:
            return
        
        # Get monitor dimensions
        mon_x, mon_y, mon_width, mon_height = self.get_monitor_geometry()
        
        # Get current position and size
        win_x = self.root.winfo_x()
        win_y = self.root.winfo_y()
        win_width = self.root.winfo_width()
        win_height = self.root.winfo_height()
        
        # Calculate target position based on dock side
        if self.dock_side == "left":
            target_x = mon_x - win_width + self.dock_reveal_size
            current_pos = win_x
            step = (target_x - current_pos) // self.dock_animation_steps
            
            def animate_step(step_count):
                new_x = win_x + (step * step_count)
                if step_count >= self.dock_animation_steps or new_x <= target_x:
                    self.root.geometry(f"+{target_x}+{win_y}")
                    self._animation_after_id = None
                    self._hover_check_id = self.root.after(100, self.check_hover)
                else:
                    self.root.geometry(f"+{new_x}+{win_y}")
                    self._animation_after_id = self.root.after(
                        self.dock_animation_ms, 
                        lambda: animate_step(step_count + 1)
                    )
                    
        elif self.dock_side == "right":
            target_x = mon_x + mon_width - self.dock_reveal_size
            current_pos = win_x
            step = (target_x - current_pos) // self.dock_animation_steps
            
            def animate_step(step_count):
                new_x = win_x + (step * step_count)
                if step_count >= self.dock_animation_steps or new_x >= target_x:
                    self.root.geometry(f"+{target_x}+{win_y}")
                    self._animation_after_id = None
                    self._hover_check_id = self.root.after(100, self.check_hover)
                else:
                    self.root.geometry(f"+{new_x}+{win_y}")
                    self._animation_after_id = self.root.after(
                        self.dock_animation_ms, 
                        lambda: animate_step(step_count + 1)
                    )
                    
        elif self.dock_side == "top":
            target_y = mon_y - win_height + self.dock_reveal_size
            current_pos = win_y
            step = (target_y - current_pos) // self.dock_animation_steps
            
            def animate_step(step_count):
                new_y = win_y + (step * step_count)
                if step_count >= self.dock_animation_steps or new_y <= target_y:
                    self.root.geometry(f"+{win_x}+{target_y}")
                    self._animation_after_id = None
                    self._hover_check_id = self.root.after(100, self.check_hover)
                else:
                    self.root.geometry(f"+{win_x}+{new_y}")
                    self._animation_after_id = self.root.after(
                        self.dock_animation_ms, 
                        lambda: animate_step(step_count + 1)
                    )
                    
        elif self.dock_side == "bottom":
            target_y = mon_y + mon_height - self.dock_reveal_size
            current_pos = win_y
            step = (target_y - current_pos) // self.dock_animation_steps
            
            def animate_step(step_count):
                new_y = win_y + (step * step_count)
                if step_count >= self.dock_animation_steps or new_y >= target_y:
                    self.root.geometry(f"+{win_x}+{target_y}")
                    self._animation_after_id = None
                    self._hover_check_id = self.root.after(100, self.check_hover)
                else:
                    self.root.geometry(f"+{win_x}+{new_y}")
                    self._animation_after_id = self.root.after(
                        self.dock_animation_ms, 
                        lambda: animate_step(step_count + 1)
                    )
        
        # Start animation
        self._animation_after_id = self.root.after(0, lambda: animate_step(1))
    
    def check_hover(self):
        """Periodically check if mouse is hovering over the visible part of the window"""
        if not self.is_docked:
            self._hover_check_id = None
            return
            
        # Get mouse position
        mouse_x = self.root.winfo_pointerx()
        mouse_y = self.root.winfo_pointery()
        
        # Get window position
        win_x = self.root.winfo_rootx()
        win_y = self.root.winfo_rooty()
        win_width = self.root.winfo_width()
        win_height = self.root.winfo_height()
        
        # Debug info
        # print(f"Mouse: {mouse_x}, {mouse_y} | Window: {win_x}, {win_y}, {win_width}x{win_height}")
        
        # Check if mouse is over the visible part, with larger detection area
        is_hovering = False
        
        # Increase the detection area slightly for better user experience
        hover_padding = 5
        
        if self.dock_side == "left":
            # Add extra detection area to the right of the visible part
            is_hovering = (win_x <= mouse_x <= win_x + self.dock_reveal_size + hover_padding and
                         win_y - hover_padding <= mouse_y <= win_y + win_height + hover_padding)
        elif self.dock_side == "right":
            # Add extra detection area to the left of the visible part
            is_hovering = (win_x - hover_padding <= mouse_x <= win_x + self.dock_reveal_size and
                         win_y - hover_padding <= mouse_y <= win_y + win_height + hover_padding)
        elif self.dock_side == "top":
            # Add extra detection area below the visible part
            is_hovering = (win_x - hover_padding <= mouse_x <= win_x + win_width + hover_padding and
                         win_y <= mouse_y <= win_y + self.dock_reveal_size + hover_padding)
        elif self.dock_side == "bottom":
            # Add extra detection area above the visible part
            is_hovering = (win_x - hover_padding <= mouse_x <= win_x + win_width + hover_padding and
                         win_y - hover_padding <= mouse_y <= win_y + self.dock_reveal_size)
        
        # Show window if hovering
        if is_hovering:
            self.show_window()
        else:
            # Schedule next check
            self._hover_check_id = self.root.after(100, self.check_hover)

    def configure_theme(self):
        """Configure the application theme (dark/light mode)"""
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

    def toggle_theme(self):
        """Toggle between dark and light theme"""
        if self.theme_mode == "dark":
            self.theme_mode = "light"
        else:
            self.theme_mode = "dark"
        self.configure_theme()

    def get_existing_categories(self):
        """Retrieve all existing categories from the treeview"""
        categories = set()
        for item in self.tree.get_children():
            category = self.tree.item(item)["values"][1]
            if category:
                categories.add(category)
        return sorted(list(categories))

    def open_settings(self):
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
                self.end_time   = time(h,m)
                self.interval   = int(i_ent.get())
            except Exception as ex:
                messagebox.showerror("Bad value", ex)
                return
            dlg.destroy()
            self.schedule_next()

        btn_frame = ttk.Frame(settings_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="OK", command=save_and_close).pack(pady=5, padx=5)

    def schedule_next(self):
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
        today_end   = datetime.combine(now.date(), self.end_time)

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
        self._after_id = self.root.after(int(delta), self.show_prompt)
        
        # Start updating the countdown
        self.update_countdown()

    def update_countdown(self):
        """Update the countdown timer display"""
        if not self.next_reminder:
            self.countdown_label.config(text="Next prompt: Not scheduled")
            return
            
        now = datetime.now()
        if now >= self.next_reminder:
            self.countdown_label.config(text="Prompting now...")
            return
            
        # Calculate time difference
        time_diff = self.next_reminder - now
        hours, remainder = divmod(time_diff.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if time_diff.days > 0:
            countdown_text = f"Next prompt: {time_diff.days}d {hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            countdown_text = f"Next prompt: {hours:02d}:{minutes:02d}:{seconds:02d}"
            
        # Use themed colors instead of direct color changes
        if self.theme_mode == "dark":
            if time_diff.seconds < 60:  # Less than 1 minute
                self.countdown_label.configure(style="CountdownUrgent.TLabel")
            elif time_diff.seconds < 300:  # Less than 5 minutes
                self.countdown_label.configure(style="CountdownWarning.TLabel")
            else:
                self.countdown_label.configure(style="CountdownNormal.TLabel")
        else:
            # Original color scheme for light mode
            if time_diff.seconds < 60:  # Less than 1 minute
                self.countdown_label.configure(foreground="red")
            elif time_diff.seconds < 300:  # Less than 5 minutes
                self.countdown_label.configure(foreground="orange")
            else:
                self.countdown_label.configure(foreground="blue")
            
        self.countdown_label.configure(text=countdown_text)
        
        # Schedule the next update in 1 second
        self._countdown_after_id = self.root.after(1000, self.update_countdown)

    def trigger_prompt_early(self, event=None):
        """Trigger the prompt early when countdown is clicked"""
        if self._after_id:
            self.root.after_cancel(self._after_id)
            self._after_id = None
            # Reset next_reminder to ensure proper scheduling when canceled
            self.next_reminder = None
            self.show_prompt()
        
    def show_prompt(self):
        """Show time entry prompt in main window"""
        # Force window to foreground
        self.root.attributes('-topmost', True)
        self.root.attributes('-topmost', False)
        
        # Play notification sound
        self.root.bell()
        
        # Find main frame to place the entry frame
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Frame) and widget != self.status_frame:
                main_frame = widget
                break
        else:
            # If not found, use the root as parent
            main_frame = self.root
        
        # Show the entry section
        self.entry_frame.pack_forget()  # First remove it if it's already packed
        self.entry_frame.pack(in_=main_frame, fill=tk.X, padx=5, pady=5, before=self.tree_frame)
        
        # Focus on the category combo box
        self.category_combo.focus_force()
        
        # Update category list
        self.update_category_list()
        
        # Pre-populate with last values
        self.category_var.set(self.last_category)
        self.description_var.set(self.last_description)
        
        # Start auto-record countdown
        self.start_auto_record_countdown(self.auto_record_seconds)
        
        # Schedule next reminder when current one starts
        self.schedule_next()

    def save_entry(self, event=None):
        """Save the current entry data"""
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
            
            # Update the item with the original timestamp and new category/description
            self.tree.item(self.editing_item_id, values=(original_timestamp, category, description))
            self.currently_editing = False
            self.editing_item_id = None
        else:
            # Insert a new item with current timestamp
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.tree.insert("", "end", values=(ts, category, description))
        
        # Mark as modified
        self.mark_as_modified()
        
        # Clear the entry fields
        self.category_var.set("")
        self.description_var.set("")
        
        # Hide entry frame
        self.entry_frame.pack_forget()
        
        # Cancel auto-record timer
        if self._auto_record_timer:
            self.root.after_cancel(self._auto_record_timer)
            self._auto_record_timer = None
        
        # Schedule next reminder
        self.schedule_next()

    def on_entry_modified(self, event=None):
        """Handle when the user modifies an entry field to reset the auto-record timer"""
        # Mark that user is actively editing
        self.currently_editing = True
        
        # Reset the auto-record countdown when the user makes changes
        self.start_auto_record_countdown(self.auto_record_seconds)

    def on_tree_double_click(self, event=None):
        """Handle double-click on treeview item to edit it"""
        # Get the selected item
        item_id = self.tree.focus()
        if not item_id:
            return
            
        # Get the current values
        values = self.tree.item(item_id)['values']
        if not values or len(values) < 3:
            return
        
        # Find main frame to place the entry frame
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Frame) and widget != self.status_frame:
                main_frame = widget
                break
        else:
            # If not found, use the root as parent
            main_frame = self.root
        
        # Show entry fields
        self.entry_frame.pack_forget()  # First remove it if it's already packed
        self.entry_frame.pack(in_=main_frame, fill=tk.X, padx=5, pady=5, before=self.tree_frame)
        
        # Set the current values
        self.category_var.set(values[1])
        self.description_var.set(values[2].replace(" [Auto-recorded]", ""))
        
        # Set the editing item ID
        self.editing_item_id = item_id
        self.currently_editing = True
        
        # Focus on category field
        self.category_combo.focus_force()
        
        # Start auto-record countdown
        self.start_auto_record_countdown(self.auto_record_seconds)
        
        # Bring window to front
        self.root.attributes('-topmost', True)
        self.root.attributes('-topmost', False)
        
        # Play notification sound to attract attention
        self.root.bell()

    def update_category_list(self):
        """Update the category list in the combobox from the treeview"""
        categories = self.get_existing_categories()
        self.category_combo['values'] = categories

    def mark_as_modified(self):
        """Mark the file as having unsaved changes and update window title"""
        if not self.has_unsaved_changes:
            self.has_unsaved_changes = True
            self.update_window_title()
            
    def update_window_title(self):
        """Update the window title based on current file and modified status"""
        title = "Time Tracker"
        
        if self.current_file:
            # Get the base filename without extension
            basename = os.path.splitext(os.path.basename(self.current_file))[0]
            title = f"Time Tracker - {basename}"
            
        if self.has_unsaved_changes:
            title += " *"
            
        self.root.title(title)
    
    def new_file(self):
        """Create a new empty file"""
        # Check for unsaved changes first
        if self.has_unsaved_changes and self.tree.get_children():
            if not messagebox.askyesno("Unsaved Changes", 
                                      "You have unsaved changes. Create a new file anyway?"):
                return
                
        # Clear the treeview
        self.tree.delete(*self.tree.get_children())
        
        # Reset current file and modified status
        self.current_file = None
        self.has_unsaved_changes = False
        self.update_window_title()
    
    def save_current_file(self, event=None):
        """Save to the current file or prompt for a location if none"""
        if self.current_file:
            return self.save_to_file(self.current_file)
        else:
            return self.save_data()
    
    def save_to_file(self, filepath):
        """Save data to the specified file path"""
        try:
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "category", "description"])
                for row in self.tree.get_children():
                    writer.writerow(self.tree.item(row)["values"])
            
            # Update current file and status
            self.current_file = filepath
            self.has_unsaved_changes = False
            self.update_window_title()
            
            # Add to recent files
            self.add_to_recent_files(filepath)
            
            return True
        except Exception as e:
            messagebox.showerror("Save Error", f"Error saving file: {e}")
            return False
    
    def save_data(self):
        """Save data to a new file location"""
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files","*.csv")],
            initialfile="" if not self.current_file else os.path.basename(self.current_file)
        )
        if not path: 
            return False
            
        success = self.save_to_file(path)
        return success
    
    def load_data(self):
        """Load data from a file"""
        # Check for unsaved changes first
        if self.has_unsaved_changes and self.tree.get_children():
            if not messagebox.askyesno("Unsaved Changes", 
                                      "You have unsaved changes. Load a new file anyway?"):
                return
                
        path = filedialog.askopenfilename(filetypes=[("CSV files","*.csv")])
        if not path: 
            return
            
        self.load_file(path)
    
    def load_file(self, filepath):
        """Load data from the specified file path"""
        try:
            with open(filepath, newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None)  # skip header
                self.tree.delete(*self.tree.get_children())
                for row in reader:
                    if len(row) == 2:  # Handle old format
                        ts, description = row
                        category = ""
                        self.tree.insert("", "end", values=(ts, category, description))
                    elif len(row) >= 3:  # New format
                        self.tree.insert("", "end", values=(row[0], row[1], row[2]))
            
            # Update current file and status
            self.current_file = filepath
            self.has_unsaved_changes = False
            self.update_window_title()
            
            # Add to recent files
            self.add_to_recent_files(filepath)
            
            # Update category list
            self.update_category_list()
            return True
        except Exception as e:
            messagebox.showerror("Load Error", f"Error loading file: {e}")
            return False
    
    def add_to_recent_files(self, filepath):
        """Add a file to the recent files list"""
        # Remove if already in list
        if filepath in self.recent_files:
            self.recent_files.remove(filepath)
            
        # Add to front of list
        self.recent_files.insert(0, filepath)
        
        # Trim if needed
        if len(self.recent_files) > self.max_recent_files:
            self.recent_files = self.recent_files[:self.max_recent_files]
            
        # Update menu
        self.update_recent_files_menu()
    
    def update_recent_files_menu(self):
        """Update the recent files dropdown menu"""
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
                    command=lambda p=path: self.load_file(p)
                )

    def load_config(self):
        """Load the configuration from the config file, or create default if it doesn't exist"""
        if not self.config_file.exists():
            self.save_config(self.default_config)
            return self.default_config
        
        with open(self.config_file, "r") as f:
            config = json.load(f)
        return config

    def save_config(self, config):
        """Save the configuration to the config file"""
        self.config_dir.mkdir(parents=True, exist_ok=True)  # Create config directory if it doesn't exist
        with open(self.config_file, "w") as f:
            json.dump(config, f, indent=4)

    def start_auto_record_countdown(self, seconds):
        """Start the auto-record countdown with progress bar"""
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
                self.auto_record_entry()
                return
                
            # Update progress bar
            new_progress = current_progress - decrement_per_sec
            self.progress_var.set(max(0, new_progress))
            
            # Schedule next update
            self._auto_record_timer = self.root.after(1000, lambda: 
                update_progress_and_countdown(remaining_seconds - 1, new_progress))
        
        # Start the countdown
        update_progress_and_countdown(seconds, 100)

if __name__ == "__main__":
    root = tk.Tk()
    app = TimeTrackerApp(root)
    root.mainloop()
