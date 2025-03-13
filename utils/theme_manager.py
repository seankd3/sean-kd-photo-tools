import os
import json
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt

class ThemeManager:
    """Manages application themes and colors."""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.themes = {
            "dark": {
                "app_background": "#1e1e1e",
                "sidebar_background": "#2d2d2d",
                "module_background": "#2a2a2a",
                "card_background": "#333333",
                "primary_text": "#ffffff",
                "secondary_text": "#b0b0b0",
                "accent_color": "#0078d4",
                "button_background": "#3a3a3a",
                "button_hover": "#4a4a4a",
                "border_color": "#444444",
                "success_color": "#0f9d58",
                "warning_color": "#f4b400",
                "error_color": "#db4437"
            },
            "light": {
                "app_background": "#f5f5f5",
                "sidebar_background": "#e0e0e0",
                "module_background": "#f0f0f0",
                "card_background": "#ffffff",
                "primary_text": "#212121",
                "secondary_text": "#666666",
                "accent_color": "#0078d4",
                "button_background": "#e7e7e7",
                "button_hover": "#d7d7d7",
                "border_color": "#cccccc",
                "success_color": "#0f9d58",
                "warning_color": "#f4b400",
                "error_color": "#db4437"
            }
        }
        
        # Theme paths
        self.config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config")
        os.makedirs(self.config_dir, exist_ok=True)
        self.theme_file = os.path.join(self.config_dir, "themes.json")
        
        # Load custom themes if available
        self.load_custom_themes()
    
    def load_custom_themes(self):
        """Load custom themes from configuration file."""
        if os.path.exists(self.theme_file):
            try:
                with open(self.theme_file, 'r') as f:
                    custom_themes = json.load(f)
                    # Merge with existing themes, overwriting default ones if needed
                    self.themes.update(custom_themes)
            except Exception as e:
                print(f"Error loading custom themes: {e}")
    
    def save_custom_theme(self, theme_name, theme_data):
        """Save a custom theme to the configuration file."""
        # Update themes dictionary
        self.themes[theme_name] = theme_data
        
        # Save all themes to file
        try:
            with open(self.theme_file, 'w') as f:
                json.dump(self.themes, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving custom theme: {e}")
            return False
    
    def apply_theme(self, theme_name):
        """Apply the specified theme to the application."""
        if theme_name not in self.themes:
            theme_name = "dark"  # Default to dark theme
        
        theme = self.themes[theme_name]
        
        # Create style sheet
        style_sheet = f"""
        /* Global Styles */
        QWidget {{
            background-color: {theme["app_background"]};
            color: {theme["primary_text"]};
            font-family: "Segoe UI", Arial, sans-serif;
        }}
        
        /* Sidebar */
        #sidebar {{
            background-color: {theme["sidebar_background"]};
            border-right: 1px solid {theme["border_color"]};
        }}
        
        QToolButton {{
            background-color: {theme["sidebar_background"]};
            color: {theme["secondary_text"]};
            border: none;
            border-radius: 6px;
            padding: 8px;
        }}
        
        QToolButton:hover {{
            background-color: {theme["button_hover"]};
        }}
        
        QToolButton:checked {{
            background-color: {theme["accent_color"]};
            color: white;
        }}
        
        /* Content Area */
        QStackedWidget {{
            background-color: {theme["module_background"]};
        }}
        
        /* Buttons */
        QPushButton {{
            background-color: {theme["button_background"]};
            color: {theme["primary_text"]};
            border: 1px solid {theme["border_color"]};
            padding: 8px 16px;
            border-radius: 4px;
        }}
        
        QPushButton:hover {{
            background-color: {theme["button_hover"]};
        }}
        
        QPushButton:pressed {{
            background: {theme["accent_color"]};
            color: white;
        }}
        
        /* Progress Bar */
        QProgressBar {{
            border: 1px solid {theme["border_color"]};
            border-radius: 3px;
            background-color: {theme["app_background"]};
            text-align: center;
        }}
        
        QProgressBar::chunk {{
            background-color: {theme["accent_color"]};
            width: 10px;
            margin: 0.5px;
        }}
        
        /* Scroll Areas */
        QScrollArea {{
            border: 1px solid {theme["border_color"]};
            background-color: {theme["module_background"]};
        }}
        
        /* Scroll Bar */
        QScrollBar:vertical {{
            border: none;
            background-color: {theme["app_background"]};
            width: 10px;
            margin: 0px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {theme["border_color"]};
            min-height: 20px;
            border-radius: 5px;
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        
        QScrollBar:horizontal {{
            border: none;
            background-color: {theme["app_background"]};
            height: 10px;
            margin: 0px;
        }}
        
        QScrollBar::handle:horizontal {{
            background-color: {theme["border_color"]};
            min-width: 20px;
            border-radius: 5px;
        }}
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}
        
        /* Menu Bar */
        QMenuBar {{
            background-color: {theme["sidebar_background"]};
            color: {theme["primary_text"]};
            border-bottom: 1px solid {theme["border_color"]};
        }}
        
        QMenuBar::item {{
            background: transparent;
            padding: 8px 12px;
        }}
        
        QMenuBar::item:selected {{
            background: {theme["button_hover"]};
        }}
        
        QMenu {{
            background-color: {theme["sidebar_background"]};
            border: 1px solid {theme["border_color"]};
        }}
        
        QMenu::item {{
            padding: 6px 24px 6px 12px;
        }}
        
        QMenu::item:selected {{
            background-color: {theme["button_hover"]};
        }}
        
        /* Combo Box */
        QComboBox {{
            background-color: {theme["button_background"]};
            color: {theme["primary_text"]};
            border: 1px solid {theme["border_color"]};
            padding: 4px 8px;
            border-radius: 4px;
            min-width: 6em;
        }}
        
        QComboBox:hover {{
            background-color: {theme["button_hover"]};
        }}
        
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 15px;
            border-left: 1px solid {theme["border_color"]};
        }}
        
        /* Slider */
        QSlider::groove:horizontal {{
            border: 1px solid {theme["border_color"]};
            height: 8px;
            background: {theme["app_background"]};
            margin: 2px 0;
            border-radius: 4px;
        }}
        
        QSlider::handle:horizontal {{
            background: {theme["accent_color"]};
            border: 1px solid {theme["accent_color"]};
            width: 16px;
            height: 16px;
            margin: -5px 0;
            border-radius: 8px;
        }}
        
        QSlider::handle:horizontal:hover {{
            background: {theme["primary_text"]};
        }}
        
        /* Tabs */
        QTabWidget::pane {{
            border: 1px solid {theme["border_color"]};
            background-color: {theme["module_background"]};
        }}
        
        QTabBar::tab {{
            background-color: {theme["sidebar_background"]};
            color: {theme["secondary_text"]};
            padding: 8px 16px;
            border: 1px solid {theme["border_color"]};
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {theme["module_background"]};
            color: {theme["primary_text"]};
        }}
        
        QTabBar::tab:hover:!selected {{
            background-color: {theme["button_hover"]};
        }}
        
        /* Line Edit */
        QLineEdit {{
            background-color: {theme["app_background"]};
            color: {theme["primary_text"]};
            border: 1px solid {theme["border_color"]};
            padding: 4px 8px;
            border-radius: 4px;
        }}
        
        QLineEdit:focus {{
            border: 1px solid {theme["accent_color"]};
        }}
        
        /* Group Box */
        QGroupBox {{
            border: 1px solid {theme["border_color"]};
            border-radius: 4px;
            margin-top: 20px;
            padding-top: 16px;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 6px;
            color: {theme["primary_text"]};
        }}
        
        /* Labels */
        QLabel {{
            color: {theme["primary_text"]};
            background: transparent;
        }}
        
        /* Tooltips */
        QToolTip {{
            background-color: {theme["card_background"]};
            color: {theme["primary_text"]};
            border: 1px solid {theme["border_color"]};
            padding: 4px;
        }}
        """
        
        # Apply stylesheet to application
        QApplication.instance().setStyleSheet(style_sheet)
        
        # Save current theme in settings
        if self.parent and hasattr(self.parent, 'settings_manager'):
            self.parent.settings_manager.set("theme", theme_name)
        
        return True
    
    def get_theme_colors(self, theme_name=None):
        """Get the colors for a specific theme."""
        if not theme_name or theme_name not in self.themes:
            theme_name = "dark"  # Default to dark theme
        
        return self.themes.get(theme_name, self.themes["dark"])
    
    def get_available_themes(self):
        """Get a list of all available theme names."""
        return list(self.themes.keys())
