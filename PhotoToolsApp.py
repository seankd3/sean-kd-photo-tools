import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLabel, QStackedWidget, QSplitter, QFrame,
                           QToolButton, QSizePolicy, QScrollArea, QMenu, QMessageBox,
                           QTabWidget, QComboBox, QCheckBox, QColorDialog, QFileDialog)
from PyQt6.QtGui import QIcon, QFont, QPixmap, QAction, QColor
from PyQt6.QtCore import Qt, QSize, pyqtSignal

# Import module UIs
from modules.dng_stacker.stacker_ui import DNGStackerModule
from modules.photo_desqueezer.desqueezer_ui import DesqueezerModule
from modules.video_averager.averager_ui import VideoAveragerModule
from modules.video_smover.smover_ui import VideoSmoverModule
from modules.gif_creator.gif_ui import GIFCreatorModule
from utils.theme_manager import ThemeManager
from utils.settings_manager import SettingsManager

class SidebarButton(QToolButton):
    """Custom sidebar button with icon and text."""
    def __init__(self, text, icon_path=None, parent=None):
        super().__init__(parent)
        self.setText(text)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.setIconSize(QSize(32, 32))
        self.setFixedSize(90, 90)
        if icon_path:
            self.setIcon(QIcon(icon_path))
        else:
            # Set a default icon if none provided
            self.setIcon(QIcon.fromTheme("application-x-executable"))
        
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setCheckable(True)

class SettingsPage(QWidget):
    """Settings page for the application."""
    def __init__(self, parent=None, settings_manager=None, theme_manager=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.theme_manager = theme_manager
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Settings")
        title_font = title_label.font()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)
        
        # Create tabs
        tabs = QTabWidget()
        
        # Appearance tab
        appearance_tab = QWidget()
        appearance_layout = QVBoxLayout(appearance_tab)
        
        # Theme selection
        theme_box = QFrame()
        theme_box.setFrameShape(QFrame.Shape.StyledPanel)
        theme_layout = QVBoxLayout(theme_box)
        theme_layout.addWidget(QLabel("<b>Theme</b>"))
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(self.theme_manager.get_available_themes())
        current_theme = self.settings_manager.get("theme", "dark")
        index = self.theme_combo.findText(current_theme, Qt.MatchFlag.MatchFixedString)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
        self.theme_combo.currentTextChanged.connect(self.change_theme)
        theme_layout.addWidget(self.theme_combo)
        
        # Custom colors
        theme_layout.addWidget(QLabel("<b>Custom Colors</b>"))
        
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Accent Color:"))
        self.accent_color_btn = QPushButton()
        self.accent_color_btn.setFixedSize(24, 24)
        self.accent_color = self.settings_manager.get("accent_color", "#3498db")
        self.accent_color_btn.setStyleSheet(f"background-color: {self.accent_color};")
        self.accent_color_btn.clicked.connect(self.select_accent_color)
        color_layout.addWidget(self.accent_color_btn)
        color_layout.addStretch()
        theme_layout.addLayout(color_layout)
        
        appearance_layout.addWidget(theme_box)
        appearance_layout.addStretch()
        
        # Performance tab
        performance_tab = QWidget()
        performance_layout = QVBoxLayout(performance_tab)
        
        # Memory usage
        memory_box = QFrame()
        memory_box.setFrameShape(QFrame.Shape.StyledPanel)
        memory_layout = QVBoxLayout(memory_box)
        memory_layout.addWidget(QLabel("<b>Memory Usage</b>"))
        
        self.limit_memory_check = QCheckBox("Limit memory usage")
        self.limit_memory_check.setChecked(self.settings_manager.get("limit_memory", True))
        memory_layout.addWidget(self.limit_memory_check)
        
        performance_layout.addWidget(memory_box)
        performance_layout.addStretch()
        
        # Add tabs
        tabs.addTab(appearance_tab, "Appearance")
        tabs.addTab(performance_tab, "Performance")
        
        # Add to main layout
        main_layout.addWidget(tabs)
        
        # Save button
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.save_settings)
        main_layout.addWidget(save_btn)
    
    def change_theme(self, theme_name):
        """Change the application theme."""
        if self.theme_manager:
            self.theme_manager.apply_theme(theme_name)
    
    def select_accent_color(self):
        """Open color dialog to select accent color."""
        color = QColorDialog.getColor(QColor(self.accent_color), self, "Select Accent Color")
        if color.isValid():
            self.accent_color = color.name()
            self.accent_color_btn.setStyleSheet(f"background-color: {self.accent_color};")
    
    def save_settings(self):
        """Save settings to file."""
        if self.settings_manager:
            # Save theme
            self.settings_manager.set("theme", self.theme_combo.currentText())
            
            # Save accent color
            self.settings_manager.set("accent_color", self.accent_color)
            
            # Save memory limit
            self.settings_manager.set("limit_memory", self.limit_memory_check.isChecked())
            
            # Save to file
            self.settings_manager.save_settings()
            
            QMessageBox.information(self, "Settings", "Settings saved successfully.")

