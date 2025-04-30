# Time Tracker

A simple but powerful time tracking application built with Python and Tkinter.

## Features

- **Timed Reminders**: Get prompted at regular intervals to record your activities
- **Direct Entry**: Add time entries directly in the main window with category suggestions
- **In-line Editing**: Double-click any entry to modify it
- **Visual Countdown**: See the time remaining before auto-recording with a progress bar
- **Activity Categorization**: Organize entries with categories and descriptions
- **Smart File Management**: Track current file with unsaved changes indicator
- **Recent Files**: Quickly access recently used tracking files
- **Dark/Light Theme**: Switch between visual themes for comfort
- **Dockable Interface**: Dock the application to any screen edge to save space
- **Data Persistence**: Save and load your time entries as CSV files
- **Multi-monitor Support**: Works across multiple displays
- **Configurable Settings**: Customize reminders, auto-record timeout, and more

## Getting Started

1. Ensure you have Python 3.6+ installed
2. Install required packages:
   ```
   pip install -r requirements.txt
   ```
3. Run the application:
   ```
   python timetracker.py
   ```
4. Configure your reminder intervals via Settings → Configure Reminders
5. Start tracking your time!

## Using the Application

### Time Entry

When prompted (or when clicking the countdown timer):
- **Category**: Select or type a category (offers suggestions based on existing entries)
- **Description**: Add details about what you were doing

Entries are automatically recorded after the configured timeout if left unattended (default: 60 seconds).

### Editing Entries

- **Double-click** any entry in the list to modify it
- Make your changes and press **Enter** or click **Save** to update
- Auto-save will still occur if no changes are made within the timeout period

### File Management

- **New File**: File → New to start a new tracking session
- **Open**: File → Open... to import previously saved data
- **Save**: File → Save (Ctrl+S) to save the current file
- **Save As**: File → Save As... to save to a new location
- **Recent Files**: Access recently opened files from the File → Recent Files menu

The window title shows the current file name and indicates unsaved changes with an asterisk (*).

### Docking

The application can be docked to any screen edge:
- Settings → Docking Options → Dock to Left/Right/Top/Bottom
- When docked, hover over the visible edge to reveal the full window
- Undock from the same menu

## Configuration

The application stores your settings (including recent files) in:
- Windows: %APPDATA%\TimeTracker\TimeTracker\settings.json
- macOS: ~/Library/Application Support/TimeTracker/settings.json
- Linux: ~/.config/TimeTracker/settings.json

## See Also

Check the [TODO.md](TODO.md) file for planned improvements and known issues.
