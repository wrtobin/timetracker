# Time Tracker: Future Improvements

This document outlines planned enhancements and known issues for the Time Tracker application.
See [README.md](README.md) for current features and usage instructions.

## High Priority

### Docking Functionality
- [ ] Fix multi-monitor docking behavior, especially at monitor boundaries
- [ ] Improve visibility of docked window edges with clear visual indicators
- [ ] Fix window positioning when docked to prevent unintended movement
- [ ] Ensure the window properly returns to its fully visible position when hovered

### UI Improvements
- [ ] Add proper window restore/minimize/close buttons when docked
- [ ] Implement smoother animations for dock/undock transitions
- [ ] Fix content frame handling when switching between docked/undocked states

## Medium Priority

### Feature Enhancements
- [ ] Add data visualization (charts/graphs of time usage)
- [ ] Implement statistics dashboard (daily/weekly summaries)
- [ ] Add project-based organization for entries
- [ ] Create search/filter functionality for time entries
- [ ] Support for data export in multiple formats (Excel, JSON)

### Technical Improvements
- [ ] Refactor monitor detection logic for better multi-monitor support
- [ ] Move to a proper database rather than CSV for data storage
- [ ] Add keyboard shortcuts for common actions
- [ ] Consider packaging as a standalone application

## Low Priority

### Polish
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
