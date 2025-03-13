import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QProgressBar, QFileDialog, QGroupBox,
                           QFrame, QSlider, QComboBox, QSpinBox, QDoubleSpinBox,
                           QSplitter, QListWidget, QListWidgetItem)
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt, pyqtSlot, QSize

import numpy as np
from PIL import Image, ImageQt

from utils.module_base import ModuleBase
from .desqueezer_core import PhotoDesqueezer

class DesqueezerModule(ModuleBase):
    """UI for the Photo Desqueezer module."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.module_name = "Photo Desqueezer"
        self.module_description = "Desqueeze anamorphic DNG files"
        
        # Init core processor
        self.desqueezer = PhotoDesqueezer(callback=self.handle_callback)
        
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
        
        self.select_files_btn = QPushButton("Select DNG Files")
        self.select_files_btn.clicked.connect(self.select_files)
        file_layout.addWidget(self.select_files_btn)
        
        self.select_folder_btn = QPushButton("Select Folder")
        self.select_folder_btn.clicked.connect(self.select_folder)
        file_layout.addWidget(self.select_folder_btn)
        
        self.file_list = QListWidget()
        self.file_list.setAlternatingRowColors(True)
        self.file_list.setMinimumHeight(150)
        file_layout.addWidget(self.file_list)
        
        self.file_count_label = QLabel("No files selected")
        file_layout.addWidget(self.file_count_label)
        
        left_layout.addWidget(file_group)
        
        # Desqueeze settings
        settings_group = QGroupBox("Desqueeze Settings")
        settings_layout = QVBoxLayout(settings_group)
        
        # Desqueeze factor
        factor_layout = QHBoxLayout()
        factor_layout.addWidget(QLabel("Desqueeze Factor:"))
        self.factor_spinbox = QDoubleSpinBox()
        self.factor_spinbox.setMinimum(1.1)
        self.factor_spinbox.setMaximum(3.0)
        self.factor_spinbox.setValue(1.6)
        self.factor_spinbox.setSingleStep(0.1)
        self.factor_spinbox.setDecimals(2)
        factor_layout.addWidget(self.factor_spinbox)
        settings_layout.addLayout(factor_layout)
        
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
        self.process_btn = QPushButton("Start Desqueezing")
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
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        status_layout.addWidget(self.progress_bar)
        
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
        
        # Before/After Preview
        preview_frame = QFrame()
        preview_frame.setStyleSheet("background-color: #1a1a1a; border: 1px solid #333333;")
        preview_frame.setMinimumSize(500, 400)
        
        preview_layout = QHBoxLayout(preview_frame)
        
        # Before image
        before_container = QWidget()
        before_layout = QVBoxLayout(before_container)
        before_layout.addWidget(QLabel("Before"))
        self.before_label = QLabel()
        self.before_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.before_label.setText("Original image will appear here")
        before_layout.addWidget(self.before_label)
        preview_layout.addWidget(before_container)
        
        # After image
        after_container = QWidget()
        after_layout = QVBoxLayout(after_container)
        after_layout.addWidget(QLabel("After"))
        self.after_label = QLabel()
        self.after_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.after_label.setText("Desqueezed image will appear here")
        after_layout.addWidget(self.after_label)
        preview_layout.addWidget(after_container)
        
        right_layout.addWidget(preview_frame)
        
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
        """Select DNG files for processing."""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Select DNG Files", "", "DNG Files (*.dng)"
        )
        
        if not file_paths:
            return
            
        self._update_file_list(file_paths)
    
    def select_folder(self):
        """Select a folder containing DNG files."""
        folder_path = QFileDialog.getExistingDirectory(
            self, "Select Folder with DNG Files"
        )
        
        if not folder_path:
            return
            
        # Find all DNG files in the folder
        file_paths = []
        for filename in os.listdir(folder_path):
            if filename.lower().endswith('.dng'):
                file_paths.append(os.path.join(folder_path, filename))
                
        if not file_paths:
            self.status_label.setText("No DNG files found in the selected folder.")
            return
            
        self._update_file_list(file_paths)
    
    def _update_file_list(self, file_paths):
        """Update the file list with the selected files."""
        # Clear existing items
        self.file_list.clear()
        
        # Add new items
        for file_path in file_paths:
            item = QListWidgetItem(os.path.basename(file_path))
            item.setToolTip(file_path)
            self.file_list.addItem(item)
            
        # Update file count label
        self.file_count_label.setText(f"{len(file_paths)} files selected")
        
        # Enable process button if files are selected
        self.process_btn.setEnabled(len(file_paths) > 0)
        
        # Show preview for the first file
        if file_paths:
            self._show_preview(file_paths[0])
    
    def _show_preview(self, file_path):
        """Show a preview of the original and desqueezed image."""
        try:
            # Load the image
            with rawpy.imread(file_path) as raw:
                rgb_image = raw.postprocess()
                
            # Create PIL image
            image = Image.fromarray(rgb_image)
            
            # Show original image
            original_pixmap = self._pil_to_pixmap(image)
            self.before_label.setPixmap(original_pixmap)
            
            # Calculate desqueezed dimensions
            desqueeze_factor = self.factor_spinbox.value()
            new_width = int(image.width * desqueeze_factor)
            
            # Create desqueezed image preview
            desqueezed_image = image.resize((new_width, image.height), Image.LANCZOS)
            desqueezed_pixmap = self._pil_to_pixmap(desqueezed_image)
            self.after_label.setPixmap(desqueezed_pixmap)
            
        except Exception as e:
            self.status_label.setText(f"Error loading preview: {e}")
            self.before_label.setText("Error loading preview")
            self.after_label.setText("Error loading preview")
    
    def _pil_to_pixmap(self, pil_image):
        """Convert a PIL image to a scaled QPixmap for display."""
        # Convert PIL image to QImage
        q_image = ImageQt.ImageQt(pil_image)
        pixmap = QPixmap.fromImage(q_image)
        
        # Scale to fit preview area
        preview_size = self.before_label.size()
        scaled_pixmap = pixmap.scaled(
            preview_size, 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        
        return scaled_pixmap
    
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
        desqueeze_factor = self.factor_spinbox.value()
        output_format = self.format_combo.currentText().lower()
        
        # Start processing
        success = self.desqueezer.start_batch_processing(file_paths, desqueeze_factor, output_format)
        
        if success:
            # Update UI state
            self.process_btn.setEnabled(False)
            self.cancel_btn.setEnabled(True)
            self.select_files_btn.setEnabled(False)
            self.select_folder_btn.setEnabled(False)
            self.progress_bar.setValue(0)
            
            # Clear output list
            self.output_list.clear()
            
            # Update status
            self.status_label.setText("Processing...")
    
    def cancel_processing(self):
        """Cancel the processing operation."""
        self.desqueezer.cancel()
        
        # Update UI state
        self.cancel_btn.setEnabled(False)
        self.status_label.setText("Cancelling...")
    
    def handle_callback(self, callback_type, data):
        """Handle callbacks from the desqueezer core."""
        if callback_type == "status":
            self.status_label.setText(str(data))
        elif callback_type == "progress":
            self.progress_bar.setValue(int(data))
        elif callback_type == "max_progress":
            self.progress_bar.setMaximum(int(data))
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
            self.select_folder_btn.setEnabled(True)
            
            # Enable open folder button if there are output files
            self.open_folder_btn.setEnabled(len(data) > 0)
            
            # Update status
            self.status_label.setText(f"Processing complete. {len(data)} files desqueezed.")
    
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
        self.progress_bar.setValue(0)
        
        # Reset status
        self.status_label.setText("Ready")
        
        # Reset preview
        self.before_label.setText("Original image will appear here")
        self.before_label.setPixmap(QPixmap())
        self.after_label.setText("Desqueezed image will appear here")
        self.after_label.setPixmap(QPixmap())
        
        # Reset UI state
        self.process_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.select_files_btn.setEnabled(True)
        self.select_folder_btn.setEnabled(True)
        self.open_folder_btn.setEnabled(False)
        
        return True
    
    def can_process(self):
        """Check if the module is ready to process."""
        return self.file_list.count() > 0
    
    def load_settings(self):
        """Load module-specific settings."""
        super().load_settings()
        
        if self.settings:
            # Load desqueeze factor
            desqueeze_factor = self.get_setting("desqueeze_factor", 1.6)
            self.factor_spinbox.setValue(desqueeze_factor)
            
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
            
        # Save desqueeze factor
        self.set_setting("desqueeze_factor", self.factor_spinbox.value())
        
        # Save output format
        self.set_setting("output_format", self.format_combo.currentText())
        
        return True
