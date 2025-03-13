import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QProgressBar, QFileDialog, QGroupBox,
                           QFrame, QSlider, QComboBox, QDoubleSpinBox,
                           QSplitter, QListWidget, QListWidgetItem)
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt, pyqtSlot, QSize

import numpy as np
from PIL import Image, ImageQt

from utils.module_base import ModuleBase
from .averager_core import VideoAverager

class VideoAveragerModule(ModuleBase):
    """UI for the Video Averager module."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.module_name = "Video Averager"
        self.module_description = "Average frames from video files into a single image"
        
        # Init core processor
        self.averager = VideoAverager(callback=self.handle_callback)
        
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
        
        self.select_files_btn = QPushButton("Select Video Files")
        self.select_files_btn.clicked.connect(self.select_files)
        file_layout.addWidget(self.select_files_btn)
        
        self.file_list = QListWidget()
        self.file_list.setAlternatingRowColors(True)
        self.file_list.setMinimumHeight(150)
        file_layout.addWidget(self.file_list)
        
        self.file_count_label = QLabel("No files selected")
        file_layout.addWidget(self.file_count_label)
        
        left_layout.addWidget(file_group)
        
        # Averaging settings
        settings_group = QGroupBox("Averaging Settings")
        settings_layout = QVBoxLayout(settings_group)
        
        # Sampling rate
        sampling_layout = QHBoxLayout()
        sampling_layout.addWidget(QLabel("Sampling Rate:"))
        self.sampling_spinbox = QDoubleSpinBox()
        self.sampling_spinbox.setMinimum(0.01)
        self.sampling_spinbox.setMaximum(1.0)
        self.sampling_spinbox.setValue(1.0)
        self.sampling_spinbox.setSingleStep(0.1)
        self.sampling_spinbox.setDecimals(2)
        self.sampling_spinbox.setToolTip("1.0 = use all frames, 0.5 = use every other frame, etc.")
        sampling_layout.addWidget(self.sampling_spinbox)
        settings_layout.addLayout(sampling_layout)
        
        # Output format
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Output Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["TIFF", "JPEG", "PNG"])
        self.format_combo.setCurrentText("TIFF")
        format_layout.addWidget(self.format_combo)
        settings_layout.addLayout(format_layout)
        
        left_layout.addWidget(settings_group)
        
        # Process button
        self.process_btn = QPushButton("Start Averaging")
        self.process_btn.setMinimumHeight(40)
        self.process_btn.clicked.connect(self.start_processing)
        self.process_btn.setEnabled(False)
        left_layout.addWidget(self.process_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self.cancel_processing)
        left_layout.addWidget(self.cancel_btn)
        
        # Status
        status_frame = QFrame()
        status_layout = QVBoxLayout(status_frame)
        
        # File progress
        self.file_progress_bar = QProgressBar()
        self.file_progress_bar.setMinimum(0)
        self.file_progress_bar.setMaximum(100)
        self.file_progress_bar.setValue(0)
        status_layout.addWidget(QLabel("Overall Progress:"))
        status_layout.addWidget(self.file_progress_bar)
        
        # Frame progress
        self.frame_progress_bar = QProgressBar()
        self.frame_progress_bar.setMinimum(0)
        self.frame_progress_bar.setMaximum(100)
        self.frame_progress_bar.setValue(0)
        status_layout.addWidget(QLabel("Current File Progress:"))
        status_layout.addWidget(self.frame_progress_bar)
        
        self.status_label = QLabel("Ready")
        status_layout.addWidget(self.status_label)
        
        left_layout.addWidget(status_frame)
        
        # Right panel: Preview and output
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        preview_label = QLabel("Preview")
        preview_font = preview_label.font()
        preview_font.setBold(True)
        preview_label.setFont(preview_font)
        right_layout.addWidget(preview_label)
        
        # Preview frame
        self.preview_frame = QFrame()
        self.preview_frame.setStyleSheet("background-color: #1a1a1a; border: 1px solid #333333;")
        self.preview_frame.setMinimumSize(500, 400)
        
        preview_layout = QVBoxLayout(self.preview_frame)
        self.preview_label = QLabel("Averaged image will appear here")
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
        
        # Open output folder button
        self.open_folder_btn = QPushButton("Open Output Folder")
        self.open_folder_btn.clicked.connect(self.open_output_folder)
        self.open_folder_btn.setEnabled(False)
        output_layout.addWidget(self.open_folder_btn)
        
        right_layout.addWidget(output_group)
        
        # Add panels to splitter
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(right_panel)
        main_splitter.setSizes([300, 700])
        
        # Add splitter to main layout
        self.main_layout.addWidget(main_splitter)
    
    def select_files(self):
        """Select video files for processing."""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Video Files", "", "Video Files (*.mp4 *.avi *.mov *.mkv *.wmv)"
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
        
        # Enable process button if files are selected
        self.process_btn.setEnabled(len(file_paths) > 0)
    
    def start_processing(self):
        """Start processing the selected files."""
        # Get selected files
        file_paths = []
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            file_paths.append(item.toolTip())
            
        if not file_paths:
            self.status_label.setText("No files selected.")
            return
            
        # Get settings
        sample_rate = self.sampling_spinbox.value()
        output_format = self.format_combo.currentText().lower()
        
        # Start processing
        success = self.averager.start_batch_processing(file_paths, output_format, sample_rate)
        
        if success:
            # Update UI state
            self.process_btn.setEnabled(False)
            self.cancel_btn.setEnabled(True)
            self.select_files_btn.setEnabled(False)
            self.file_progress_bar.setValue(0)
            self.frame_progress_bar.setValue(0)
            
            # Clear output list
            self.output_list.clear()
            
            # Update status
            self.status_label.setText("Processing...")
    
    def cancel_processing(self):
        """Cancel the processing operation."""
        self.averager.cancel()
        
        # Update UI state
        self.cancel_btn.setEnabled(False)
        self.status_label.setText("Cancelling...")
    
    def handle_callback(self, callback_type, data):
        """Handle callbacks from the averager core."""
        if callback_type == "status":
            self.status_label.setText(str(data))
        elif callback_type == "progress":
            self.frame_progress_bar.setValue(int(data))
        elif callback_type == "max_progress":
            self.frame_progress_bar.setMaximum(int(data))
        elif callback_type == "file_progress":
            self.file_progress_bar.setValue(int(data))
        elif callback_type == "file_max_progress":
            self.file_progress_bar.setMaximum(int(data))
        elif callback_type == "preview":
            self.update_preview(data)
        elif callback_type == "output_file":
            # Add output file to list
            item = QListWidgetItem(os.path.basename(data))
            item.setToolTip(data)
            self.output_list.addItem(item)
            self.open_folder_btn.setEnabled(True)
        elif callback_type == "complete":
            # Update UI state
            self.process_btn.setEnabled(True)
            self.cancel_btn.setEnabled(False)
            self.select_files_btn.setEnabled(True)
            
            # Enable open folder button if there are output files
            self.open_folder_btn.setEnabled(len(data) > 0)
            
            # Update status
            self.status_label.setText(f"Processing complete. {len(data)} files processed.")
    
    def update_preview(self, image_array):
        """Update the preview image."""
        if image_array is None:
            self.preview_label.setText("No preview available")
            return
            
        # Convert numpy array to QImage
        height, width, channels = image_array.shape
        bytes_per_line = channels * width
        
        q_img = QImage(image_array.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        
        # Scale to fit preview area while maintaining aspect ratio
        preview_size = self.preview_frame.size()
        scaled_pixmap = pixmap.scaled(
            preview_size, 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        
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
    
    def open_output_folder(self):
        """Open the output folder."""
        if self.output_list.count() > 0:
            item = self.output_list.item(0)
            file_path = item.toolTip()
            folder_path = os.path.dirname(file_path)
            
            try:
                import os
                if os.name == 'nt':  # Windows
                    os.startfile(folder_path)
                elif os.name == 'posix':  # macOS, Linux
                    import subprocess
                    subprocess.call(('xdg-open', folder_path))
            except Exception as e:
                self.status_label.setText(f"Error opening folder: {e}")
    
    def reset(self):
        """Reset the module to its initial state."""
        # Clear file list
        self.file_list.clear()
        self.file_count_label.setText("No files selected")
        
        # Clear output list
        self.output_list.clear()
        
        # Reset progress
        self.file_progress_bar.setValue(0)
        self.frame_progress_bar.setValue(0)
        
        # Reset status
        self.status_label.setText("Ready")
        
        # Reset preview
        self.preview_label.setText("Averaged image will appear here")
        self.preview_label.setPixmap(QPixmap())
        
        # Reset UI state
        self.process_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.select_files_btn.setEnabled(True)
        self.open_folder_btn.setEnabled(False)
        
        return True
    
    def can_process(self):
        """Check if the module is ready to process."""
        return self.file_list.count() > 0
    
    def load_settings(self):
        """Load module-specific settings."""
        super().load_settings()
        
        if self.settings:
            # Load sampling rate
            sampling_rate = self.get_setting("sampling_rate", 1.0)
            self.sampling_spinbox.setValue(sampling_rate)
            
            # Load output format
            output_format = self.get_setting("output_format", "TIFF")
            index = self.format_combo.findText(output_format, Qt.MatchFlag.MatchFixedString)
            if index >= 0:
                self.format_combo.setCurrentIndex(index)
            
            return True
        
        return False
    
    def save_settings(self):
        """Save module-specific settings."""
        if not self.settings:
            return False
            
        # Save sampling rate
        self.set_setting("sampling_rate", self.sampling_spinbox.value())
        
        # Save output format
        self.set_setting("output_format", self.format_combo.currentText())
        
        return True
