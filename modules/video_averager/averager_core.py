import os
import threading
import numpy as np
import cv2
from PIL import Image

class VideoAverager:
    """Core functionality for averaging frames from video files."""
    
    def __init__(self, callback=None):
        self.callback = callback
        self.cancel_processing = False
        self.processing_thread = None
        self.output_files = []
    
    def average_frames(self, video_path, output_format="tiff", sample_rate=1.0):
        """Average all frames in a video file."""
        try:
            # Open the video file
            cap = cv2.VideoCapture(video_path)
            
            # Check if the video was opened successfully
            if not cap.isOpened():
                if self.callback:
                    self.callback("status", f"Error: Could not open video file {video_path}")
                return None
            
            # Get video properties
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            if self.callback:
                self.callback("status", f"Video info: {width}x{height}, {frame_count} frames, {fps} fps")
                self.callback("progress", 0)
                self.callback("max_progress", frame_count)
            
            # Initialize sum and count
            sum_frames = np.zeros((height, width, 3), dtype=np.float64)
            frame_number = 0
            processed_count = 0
            
            # Determine sampling interval based on sample rate
            # sample_rate of 1.0 means use every frame, 0.5 means use every other frame, etc.
            sampling_interval = max(1, int(1.0 / float(sample_rate)))
            
            # Process frames
            while True:
                if self.cancel_processing:
                    cap.release()
                    if self.callback:
                        self.callback("status", "Processing cancelled.")
                    return None
                
                # Read the next frame
                ret, frame = cap.read()
                
                # Break if we've reached the end of the video
                if not ret:
                    break
                
                # Only process frames based on the sampling interval
                if frame_number % sampling_interval == 0:
                    # Convert from BGR to RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    # Add to sum
                    sum_frames += frame_rgb.astype(np.float64)
                    processed_count += 1
                
                # Update progress
                if self.callback and frame_number % 10 == 0:  # Update every 10 frames to avoid UI lag
                    self.callback("progress", frame_number)
                    self.callback("status", f"Processed {frame_number} of {frame_count} frames")
                
                frame_number += 1
            
            # Release the video capture object
            cap.release()
            
            # Calculate average
            if processed_count > 0:
                avg_frame = sum_frames / processed_count
                avg_frame = np.clip(avg_frame, 0, 255).astype(np.uint8)
                
                # Create output filename
                output_file_path = self._get_output_path(video_path, output_format)
                
                # Save the average frame
                self._save_image(avg_frame, output_file_path, output_format)
                
                if self.callback:
                    self.callback("status", f"Averaged {processed_count} frames from {video_path}")
                    self.callback("progress", frame_count)
                    self.callback("preview", avg_frame)
                
                return output_file_path
            else:
                if self.callback:
                    self.callback("status", f"No frames were processed from {video_path}")
                return None
                
        except Exception as e:
            if self.callback:
                self.callback("status", f"Error processing {video_path}: {e}")
            return None
    
    def _get_output_path(self, input_path, output_format):
        """Generate the output file path."""
        # Get the directory and filename
        directory = os.path.dirname(input_path)
        filename = os.path.splitext(os.path.basename(input_path))[0]
        
        # Create the output directory if it doesn't exist
        output_dir = os.path.join(directory, 'Averaged_Frames')
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate the output file path
        output_path = os.path.join(output_dir, f"{filename}_average.{output_format.lower()}")
        
        return output_path
    
    def _save_image(self, image_array, output_path, output_format):
        """Save the image array to a file."""
        # Convert numpy array to PIL Image
        img = Image.fromarray(image_array)
        
        # Save the image in the specified format
        if output_format.lower() == "tiff":
            img.save(output_path, format='TIFF')
        elif output_format.lower() == "jpg" or output_format.lower() == "jpeg":
            img.save(output_path, format='JPEG', quality=95)
        elif output_format.lower() == "png":
            img.save(output_path, format='PNG')
        else:
            # Default to TIFF
            img.save(output_path, format='TIFF')
        
        return output_path
    
    def start_batch_processing(self, file_paths, output_format="tiff", sample_rate=1.0):
        """Start batch processing of multiple video files."""
        if self.processing_thread and self.processing_thread.is_alive():
            if self.callback:
                self.callback("status", "Processing is already running.")
            return False
            
        self.cancel_processing = False
        self.output_files = []
        
        self.processing_thread = threading.Thread(
            target=self._process_batch,
            args=(file_paths, output_format, sample_rate)
        )
        self.processing_thread.daemon = True
        self.processing_thread.start()
        
        return True
    
    def _process_batch(self, file_paths, output_format, sample_rate):
        """Process a batch of video files."""
        total_files = len(file_paths)
        
        if self.callback:
            self.callback("status", f"Processing {total_files} video files...")
            self.callback("file_progress", 0)
            self.callback("file_max_progress", total_files)
        
        for i, file_path in enumerate(file_paths):
            if self.cancel_processing:
                if self.callback:
                    self.callback("status", "Processing cancelled.")
                break
            
            if self.callback:
                self.callback("status", f"Processing file {i+1} of {total_files}: {os.path.basename(file_path)}")
                self.callback("file_progress", i)
            
            # Process the file
            output_file = self.average_frames(file_path, output_format, sample_rate)
            
            if output_file:
                self.output_files.append(output_file)
                if self.callback:
                    self.callback("output_file", output_file)
            
            if self.callback:
                self.callback("file_progress", i + 1)
        
        if self.callback:
            self.callback("status", f"Completed processing {len(self.output_files)} of {total_files} files.")
            self.callback("complete", self.output_files)
            
        return self.output_files
    
    def cancel(self):
        """Cancel the processing operation."""
        self.cancel_processing = True
        if self.callback:
            self.callback("status", "Cancelling processing...")
        return True
