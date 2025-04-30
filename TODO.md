# Time Tracker: Future Improvements

This document outlines planned enhancements and known issues for the Time Tracker application.
See [README.md](README.md) for current features and usage instructions.

## High Priority

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

### Architecture Improvements
- [ ] Refactor to service-based architecture (see roadmap below)
- [ ] Move to a proper database rather than CSV for data storage
- [ ] Implement proper dependency injection for better testability

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

## Service-Based Architecture Roadmap

### Phase 1: Planning and Design
- [ ] Define service interfaces and responsibilities
- [ ] Design data flow between UI and services
- [ ] Create domain models separate from UI representation
- [ ] Plan transition strategy with minimal disruption

### Phase 2: Core Services Implementation
- [ ] Create TimeTrackingService to manage entries and categories
- [ ] Develop FileService for file operations and persistence
- [ ] Implement ConfigurationService for app settings and user preferences
- [ ] Build NotificationService for reminders and alerts

### Phase 3: UI Decoupling
- [ ] Convert direct function calls to service requests
- [ ] Implement message bus or event dispatcher for UI-service communication
- [ ] Create UI-specific view models that map to domain models
- [ ] Refactor UI components to consume services through defined interfaces

### Phase 4: Advanced Features
- [ ] Add plugin architecture for extensibility
- [ ] Implement proper logging and telemetry services
- [ ] Create synchronization service for potential cloud/remote storage
- [ ] Support for multiple concurrent views of the same data

### Benefits of Service Architecture
1. Clear separation of concerns between UI and business logic
2. Easier testing with mocked services
3. Possibility to change UI framework without affecting core functionality
4. Foundation for potential client-server implementation or web interface
5. Better scalability for adding new features
