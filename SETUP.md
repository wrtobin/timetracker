# TimeTracker - Development and Deployment Guide

This document provides instructions for setting up the development environment and building a standalone executable.

## Development Setup

### Prerequisites

- Python 3.6 or higher
- Visual Studio Code (recommended)

### Setting up the Development Environment

1. Clone or download the repository
2. Run the setup script to create a virtual environment and install dependencies:

```
python setup_project.py
```

3. Activate the virtual environment:
   - Windows: `.venv\Scripts\activate`
   - macOS/Linux: `source .venv/bin/activate`

4. Open the project in Visual Studio Code:

```
code .
```

5. VS Code should detect the Python interpreter in your virtual environment. If not, press `Ctrl+Shift+P` and select "Python: Select Interpreter", then choose the one in the `.venv` folder.

### Running the Application in Development Mode

- Press F5 in VS Code to start with the debugger
- Or run manually: `python timetracker.py`

## Creating a Standalone Executable

### Building with PyInstaller

1. Ensure you have completed the development setup steps
2. Activate the virtual environment
3. Run the build script:

```
python build.py
```

4. The executable will be created in the `dist` folder

### Customizing the Build

- Add your application icon as `assets/timetracker.ico`
- Modify `build.py` to add additional files or change build settings

## Project Structure

```
timetracker/
├── .vscode/                # VS Code configuration
│   ├── launch.json         # Debug configuration
│   ├── settings.json       # Editor settings
│   └── extensions.json     # Recommended extensions
├── assets/                 # Application resources
│   └── timetracker.ico     # Application icon
├── dist/                   # Built executables (generated)
├── build/                  # Build artifacts (generated)
├── .venv/                  # Virtual environment (generated)
├── timetracker.py          # Main application code
├── setup.py                # Package configuration
├── setup_project.py        # Development setup script
├── build.py                # Build script for executable
├── requirements.txt        # Python dependencies
├── README.md               # General information
├── TODO.md                 # Future improvements
└── SETUP.md                # This file
```

## Troubleshooting

### Missing Dependencies
If you encounter missing dependency errors when running the application, try:
```
pip install -r requirements.txt
```

### Build Issues
If PyInstaller fails to create the executable:
1. Make sure all imports in the code are for installed packages
2. Try running with verbose output: `pyinstaller --verbose timetracker.py`
3. Check if any hidden imports are needed

### Running the Executable
If the executable fails to start:
1. Try running it from the command line to see error messages
2. Ensure all required files are included in the build
3. Check for any path-related issues in the code
