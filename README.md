# Time Tracker

A simple but powerful time tracking application built with Python and Tkinter.

## Features

- **Timed Reminders**: Get prompted at regular intervals to record your activities
- **Activity Categorization**: Organize entries with categories and descriptions
- **Dark/Light Theme**: Switch between visual themes for comfort
- **Dockable Interface**: Dock the application to any screen edge to save space
- **Data Persistence**: Save and load your time entries as CSV files
- **Multi-monitor Support**: Works across multiple displays

## Getting Started

1. Ensure you have Python 3.6+ installed
2. Run the application:
   ```
   python timetracker.py
   ```

3. Configure your reminder intervals via Settings → Configure Reminders
4. Start tracking your time!

## Using the Application

### Time Entry

When prompted, enter:
- **Category**: The type of work (e.g., "Development", "Meeting", "Break")
- **Description**: More specific details about what you were doing

Entries are automatically added after 60 seconds if left unattended.

### Docking

The application can be docked to any screen edge:
- Settings → Docking Options → Dock to Left/Right/Top/Bottom
- When docked, hover over the visible edge to reveal the full window
- Undock from the same menu

### Data Management

- **Save**: File → Save... to export your entries as CSV
- **Load**: File → Load... to import previously saved data

## See Also

Check the [TODO.md](TODO.md) file for planned improvements and known issues.
