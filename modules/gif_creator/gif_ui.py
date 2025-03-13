import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QProgressBar, QFileDialog, QGroupBox,
                           QFrame, QSlider, QComboBox, QSpinBox, QDoubleSpinBox,
                           QSplitter, QListWidget, QListWidgetItem, QCheckBox)
from PyQt6.QtGui import QPixmap, QImage, QMovie
from PyQt6.QtCore import Qt, pyqtSlot, QSize, QByteArray

import numpy as np
from PIL import Image, ImageQt

from utils.module_base import ModuleBase
from .gif_core import GIFCreator

class GIFCreatorModule(ModuleBase):
    """UI for the GIF Creator module."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.module_name = "GIF Creator"
        self.module_description = "Create animated GIFs from sequences of images"
        
        # Init core processor
        self.gif_creator = GIFCreator(callback=self.handle_callback)
        
        # Setup UI
        self.init_ui()
        
        # Class variables for tracking state
        self.selected_files = []
        self.movie = None
    
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
        
        self.select_files_btn = QPushButton("Select Image Files")
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
        
        # GIF settings
        settings_group = QGroupBox("GIF Settings")
        settings_layout = QVBoxLayout(settings_group)
        
        # FPS
        fps_layout = QHBoxLayout()
        fps_layout.addWidget(QLabel("Frames Per Second:"))
        self.fps_spinbox = QSpinBox()
        self.fps_spinbox.setMinimum(1)
        self.fps_spinbox.setMaximum(60)
        self.fps_spinbox.setValue(10)
        fps_layout.addWidget(self.fps_spinbox)
        settings_layout.addLayout(fps_layout)
        
        # Loop settings
        loop_layout = QHBoxLayout()
        loop_layout.addWidget(QLabel("Loop Count:"))
        self.loop_spinbox = QSpinBox()
        self.loop_spinbox.setMinimum(0)
        self.loop_spinbox.setMaximum(100)
        self.loop_spinbox.setValue(0)
        self.loop_spinbox.setSpecialValueText("Infinite")
        loop_layout.addWidget(self.loop_spinbox)
        settings_layout.addLayout(loop_layout)
        
        # Optimize checkbox
        self.optimize_checkbox = QCheckBox("Optimize GIF")
        self.optimize_checkbox.setChecked(True)
        settings_layout.addWidget(self.optimize_checkbox)
        
        # Quality
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("Quality:"))
        self.quality_spinbox = QSpinBox()
        self.quality_spinbox.setMinimum(1)
        self.quality_spinbox.setMaximum(100)
        self.quality_spinbox.setValue(85)
        quality_layout.addWidget(self.quality_spinbox)
        settings_layout.addLayout(quality_layout)
        
        # Resize factor
        resize_layout = QHBoxLayout()
        resize_layout.addWidget(QLabel("Resize Factor:"))
        self.resize_spinbox = QDoubleSpinBox()
        self.resize_spinbox.setMinimum(0.1)
        self.resize_spinbox.setMaximum(2.0)
        self.resize_spinbox.setValue(1.0)
        self.resize_spinbox.setSingleStep(0.1)
        self.resize_spinbox.setDecimals(1)
        resize_layout.addWidget(self.resize_spinbox)
        settings_layout.addLayout(resize_layout)
        
        left_layout.addWidget(settings_group)
        
        # Output file selection
        output_group = QGroupBox("Output File")
        output_layout = QVBoxLayout(output_group)
        
        self.output_path_label = QLabel("Default: First image directory")
        output_layout.addWidget(self.output_path_label)
        
        self.select_output_btn = QPushButton("Select Output Location")
        self.select_output_btn.clicked.connect(self.select_output)
        output_layout.addWidget(self.select_output_btn)
        
        left_layout.addWidget(output_group)
        
        # Process button
        self.process_btn = QPushButton("Create GIF")
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
        
        # Right panel: Preview
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
        self.preview_label = QLabel("GIF preview will appear here")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(self.preview_label)
        
        right_layout.addWidget(self.preview_frame)
        
        # Buttons for previewing first and last frames
        preview_controls = QHBoxLayout()
        
        self.first_frame_btn = QPushButton("View First Frame")
        self.first_frame_btn.clicked.connect(self.show_first_frame)
        self.first_frame_btn.setEnabled(False)
        preview_controls.addWidget(self.first_frame_btn)
        
        self.last_frame_btn = QPushButton("View Last Frame")
        self.last_frame_btn.clicked.connect(self.show_last_frame)
        self.last_frame_btn.setEnabled(False)
        preview_controls.addWidget(self.last_frame_btn)
        
        right_layout.addLayout(preview_controls)
        
        # Output actions
        output_actions = QHBoxLayout()
        
        self.open_gif_btn = QPushButton("Open GIF")
        self.open_gif_btn.clicked.connect(self.open_output_file)
        self.open_gif_btn.setEnabled(False)
        output_actions.addWidget(self.open_gif_btn)
        
        self.open_folder_btn = QPushButton("Open Output Folder")
        self.open_folder_btn.clicked.connect(self.open_output_folder)
        self.open_folder_btn.setEnabled(False)
        output_actions.addWidget(self.open_folder_btn)
        
        right_layout.addLayout(output_actions)
        
        # Add panels to splitter
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(right_panel)
        main_splitter.setSizes([300, 700])
        
        # Add splitter to main layout
        self.main_layout.addWidget(main_splitter)
    
    def select_files(self):
        """Select image files for creating a GIF."""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Image Files", "", "Image Files (*.png *.jpg *.jpeg *.tiff *.tif *.bmp)"
        )
        
        if not file_paths:
            return
            
        self.selected_files = sorted(file_paths)
        self._update_file_list()
    
    def select_folder(self):
        """Select a folder containing image files."""
        folder_path = QFileDialog.getExistingDirectory(
            self, "Select Folder with Image Files"
        )
        
        if not folder_path:
            return
            
        # Find all image files in the folder
        extensions = ['.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp']
        file_paths = []
        for filename in os.listdir(folder_path):
            if any(filename.lower().endswith(ext) for ext in extensions):
                file_paths.append(os.path.join(folder_path, filename))
                
        if not file_paths:
            self.status_label.setText("No image files found in the selected folder.")
            return
            
        self.selected_files = sorted(file_paths)
        self._update_file_list()
    
    def _update_file_list(self):
        """Update the file list with the selected files."""
        # Clear existing items
        self.file_list.clear()
        
        # Add new items
        for file_path in self.selected_files:
            item = QListWidgetItem(os.path.basename(file_path))
            item.setToolTip(file_path)
            self.file_list.addItem(item)
            
        # Update file count label
        self.file_count_label.setText(f"{len(self.selected_files)} files selected")
        
        # Enable process and preview buttons if files are selected
        has_files = len(self.selected_files) > 0
        self.process_btn.setEnabled(has_files)
        self.first_frame_btn.setEnabled(has_files)
        self.last_frame_btn.setEnabled(has_files)
        
        # Update the default output path
        if has_files:
            first_dir = os.path.dirname(self.selected_files[0])
            default_path = os.path.join(first_dir, "animated.gif")
            self.output_path_label.setText(default_path)
            self.output_path = default_path
            
            # Show preview of first frame
            self.show_first_frame()
    
    def select_output(self):
        """Select the output file location."""
        if not self.selected_files:
            self.status_label.setText("Please select input files first.")
            return
            
        # Get the default directory from the first image
        default_dir = os.path.dirname(self.selected_files[0])
        
        output_path, _ = QFileDialog.getSaveFileName(
            self, "Select Output GIF Location", 
            os.path.join(default_dir, "animated.gif"),
            "GIF Files (*.gif)"
        )
        
        if output_path:
            self.output_path = output_path
            self.output_path_label.setText(output_path)
    
    def show_first_frame(self):
        """Show the first frame in the preview."""
        if not self.selected_files:
            return
            
        try:
            self._show_frame(self.selected_files[0])
        except Exception as e:
            self.status_label.setText(f"Error loading preview: {e}")
    
    def show_last_frame(self):
        """Show the last frame in the preview."""
        if not self.selected_files:
            return
            
        try:
            self._show_frame(self.selected_files[-1])
        except Exception as e:
            self.status_label.setText(f"Error loading preview: {e}")
    
    def _show_frame(self, file_path):
        """Show a specific frame in the preview."""
        try:
            # Load the image
            img = Image.open(file_path)
            
            # Convert PIL image to QPixmap for display
            q_image = ImageQt.ImageQt(img)
            pixmap = QPixmap.fromImage(q_image)
            
            # Scale to fit preview area
            preview_size = self.preview_frame.size()
            scaled_pixmap = pixmap.scaled(
                preview_size, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            
            self.preview_label.setPixmap(scaled_pixmap)
            
        except Exception as e:
            self.status_label.setText(f"Error loading image: {e}")
    
    def show_gif_preview(self, gif_path):
        """Show the created GIF in the preview area."""
        try:
            # Clear any existing QMovie
            if self.movie:
                self.movie.stop()
                self.preview_label.clear()
            
            # Create a new QMovie
            self.movie = QMovie(gif_path)
            
            # Scale the movie to fit the preview area
            preview_size = self.preview_frame.size()
            self.movie.setScaledSize(QSize(
                preview_size.width() - 20,  # Subtract some padding
                preview_size.height() - 20
            ))
            
            # Set the movie on the label
            self.preview_label.setMovie(self.movie)
            
            # Start the animation
            self.movie.start()
            
        except Exception as e:
            self.status_label.setText(f"Error displaying GIF preview: {e}")
    
    def start_processing(self):
        """Start creating the GIF."""
        if not self.selected_files:
            self.status_label.setText("No files selected.")
            return
            
        # Get settings
        fps = self.fps_spinbox.value()
        loop = self.loop_spinbox.value()
        optimize = self.optimize_checkbox.isChecked()
        quality = self.quality_spinbox.value()
        resize_factor = self.resize_spinbox.value()
        
        # Get output path
        output_path = getattr(self, 'output_path', None)
        
        # Start processing
        success = self.gif_creator.start_processing(
            self.selected_files, output_path, fps, loop, optimize, quality, resize_factor
        )
        
        if success:
            # Update UI state
            self.process_btn.setEnabled(False)
            self.cancel_btn.setEnabled(True)
            self.select_files_btn.setEnabled(False)
            self.select_folder_btn.setEnabled(False)
            self.select_output_btn.setEnabled(False)
            self.progress_bar.setValue(0)
            
            # Update status
            self.status_label.setText("Creating GIF...")
    
    def cancel_processing(self):
        """Cancel the GIF creation."""
        self.gif_creator.cancel()
        
        # Update UI state
        self.cancel_btn.setEnabled(False)
        self.status_label.setText("Cancelling...")
    
    def handle_callback(self, callback_type, data):
        """Handle callbacks from the GIF creator core."""
        if callback_type == "status":
            self.status_label.setText(str(data))
        elif callback_type == "progress":
            self.progress_bar.setValue(int(data))
        elif callback_type == "max_progress":
            self.progress_bar.setMaximum(int(data))
        elif callback_type == "preview":
            # For PIL Image preview, convert and display
            if hasattr(data, 'convert'):  # Check if it's a PIL Image
                q_image = ImageQt.ImageQt(data)
                pixmap = QPixmap.fromImage(q_image)
                
                # Scale to fit preview area
                preview_size = self.preview_frame.size()
                scaled_pixmap = pixmap.scaled(
                    preview_size, 
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                )
                
                self.preview_label.setPixmap(scaled_pixmap)
        elif callback_type == "output_file":
            # Enable open buttons
            self.open_gif_btn.setEnabled(True)
            self.open_folder_btn.setEnabled(True)
            
            # Store the output path
            self.output_file = data
            
            # Show the GIF preview
            self.show_gif_preview(data)
        elif callback_type == "complete":
            # Update UI state
            self.process_btn.setEnabled(True)
            self.cancel_btn.setEnabled(False)
            self.select_files_btn.setEnabled(True)
            self.select_folder_btn.setEnabled(True)
            self.select_output_btn.setEnabled(True)
            
            # Update status
            if len(data) > 0:
                self.status_label.setText(f"GIF creation complete.")
            else:
                self.status_label.setText("GIF creation failed or was cancelled.")
    
    def open_output_file(self):
        """Open the created GIF file."""
        if hasattr(self, 'output_file') and self.output_file:
            file_path = self.output_file
            
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
        if hasattr(self, 'output_file') and self.output_file:
            folder_path = os.path.dirname(self.output_file)
            
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
        self.selected_files = []
        
        # Reset progress
        self.progress_bar.setValue(0)
        
        # Reset preview
        if self.movie:
            self.movie.stop()
        self.preview_label.clear()
        self.preview_label.setText("GIF preview will appear here")
        self.movie = None
        
        # Reset status
        self.status_label.setText("Ready")
        
        # Reset UI state
        self.process_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.select_files_btn.setEnabled(True)
        self.select_folder_btn.setEnabled(True)
        self.select_output_btn.setEnabled(False)
        self.open_gif_btn.setEnabled(False)
        self.open_folder_btn.setEnabled(False)
        self.first_frame_btn.setEnabled(False)
        self.last_frame_btn.setEnabled(False)
        
        return True
    
    def can_process(self):
        """Check if the module is ready to process."""
        return len(self.selected_files) > 0
    
    def load_settings(self):
        """Load module-specific settings."""
        super().load_settings()
        
        if self.settings:
            # Load FPS
            fps = self.get_setting("fps", 10)
            self.fps_spinbox.setValue(fps)
            
            # Load loop count
            loop = self.get_setting("loop", 0)
            self.loop_spinbox.setValue(loop)
            
            # Load optimize setting
            optimize = self.get_setting("optimize", True)
            self.optimize_checkbox.setChecked(optimize)
            
            # Load quality
            quality = self.get_setting("quality", 85)
            self.quality_spinbox.setValue(quality)
            
            # Load resize factor
            resize_factor = self.get_setting("resize_factor", 1.0)
            self.resize_spinbox.setValue(resize_factor)
            
            return True
        
        return False
    
    def save_settings(self):
        """Save module-specific settings."""
        if not self.settings:
            return False
            
        # Save FPS
        self.set_setting("fps", self.fps_spinbox.value())
        
        # Save loop count
        self.set_setting("loop", self.loop_spinbox.value())
        
        # Save optimize setting
        self.set_setting("optimize", self.optimize_checkbox.isChecked())
        
        # Save quality
        self.set_setting("quality", self.quality_spinbox.value())
        
        # Save resize factor
        self.set_setting("resize_factor", self.resize_spinbox.value())
        
        return True
