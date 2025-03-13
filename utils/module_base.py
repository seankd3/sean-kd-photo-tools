from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import pyqtSignal

class ModuleBase(QWidget):
    """Base class for all module UIs with common functionality."""
    
    # Signal to update status in main app
    status_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("module_container")
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Common module settings
        self.module_name = "Base Module"
        self.module_description = "Base module description"
        self.settings = None
        
    def init_ui(self):
        """Initialize the UI components."""
        pass
        
    def load_settings(self):
        """Load module-specific settings."""
        if self.parent() and hasattr(self.parent(), 'settings_manager'):
            self.settings = self.parent().settings_manager
            return True
        return False
    
    def save_settings(self):
        """Save module-specific settings."""
        if self.settings:
            return True
        return False
    
    def get_setting(self, key, default=None):
        """Get a module-specific setting."""
        if self.settings:
            module_key = f"modules.{self.module_name.lower().replace(' ', '_')}.{key}"
            return self.settings.get(module_key, default)
        return default
    
    def set_setting(self, key, value):
        """Set a module-specific setting."""
        if self.settings:
            module_key = f"modules.{self.module_name.lower().replace(' ', '_')}.{key}"
            return self.settings.set(module_key, value)
        return False
    
    def update_status(self, message):
        """Update status message."""
        self.status_changed.emit(message)
    
    def reset(self):
        """Reset module to initial state."""
        pass
    
    def can_process(self):
        """Check if module is ready to process."""
        return False
        
    def process(self):
        """Process the data."""
        pass
