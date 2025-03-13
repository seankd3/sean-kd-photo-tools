import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QProgressBar, QFileDialog, QGroupBox,
                           QFrame, QSlider, QComboBox, QSpinBox, QDoubleSpinBox,
                           QSplitter, QListWidget, QListWidgetItem, QRadioButton)
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt, pyqtSlot, QSize, QUrl
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget

import numpy as np
from PIL import Image, ImageQt

from utils.module_base import ModuleBase
from .smover_core import VideoSmover

class VideoSmoverModule(ModuleBase):
    """UI for the Video Smover module."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.module_name = "Video Smover"
        self.module_description = "Create smooth motion videos with various effects"
        
        # Init core processor
        self.smover = VideoSmover(callback=self.handle_callback)
        
        # Setup UI
        self.init_ui()
        
        # Class variables
        self.input_video = None
        self.output_video = None
        self.media_player = None
        self.video_widget = None
    
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
        file_group = QGroupBox("Input Video")
        file_layout = QVBoxLayout(file_group)
        
        self.select_file_btn = QPushButton("Select Video File")
        self.select_file_btn.clicked.connect(self.select_file)
        file_layout.addWidget(self.select_file_btn)
        
        self.file_path_label = QLabel("No file selected")
        file_layout.addWidget(self.file_path_label)
        
        left_layout.addWidget(file_group)
        
        # Effect settings
        settings_group = QGroupBox("Effect Settings")
        settings_layout = QVBoxLayout(settings_group)
        
        # Effect type
        effect_type_layout = QHBoxLayout()
        effect_type_layout.addWidget(QLabel("Effect Type:"))
        self.effect_combo = QComboBox()
        self.effect_combo.addItems(["Motion Blur", "Timelapse", "Slow Motion"])
        self.effect_combo.setCurrentText("Motion Blur")
        effect_type_layout.addWidget(self.effect_combo)
        settings_layout.addLayout(effect_type_layout)
        
        # Intensity
        intensity_layout = QVBoxLayout()
        intensity_header = QHBoxLayout()
        intensity_header.addWidget(QLabel("Effect Intensity:"))
        self.intensity_value_label = QLabel("0.5")
        intensity_header.addWidget(self.intensity_value_label)
        intensity_layout.addLayout(intensity_header)
        
        self.intensity_slider = QSlider(Qt.Orientation.Horizontal)
        self.intensity_slider.setMinimum(1)
        self.intensity_slider.setMaximum(100)
        self.intensity_slider.setValue(50)
        self.intensity_slider.valueChanged.connect(self.update_intensity_label)
        intensity_layout.addWidget(self.intensity_slider)
        settings_layout.addLayout(intensity_layout)
        
        # Frame rate
        fps_layout = QHBoxLayout()
        fps_layout.addWidget(QLabel("Frame Rate (FPS):"))
        self.fps_spinbox = QSpinBox()
        self.fps_spinbox.setMinimum(5)
        self.fps_spinbox.setMaximum(60)
        self.fps_spinbox.setValue(30)
        fps_layout.addWidget(self.fps_spinbox)
        settings_layout.addLayout(fps_layout)
        
        # Duration
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel("Duration (seconds):"))
        self.duration_spinbox = QDoubleSpinBox()
        self.duration_spinbox.setMinimum(1.0)
        self.duration_spinbox.setMaximum(60.0)
        self.duration_spinbox.setValue(5.0)
        self.duration_spinbox.setSingleStep(0.5)
        self.duration_spinbox.setDecimals(1)
        duration_layout.addWidget(self.duration_spinbox)
        settings_layout.addLayout(duration_layout)
        
        # Output format
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Output Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["MP4", "AVI", "MOV"])
        self.format_combo.setCurrentText("MP4")
        format_layout.addWidget(self.format_combo)
        settings_layout.addLayout(format_layout)
        
        left_layout.addWidget(settings_group)
        
        # Output file selection
        output_group = QGroupBox("Output File")
        output_layout = QVBoxLayout(output_group)
        
        self.output_path_label = QLabel("Default: Same as input, in 'Smoved_Videos' folder")
        output_layout.addWidget(self.output_path_label)
        
        self.select_output_btn = QPushButton("Select Output Location")
        self.select_output_btn.clicked.connect(self.select_output)
        output_layout.addWidget(self.select_output_btn)
        
        left_layout.addWidget(output_group)
        
        # Process button
        self.process_btn = QPushButton("Create Video")
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
        
        # Video preview section
        video_group = QGroupBox("Video Preview")
        video_layout = QVBoxLayout(video_group)
        
        # Create a video widget for preview
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumSize(640, 360)
        video_layout.addWidget(self.video_widget)
        
        # Create media player
        self.media_player = QMediaPlayer()
        self.media_player.setVideoOutput(self.video_widget)
        
        # Video controls
        controls_layout = QHBoxLayout()
        
        self.play_btn = QPushButton("Play")
        self.play_btn.clicked.connect(self.play_video)
        self.play_btn.setEnabled(False)
        controls_layout.addWidget(self.play_btn)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_video)
        self.stop_btn.setEnabled(False)
        controls_layout.addWidget(self.stop_btn)
        
        # Preview selector
        self.input_preview_radio = QRadioButton("Input Video")
        self.input_preview_radio.setChecked(True)
        self.input_preview_radio.toggled.connect(self.update_preview)
        self.input_preview_radio.setEnabled(False)
        controls_layout.addWidget(self.input_preview_radio)
        
        self.output_preview_radio = QRadioButton("Output Video")
        self.output_preview_radio.toggled.connect(self.update_preview)
        self.output_preview_radio.setEnabled(False)
        controls_layout.addWidget(self.output_preview_radio)
        
        video_layout.addLayout(controls_layout)
        right_layout.addWidget(video_group)
        
        # Output actions
        output_actions = QHBoxLayout()
        
        self.open_video_btn = QPushButton("Open Video")
        self.open_video_btn.clicked.connect(self.open_output_file)
        self.open_video_btn.setEnabled(False)
        output_actions.addWidget(self.open_video_btn)
        
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
    
    def update_intensity_label(self, value):
        """Update the intensity label to show the current value."""
        intensity = value / 100.0
        self.intensity_value_label.setText(f"{intensity:.2f}")
    
    def select_file(self):
        """Select an input video file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Video File", "", "Video Files (*.mp4 *.avi *.mov *.mkv *.wmv)"
        )
        
        if not file_path:
            return
            
        self.input_video = file_path
        self.file_path_label.setText(os.path.basename(file_path))
        
        # Enable preview buttons
        self.play_btn.setEnabled(True)
        self.input_preview_radio.setEnabled(True)
        
        # Load the video into the media player
        self.media_player.setSource(QUrl.fromLocalFile(file_path))
        
        # Enable the process button
        self.process_btn.setEnabled(True)
        
        # Update preview
        self.update_preview()
    
    def select_output(self):
        """Select the output file location."""
        if not self.input_video:
            self.status_label.setText("Please select an input video first.")
            return
            
        # Get the default directory from the input video
        default_dir = os.path.dirname(self.input_video)
        filename = os.path.splitext(os.path.basename(self.input_video))[0]
        
        # Get selected format
        format_ext = self.format_combo.currentText().lower()
        
        output_path, _ = QFileDialog.getSaveFileName(
            self, "Select Output Video Location", 
            os.path.join(default_dir, f"{filename}_smoved.{format_ext}"),
            f"Video Files (*.{format_ext})"
        )
        
        if output_path:
            self.output_path = output_path
            self.output_path_label.setText(output_path)
    
    def play_video(self):
        """Play the selected video."""
        self.media_player.play()
        self.play_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
    
    def stop_video(self):
        """Stop the video playback."""
        self.media_player.stop()
        self.play_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
    
    def update_preview(self):
        """Update the video preview based on the selected radio button."""
        # Stop any current playback
        self.media_player.stop()
        self.play_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        # Set the appropriate video source
        if self.input_preview_radio.isChecked() and self.input_video:
            self.media_player.setSource(QUrl.fromLocalFile(self.input_video))
        elif self.output_preview_radio.isChecked() and hasattr(self, 'output_file') and self.output_file:
            self.media_player.setSource(QUrl.fromLocalFile(self.output_file))
    
    def start_processing(self):
        """Start processing the video."""
        if not self.input_video:
            self.status_label.setText("No input video selected.")
            return
            
        # Get settings
        effect_map = {
            "Motion Blur": "motion_blur",
            "Timelapse": "timelapse",
            "Slow Motion": "slow_motion"
        }
        effect_type = effect_map.get(self.effect_combo.currentText(), "motion_blur")
        intensity = self.intensity_slider.value() / 100.0
        frame_rate = self.fps_spinbox.value()
        duration = self.duration_spinbox.value()
        output_format = self.format_combo.currentText().lower()
        
        # Get output path
        output_path = getattr(self, 'output_path', None)
        
        # Start processing
        success = self.smover.start_processing(
            self.input_video, output_path, effect_type, intensity, frame_rate, duration, output_format
        )
        
        if success:
            # Update UI state
            self.process_btn.setEnabled(False)
            self.cancel_btn.setEnabled(True)
            self.select_file_btn.setEnabled(False)
            self.select_output_btn.setEnabled(False)
            self.progress_bar.setValue(0)
            
            # Update status
            self.status_label.setText(f"Creating {self.effect_combo.currentText()} video...")
    
    def cancel_processing(self):
        """Cancel the video processing."""
        self.smover.cancel()
        
        # Update UI state
        self.cancel_btn.setEnabled(False)
        self.status_label.setText("Cancelling...")
    
    def handle_callback(self, callback_type, data):
        """Handle callbacks from the smover core."""
        if callback_type == "status":
            self.status_label.setText(str(data))
        elif callback_type == "progress":
            self.progress_bar.setValue(int(data))
        elif callback_type == "max_progress":
            self.progress_bar.setMaximum(int(data))
        elif callback_type == "output_file":
            # Store the output path
            self.output_file = data
            
            # Enable the output preview radio button
            self.output_preview_radio.setEnabled(True)
            
            # Enable open buttons
            self.open_video_btn.setEnabled(True)
            self.open_folder_btn.setEnabled(True)
        elif callback_type == "complete":
            # Update UI state
            self.process_btn.setEnabled(True)
            self.cancel_btn.setEnabled(False)
            self.select_file_btn.setEnabled(True)
            self.select_output_btn.setEnabled(True)
            
            # Update status
            if len(data) > 0:
                self.status_label.setText(f"Video creation complete.")
    
    def open_output_file(self):
        """Open the created video file."""
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
        # Stop any playback
        if self.media_player:
            self.media_player.stop()
        
        # Clear video path
        self.input_video = None
        self.file_path_label.setText("No file selected")
        
        # Reset progress
        self.progress_bar.setValue(0)
        
        # Reset status
        self.status_label.setText("Ready")
        
        # Reset UI state
        self.process_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.select_file_btn.setEnabled(True)
        self.select_output_btn.setEnabled(False)
        self.play_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.input_preview_radio.setEnabled(False)
        self.output_preview_radio.setEnabled(False)
        self.open_video_btn.setEnabled(False)
        self.open_folder_btn.setEnabled(False)
        
        return True
    
    def can_process(self):
        """Check if the module is ready to process."""
        return self.input_video is not None
    
    def load_settings(self):
        """Load module-specific settings."""
        super().load_settings()
        
        if self.settings:
            # Load effect type
            effect_type = self.get_setting("effect_type", "Motion Blur")
            index = self.effect_combo.findText(effect_type, Qt.MatchFlag.MatchFixedString)
            if index >= 0:
                self.effect_combo.setCurrentIndex(index)
            
            # Load intensity
            intensity = self.get_setting("intensity", 0.5)
            self.intensity_slider.setValue(int(intensity * 100))
            
            # Load frame rate
            frame_rate = self.get_setting("frame_rate", 30)
            self.fps_spinbox.setValue(frame_rate)
            
            # Load duration
            duration = self.get_setting("duration", 5.0)
            self.duration_spinbox.setValue(duration)
            
            # Load output format
            output_format = self.get_setting("output_format", "MP4")
            index = self.format_combo.findText(output_format, Qt.MatchFlag.MatchFixedString)
            if index >= 0:
                self.format_combo.setCurrentIndex(index)
            
            return True
        
        return False
    
    def save_settings(self):
        """Save module-specific settings."""
        if not self.settings:
            return False
            
        # Save effect type
        self.set_setting("effect_type", self.effect_combo.currentText())
        
        # Save intensity
        self.set_setting("intensity", self.intensity_slider.value() / 100.0)
        
        # Save frame rate
        self.set_setting("frame_rate", self.fps_spinbox.value())
        
        # Save duration
        self.set_setting("duration", self.duration_spinbox.value())
        
        # Save output format
        self.set_setting("output_format", self.format_combo.currentText())
        
        return True
