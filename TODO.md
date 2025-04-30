# Time Tracker: Future Improvements

This document outlines planned enhancements and known issues for the Time Tracker application.
See [README.md](README.md) for current features and usage instructions.

## v0.3 Service Architecture Refactoring (Current Focus)

The goal for v0.3 is to refactor the application into a clear frontend/backend separation while maintaining identical user-facing behavior. This will enable future improvements like alternative frontends (web, mobile) and remote service capabilities.

### Core Architecture Changes
- [x] Define a formal interaction protocol between frontend and backend components
- [x] Create a JSON schema for all message types in the protocol
- [x] Implement backend service classes for core functionality:
  - [x] TimeEntryService (entry management, categories, etc.)
  - [ ] ConfigurationService (settings, user preferences)
  - [x] FileStorageService (file operations, recent files)
    - [x] Define message types for file operations
    - [x] Implement the service interface
    - [x] Add backend implementation for file storage
    - [x] Update UI controller to use message bus for file operations
  - [ ] ReminderService (scheduling, notifications)
- [x] Create frontend controller to translate UI events to protocol messages
- [x] Convert direct function calls to message-based communication
  - [x] Time entry operations
  - [x] File operations
  - [ ] Configuration operations
- [x] Implement in-memory message bus for frontend/backend communication
- [x] Fix KeyError for 'timestamp' in TimeTrackerUI
- [x] Standardize timestamp field naming convention (using end_time as the primary field)
- [IN PROGRESS] Move all business logic from UI to appropriate service classes
- [ ] Ensure complete test coverage for backend services

### Project Structure Improvements
- [x] Reorganize codebase into packages (frontend, backend, protocol)
- [IN PROGRESS] Create clean interfaces for all services 
- [ ] Add proper dependency injection patterns
- [x] Implement logging throughout the application
- [ ] Add unit tests for critical components
- [ ] Update build scripts to handle new project structure

## High Priority (Post v0.3)

### UI and Workflow Improvements
- [x] Replace popup prompt with direct entry in the main window
- [x] Add ability to edit existing entries by double-clicking them
- [x] Add visual countdown timer with progress bar for auto-record
- [x] Make auto-record timeout configurable in settings
- [x] Implement audio cue for prompting user attention
- [x] Pre-populate form with last used category and description
- [ ] Refine entry field validation and error handling
- [ ] Add keyboard shortcuts for common actions
- [ ] Implement advanced categorization with hierarchical tags

### File Handling
- [x] Add proper file management with current file tracking
- [x] Add Ctrl+S shortcut to save current file
- [x] Display filename in window title with unsaved changes indicator
- [x] Add persistent recent files list with configuration storage
- [x] Auto-load the most recently used file at application startup
- [ ] Implement autosave functionality with configurable intervals
- [ ] Add backup file creation before saving
- [ ] Support for storage abstraction (files, database, cloud)

### Architecture Improvements
- [ ] Move to a proper database rather than CSV for data storage
- [ ] Implement cross-platform file and configuration handling
- [ ] Add proper error handling and recovery mechanisms

## Medium Priority

### Feature Enhancements
- [ ] Add data visualization (charts/graphs of time usage)
- [ ] Implement statistics dashboard (daily/weekly summaries)
- [ ] Add project-based organization for entries
- [ ] Create search/filter functionality for time entries
- [ ] Support for data export in multiple formats (Excel, JSON)

### Docking Functionality
- [ ] Fix multi-monitor docking behavior, especially at monitor boundaries
- [ ] Improve visibility of docked window edges with clear visual indicators
- [ ] Fix window positioning when docked to prevent unintended movement
- [ ] Ensure the window properly returns to its fully visible position when hovered
- [ ] Add proper window restore/minimize/close buttons when docked
- [ ] Implement smoother animations for dock/undock transitions
- [ ] Fix content frame handling when switching between docked/undocked states

## Low Priority

### Polish
- [x] Fix theme initialization to properly apply dark/light theme at startup
- [ ] Add more theme options
- [ ] Create a proper icon and application branding
- [ ] Add internationalization support
- [ ] Add startup option to system tray
- [ ] Implement custom dialog animations

## Known Issues

1. Docked window may not be visible when positioned at the boundary between monitors
2. Window animation sometimes leaves the application in an incorrect position
3. Multi-monitor support is limited and doesn't handle all monitor configurations
4. No proper installation script or package
5. Limited keyboard navigation support

## Future Service Architecture Roadmap (v0.4+)

### Process Separation
- [ ] Extract backend into a standalone service process
- [ ] Implement inter-process communication (IPC) 
- [ ] Add proper service discovery and connection management
- [ ] Implement connection resilience and reconnection logic

### Remote Access
- [ ] Implement secure client-server communication
- [ ] Create WebSocket or REST API for remote clients
- [ ] Add authentication and permission system
- [ ] Develop web frontend as alternative interface

### Advanced Features
- [ ] Add plugin architecture for extensibility
- [ ] Implement proper logging and telemetry services
- [ ] Create synchronization service for cloud/remote storage
- [ ] Support for multiple concurrent views of the same data

### Benefits of Service Architecture
1. Clear separation of concerns between UI and business logic
2. Easier testing with mocked services
3. Possibility to change UI framework without affecting core functionality
4. Foundation for potential client-server implementation or web interface
5. Better scalability for adding new features
