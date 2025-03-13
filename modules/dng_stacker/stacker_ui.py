import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QCheckBox, QProgressBar, QFileDialog, 
                           QScrollArea, QFrame, QSlider, QSpinBox, QGroupBox,
                           QSplitter, QListWidget, QListWidgetItem)
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt, pyqtSlot, QSize

import numpy as np
from PIL import Image, ImageQt

from utils.module_base import ModuleBase
from .stacker_core import DNGStacker

class DNGStackerModule(ModuleBase):
    """UI for the DNG Stacker module."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.module_name = "DNG Stacker"
        self.module_description = "Stack multiple DNG files using various methods"
        
        # Init core processor
        self.stacker = DNGStacker(callback=self.handle_callback)
        
        # Setup UI
        self.init_ui()
    
    def init_ui(self):
        # Main layout is already set in ModuleBase
        
        # Top section: Title and description
        title_label = QLabel(self.module_name)
        title_label.setObjectName("module_title")
        title_font = title_label.font()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        
        desc_label = QLabel(self.module_description)
        desc_label.setObjectName("module_description")
        
        self.main_layout.addWidget(title_label)
        self.main_layout.addWidget(desc_label)
        self.main_layout.addSpacing(20)
        
        # Create a splitter for the main content
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel: Controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # File selection
        file_group = QGroupBox("Input Files")
        file_layout = QVBoxLayout(file_group)
        
        self.select_btn = QPushButton("Select DNG Files")
        self.select_btn.clicked.connect(self.select_files)
        file_layout.addWidget(self.select_btn)
        
        self.file_list = QListWidget()
        self.file_list.setAlternatingRowColors(True)
        self.file_list.setMinimumHeight(150)
        file_layout.addWidget(self.file_list)
        
        self.file_count_label = QLabel("No files selected")
        file_layout.addWidget(self.file_count_label)
        
        left_layout.addWidget(file_group)
        
        # Stacking methods
        method_group = QGroupBox("Stacking Methods")
        method_layout = QVBoxLayout(method_group)
        
        self.mean_cb = QCheckBox("Mean (Average)")
        self.mean_cb.setChecked(True)
        method_layout.addWidget(self.mean_cb)
        
        self.max_cb = QCheckBox("Maximum")
        self.max_cb.setChecked(True)
        method_layout.addWidget(self.max_cb)
        
        self.min_cb = QCheckBox("Minimum")
        method_layout.addWidget(self.min_cb)
        
        self.sigma_cb = QCheckBox("Sigma Clipping")
        method_layout.addWidget(self.sigma_cb)
        
        left_layout.addWidget(method_group)
        
        # Resource limits
        resource_group = QGroupBox("Resource Limits")
        resource_layout = QVBoxLayout(resource_group)
        
        cpu_layout = QHBoxLayout()
        cpu_layout.addWidget(QLabel("CPU Limit:"))
        self.cpu_slider = QSlider(Qt.Orientation.Horizontal)
        self.cpu_slider.setMinimum(10)
        self.cpu_slider.setMaximum(100)
        self.cpu_slider.setValue(75)
        self.cpu_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.cpu_slider.setTickInterval(10)
        cpu_layout.addWidget(self.cpu_slider)
        self.cpu_value = QLabel("75%")
        self.cpu_slider.valueChanged.connect(lambda v: self.cpu_value.setText(f"{v}%"))
        cpu_layout.addWidget(self.cpu_value)
        resource_layout.addLayout(cpu_layout)
        
        ram_layout = QHBoxLayout()
        ram_layout.addWidget(QLabel("RAM Limit (MB):"))
        self.ram_spinbox = QSpinBox()
        self.ram_spinbox.setMinimum(512)
        self.ram_spinbox.setMaximum(32768)
        self.ram_spinbox.setValue(2048)
        self.ram_spinbox.setSingleStep(512)
        ram_layout.addWidget(self.ram_spinbox)
        resource_layout.addLayout(ram_layout)
        
        left_layout.addWidget(resource_group)
        
        # Process button
        self.process_btn = QPushButton("Start Stacking")
        self.process_btn.setMinimumHeight(40)
        self.process_btn.clicked.connect(self.start_processing)
        left_layout.addWidget(self.process_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self.cancel_processing)
        left_layout.addWidget(self.cancel_btn)
        
        # Status
        status_frame = QFrame()
        status_layout = QVBoxLayout(status_frame)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        status_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready")
        status_layout.addWidget(self.status_label)
        
        self.details_label = QLabel("")
        self.details_label.setWordWrap(True)
        status_layout.addWidget(self.details_label)
        
        left_layout.addWidget(status_frame)
        
        # Right panel: Preview
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        preview_label = QLabel("Preview")
        preview_font = preview_label.font()
        preview_font.setBold(True)
        preview_label.setFont(preview_font)
        right_layout.addWidget(preview_label)
        
        # Image preview
        self.preview_frame = QFrame()
        self.preview_frame.setStyleSheet("background-color: #1a1a1a; border: 1px solid #333333;")
        self.preview_frame.setMinimumSize(500, 400)
        
        preview_layout = QVBoxLayout(self.preview_frame)
        self.preview_label = QLabel("No image preview available")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(self.preview_label)
        
        right_layout.addWidget(self.preview_frame)
        
        # Output files list
        output_group = QGroupBox("Output Files")
        output_layout = QVBoxLayout(output_group)
        
        self.output_list = QListWidget()
        self.output_list.setAlternatingRowColors(True)
        self.output_list.setMinimumHeight(150)
        self.output_list.itemDoubleClicked.connect(self.open_output_file)
        output_layout.addWidget(self.output_list)
        
        right_layout.addWidget(output_group)
        
        # Add panels to splitter
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(right_panel)
        main_splitter.setSizes([300, 700])
        
        # Add splitter to main layout
        self.main_layout.addWidget(main_splitter)
    
    def select_files(self):
        """Select DNG files for processing."""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Select DNG Files", "", "DNG Files (*.dng)"
        )
        
        if not file_paths:
            return
            
        # Update file list
        self.file_list.clear()
        for file_path in file_paths:
            item = QListWidgetItem(os.path.basename(file_path))
            item.setToolTip(file_path)
            self.file_list.addItem(item)
            
        # Update file count label
        self.file_count_label.setText(f"{len(file_paths)} files selected")
        
        # Set files in stacker
        self.stacker.set_file_paths(file_paths)
        
        # Update UI state
        self.process_btn.setEnabled(len(file_paths) > 0)
    
    def start_processing(self):
        """Start processing the selected files."""
        # Get selected methods
        selected_methods = []
        if self.mean_cb.isChecked():
            selected_methods.append("Mean")
        if self.max_cb.isChecked():
            selected_methods.append("Maximum")
        if self.min_cb.isChecked():
            selected_methods.append("Minimum")
        if self.sigma_cb.isChecked():
            selected_methods.append("Sigma Clipping")
            
        if not selected_methods:
            self.status_label.setText("No stacking methods selected")
            return
            
        # Get resource limits
        cpu_limit = self.cpu_slider.value()
        ram_limit = self.ram_spinbox.value()
        
        # Start processing
        success = self.stacker.start_processing(selected_methods, cpu_limit, ram_limit)
        
        if success:
            # Update UI state
            self.process_btn.setEnabled(False)
            self.cancel_btn.setEnabled(True)
            self.select_btn.setEnabled(False)
            self.progress_bar.setValue(0)
            
            # Clear output list
            self.output_list.clear()
            
            # Update status
            self.status_label.setText("Processing...")
    
    def cancel_processing(self):
        """Cancel the processing operation."""
        self.stacker.cancel()
        
        # Update UI state
        self.cancel_btn.setEnabled(False)
        self.status_label.setText("Cancelling...")
    
    def handle_callback(self, callback_type, data):
        """Handle callbacks from the stacker core."""
        if callback_type == "status":
            self.status_label.setText(str(data))
        elif callback_type == "progress":
            self.progress_bar.setValue(int(data))
        elif callback_type == "max_progress":
            self.progress_bar.setMaximum(int(data))
        elif callback_type == "details":
            self.details_label.setText(str(data))
        elif callback_type == "preview":
            self.update_preview(data)
        elif callback_type == "complete":
            # Update UI state
            self.process_btn.setEnabled(True)
            self.cancel_btn.setEnabled(False)
            self.select_btn.setEnabled(True)
            
            # Add output files to list
            for file_path in data:
                item = QListWidgetItem(os.path.basename(file_path))
                item.setToolTip(file_path)
                self.output_list.addItem(item)
                
            # Update status
            self.status_label.setText("Processing complete")
            
        elif callback_type == "output_file":
            # Add single output file to list
            item = QListWidgetItem(os.path.basename(data))
            item.setToolTip(data)
            self.output_list.addItem(item)
            
    def update_preview(self, image_array):
        """Update the preview image."""
        if image_array is None:
            self.preview_label.setText("No preview available")
            return
            
        # Convert numpy array to QImage
        height, width, channels = image_array.shape
        bytes_per_line = channels * width
        
        # Convert to 8-bit for display
        image_array = np.clip(image_array, 0, 255).astype(np.uint8)
        
        q_img = QImage(image_array.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        
        # Scale to fit preview area while maintaining aspect ratio
        preview_size = self.preview_frame.size()
        scaled_pixmap = pixmap.scaled(preview_size, 
                                     Qt.AspectRatioMode.KeepAspectRatio, 
                                     Qt.TransformationMode.SmoothTransformation)
        
        self.preview_label.setPixmap(scaled_pixmap)
    
    def open_output_file(self, item):
        """Open the selected output file."""
        file_path = item.toolTip()
        
        # Use system's default application to open the file
        try:
            import os
            if os.name == 'nt':  # Windows
                os.startfile(file_path)
            elif os.name == 'posix':  # macOS, Linux
                import subprocess
                subprocess.call(('xdg-open', file_path))
        except Exception as e:
            self.status_label.setText(f"Error opening file: {e}")
    
    def reset(self):
        """Reset the module to its initial state."""
        # Clear file list
        self.file_list.clear()
        self.file_count_label.setText("No files selected")
        
        # Clear output list
        self.output_list.clear()
        
        # Reset progress
        self.progress_bar.setValue(0)
        
        # Reset status
        self.status_label.setText("Ready")
        self.details_label.setText("")
        
        # Reset preview
        self.preview_label.setText("No image preview available")
        self.preview_label.setPixmap(QPixmap())
        
        # Reset UI state
        self.process_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.select_btn.setEnabled(True)
        
        return True
    
    def can_process(self):
        """Check if the module is ready to process."""
        return (self.file_list.count() > 0 and 
                (self.mean_cb.isChecked() or 
                 self.max_cb.isChecked() or 
                 self.min_cb.isChecked() or 
                 self.sigma_cb.isChecked()))
    
    def load_settings(self):
        """Load module-specific settings."""
        super().load_settings()
        
        if self.settings:
            # Load stacking methods
            default_methods = self.get_setting("default_methods", ["Mean", "Maximum"])
            
            self.mean_cb.setChecked("Mean" in default_methods)
            self.max_cb.setChecked("Maximum" in default_methods)
            self.min_cb.setChecked("Minimum" in default_methods)
            self.sigma_cb.setChecked("Sigma Clipping" in default_methods)
            
            # Load resource limits
            cpu_limit = self.get_setting("cpu_limit", 75)
            self.cpu_slider.setValue(cpu_limit)
            
            ram_limit = self.get_setting("ram_limit", 2048)
            self.ram_spinbox.setValue(ram_limit)
            
            return True
        
        return False
    
    def save_settings(self):
        """Save module-specific settings."""
        if not self.settings:
            return False
            
        # Save stacking methods
        selected_methods = []
        if self.mean_cb.isChecked():
            selected_methods.append("Mean")
        if self.max_cb.isChecked():
            selected_methods.append("Maximum")
        if self.min_cb.isChecked():
            selected_methods.append("Minimum")
        if self.sigma_cb.isChecked():
            selected_methods.append("Sigma Clipping")
            
        self.set_setting("default_methods", selected_methods)
        
        # Save resource limits
        self.set_setting("cpu_limit", self.cpu_slider.value())
        self.set_setting("ram_limit", self.ram_spinbox.value())
        
        return True
