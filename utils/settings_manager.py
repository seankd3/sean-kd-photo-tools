import os
import json

class SettingsManager:
    """Manages application settings and preferences."""
    
    def __init__(self):
        # Settings file path
        self.config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config")
        os.makedirs(self.config_dir, exist_ok=True)
        self.settings_file = os.path.join(self.config_dir, "settings.json")
        
        # Default settings
        self.default_settings = {
            "theme": "dark",
            "remember_workspace": True,
            "autosave_interval": 5,  # minutes
            "preview_quality": "high",
            "cpu_limit": 75,  # percentage
            "ram_limit": 2048,  # MB
            "recent_files": [],
            "export_format": "tiff",
            "export_quality": 95,
            "language": "en",
            "show_tooltips": True,
            "enable_gpu_acceleration": True,
            "custom_workspace": {},
            "modules": {
                "dng_stacker": {
                    "default_methods": ["Mean", "Maximum"],
                    "sigma_clip_value": 2.0
                },
                "photo_desqueezer": {
                    "desqueeze_factor": 1.6
                },
                "gif_creator": {
                    "default_fps": 24,
                    "loop_enabled": True
                },
                "video_averager": {
                    "default_format": "tiff"
                },
                "video_smover": {
                    "smoothing_factor": 0.5
                }
            }
        }
        
        # Current settings
        self.settings = self.load_settings()
    
    def load_settings(self):
        """Load settings from file, fall back to defaults if necessary."""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                    
                # Merge with default settings to ensure all keys exist
                settings = self.default_settings.copy()
                self._deep_update(settings, loaded_settings)
                return settings
            except Exception as e:
                print(f"Error loading settings: {e}")
                return self.default_settings.copy()
        else:
            # Create settings file with defaults
            self.save_settings(self.default_settings)
            return self.default_settings.copy()
    
    def _deep_update(self, target, source):
        """Recursively update nested dictionaries."""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_update(target[key], value)
            else:
                target[key] = value
    
    def save_settings(self, settings=None):
        """Save settings to file."""
        if settings is None:
            settings = self.settings
            
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def get(self, key, default=None):
        """Get a setting value by key."""
        # Support nested keys using dot notation
        if '.' in key:
            parts = key.split('.')
            value = self.settings
            for part in parts:
                if part in value:
                    value = value[part]
                else:
                    return default
            return value
        
        return self.settings.get(key, default)
    
    def set(self, key, value):
        """Set a setting value by key."""
        # Support nested keys using dot notation
        if '.' in key:
            parts = key.split('.')
            target = self.settings
            for part in parts[:-1]:
                if part not in target:
                    target[part] = {}
                target = target[part]
            target[parts[-1]] = value
        else:
            self.settings[key] = value
            
        # Save settings after each change
        self.save_settings()
        
        return True
    
    def reset_to_defaults(self):
        """Reset all settings to default values."""
        self.settings = self.default_settings.copy()
        self.save_settings()
        return True
    
    def add_recent_file(self, file_path):
        """Add a file to the recent files list."""
        if 'recent_files' not in self.settings:
            self.settings['recent_files'] = []
            
        # Remove if already exists (to move to top)
        if file_path in self.settings['recent_files']:
            self.settings['recent_files'].remove(file_path)
            
        # Add to the beginning of the list
        self.settings['recent_files'].insert(0, file_path)
        
        # Limit list size to 10 items
        self.settings['recent_files'] = self.settings['recent_files'][:10]
        
        self.save_settings()
        return True
