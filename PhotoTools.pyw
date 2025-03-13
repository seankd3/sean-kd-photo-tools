#!/usr/bin/env python
"""
SeanKD PhotoTools Suite Launcher
This script launches the SeanKD PhotoTools Suite application.
"""

import sys
import os
import traceback
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QIcon

# Add the current directory to the path so we can import our modules
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

def show_error_message(error_text):
    """Show an error message box with the given text."""
    app = QApplication.instance() or QApplication(sys.argv)
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Icon.Critical)
    msg_box.setWindowTitle("PhotoTools Error")
    msg_box.setText("An error occurred while starting PhotoTools:")
    msg_box.setDetailedText(error_text)
    msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg_box.exec()

def main():
    """Main entry point for the application."""
    try:
        # Import the main application class
        from PhotoToolsApp import PhotoToolsApp
        
        # Create the application
        app = QApplication(sys.argv)
        
        # Set application icon if available
        icon_path = os.path.join(script_dir, "resources", "icons", "app_icon.png")
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
        
        # Create and show the main window
        window = PhotoToolsApp()
        window.show()
        
        # Run the application
        sys.exit(app.exec())
    
    except ImportError as e:
        error_text = f"Failed to import required module: {e}\n\n"
        error_text += "Please make sure all dependencies are installed.\n"
        error_text += f"Full error: {traceback.format_exc()}"
        show_error_message(error_text)
    
    except Exception as e:
        error_text = f"Unexpected error: {e}\n\n"
        error_text += f"Full error: {traceback.format_exc()}"
        show_error_message(error_text)

if __name__ == "__main__":
    main()