class PhotoToolsApp(QMainWindow):
    """Main application window for the PhotoTools Suite."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SeanKD PhotoTools Suite")
        self.setGeometry(100, 100, 1280, 800)
        
        # Initialize settings and theme
        self.settings_manager = SettingsManager()
        self.theme_manager = ThemeManager(self)
        
        # Setup UI
        self.init_ui()
        
        # Apply initial theme
        self.theme_manager.apply_theme(self.settings_manager.get("theme", "dark"))
        
    def init_ui(self):
        # Create central widget
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setCentralWidget(central_widget)
        
        # Create sidebar
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(100)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(5, 10, 5, 10)
        sidebar_layout.setSpacing(10)
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)
        
        # Get current directory for icons
        icons_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "icons")
        os.makedirs(icons_dir, exist_ok=True)
        
        # Create module buttons (placeholder icons for now)
        self.btn_stacker = SidebarButton("DNG\nStacker", None)
        self.btn_desqueezer = SidebarButton("Photo\nDesqueezer", None)
        self.btn_gif = SidebarButton("GIF\nCreator", None)
        self.btn_vid_avg = SidebarButton("Video\nAverager", None)
        self.btn_vid_smov = SidebarButton("Video\nSmover", None)
        
        # Add buttons to sidebar
        sidebar_layout.addWidget(self.btn_stacker)
        sidebar_layout.addWidget(self.btn_desqueezer)
        sidebar_layout.addWidget(self.btn_gif)
        sidebar_layout.addWidget(self.btn_vid_avg)
        sidebar_layout.addWidget(self.btn_vid_smov)
        sidebar_layout.addStretch()
        
        # Create settings button
        self.btn_settings = SidebarButton("Settings", None)
        sidebar_layout.addWidget(self.btn_settings)
        
        # Add sidebar to main layout
        main_layout.addWidget(self.sidebar)
        
        # Create content area
        self.content = QStackedWidget()
        
        # Create module instances
        self.stacker_module = DNGStackerModule()
        self.desqueezer_module = DesqueezerModule()
        self.gif_module = GIFCreatorModule()
        self.video_avg_module = VideoAveragerModule()
        self.video_smov_module = VideoSmoverModule()
        
        # Add modules to stacked widget
        self.content.addWidget(self.stacker_module)
        self.content.addWidget(self.desqueezer_module)
        self.content.addWidget(self.gif_module)
        self.content.addWidget(self.video_avg_module)
        self.content.addWidget(self.video_smov_module)
        
        # Create settings page
        self.settings_page = SettingsPage(self, self.settings_manager, self.theme_manager)
        self.content.addWidget(self.settings_page)
        
        # Add content to main layout
        main_layout.addWidget(self.content)
        
        # Connect button signals
        self.btn_stacker.clicked.connect(lambda: self.switch_module(0))
        self.btn_desqueezer.clicked.connect(lambda: self.switch_module(1))
        self.btn_gif.clicked.connect(lambda: self.switch_module(2))
        self.btn_vid_avg.clicked.connect(lambda: self.switch_module(3))
        self.btn_vid_smov.clicked.connect(lambda: self.switch_module(4))
        self.btn_settings.clicked.connect(lambda: self.switch_module(5))
        
        # Set initial module
        self.switch_module(0)
        
        # Create menu bar
        self.create_menu_bar()
    
    def create_menu_bar(self):
        # Create menu bar
        self.menu_bar = self.menuBar()
        
        # File menu
        file_menu = self.menu_bar.addMenu("File")
        
        # Add actions to file menu
        new_action = QAction("New Project", self)
        open_action = QAction("Open Project", self)
        save_action = QAction("Save Project", self)
        export_action = QAction("Export", self)
        exit_action = QAction("Exit", self)
        
        file_menu.addAction(new_action)
        file_menu.addAction(open_action)
        file_menu.addAction(save_action)
        file_menu.addSeparator()
        file_menu.addAction(export_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)
        
        # Connect actions
        exit_action.triggered.connect(self.close)
        
        # Edit menu
        edit_menu = self.menu_bar.addMenu("Edit")
        
        undo_action = QAction("Undo", self)
        redo_action = QAction("Redo", self)
        preferences_action = QAction("Preferences", self)
        
        edit_menu.addAction(undo_action)
        edit_menu.addAction(redo_action)
        edit_menu.addSeparator()
        edit_menu.addAction(preferences_action)
        
        # Connect preferences action
        preferences_action.triggered.connect(lambda: self.switch_module(5))
        
        # Help menu
        help_menu = self.menu_bar.addMenu("Help")
        
        about_action = QAction("About", self)
        help_action = QAction("Help", self)
        
        help_menu.addAction(help_action)
        help_menu.addAction(about_action)
        
        # Connect help actions
        about_action.triggered.connect(self.show_about)
        
    def switch_module(self, index):
        # Update buttons checked state
        for button in [self.btn_stacker, self.btn_desqueezer, self.btn_gif, 
                       self.btn_vid_avg, self.btn_vid_smov, self.btn_settings]:
            button.setChecked(False)
            
        # Check the active button
        if index == 0:
            self.btn_stacker.setChecked(True)
        elif index == 1:
            self.btn_desqueezer.setChecked(True)
        elif index == 2:
            self.btn_gif.setChecked(True)
        elif index == 3:
            self.btn_vid_avg.setChecked(True)
        elif index == 4:
            self.btn_vid_smov.setChecked(True)
        elif index == 5:
            self.btn_settings.setChecked(True)
            
        # Switch to the selected module
        self.content.setCurrentIndex(index)
        
    def show_about(self):
        """Show the about dialog."""
        about_text = (
            "<h2>SeanKD PhotoTools Suite</h2>"
            "<p>Version 1.0</p>"
            "<p>A collection of elegant programs for various photography uses</p>"
            "<p>Developed by Sean Doherty</p>"
            "<p>Application is designed for efficient photo and video processing.</p>"
        )
        QMessageBox.about(self, "About SeanKD PhotoTools", about_text)
        
    def closeEvent(self, event):
        """Handle the close event."""
        # Save settings before closing
        self.settings_manager.save_settings()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PhotoToolsApp()
    window.show()
    sys.exit(app.exec())
