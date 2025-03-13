import os
import threading
import numpy as np
import cv2
from PIL import Image

class VideoSmover:
    """Core functionality for creating smooth motion video effects."""
    
    def __init__(self, callback=None):
        self.callback = callback
        self.cancel_processing = False
        self.processing_thread = None
        self.output_files = []
    
    def create_smooth_motion(self, video_path, output_path=None, 
                            effect_type="motion_blur", intensity=0.5, 
                            frame_rate=30, duration=5.0, output_format="mp4"):
        """Create a smooth motion effect video."""
        try:
            # Open the video file
            cap = cv2.VideoCapture(video_path)
            
            # Check if the video was opened successfully
            if not cap.isOpened():
                if self.callback:
                    self.callback("status", f"Error: Could not open video file {video_path}")
                return None
            
            # Get video properties
            original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            original_fps = cap.get(cv2.CAP_PROP_FPS)
            original_frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Calculate output dimensions
            width = original_width
            height = original_height
            
            # Create default output path if none provided
            if not output_path:
                directory = os.path.dirname(video_path)
                filename = os.path.splitext(os.path.basename(video_path))[0]
                output_dir = os.path.join(directory, 'Smoved_Videos')
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, f"{filename}_smoved.{output_format}")
            
            # Calculate total frames for the output video
            total_frames = int(frame_rate * duration)
            
            # Initialize video writer
            fourcc = cv2.VideoWriter_fourcc(*self._get_fourcc(output_format))
            out = cv2.VideoWriter(output_path, fourcc, frame_rate, (width, height))
            
            if self.callback:
                self.callback("status", f"Creating smooth motion video: {effect_type}, {total_frames} frames")
                self.callback("progress", 0)
                self.callback("max_progress", total_frames)
            
            # Process based on effect type
            if effect_type == "motion_blur":
                result = self._create_motion_blur(cap, out, total_frames, intensity, original_frame_count)
            elif effect_type == "timelapse":
                result = self._create_timelapse(cap, out, total_frames, intensity, original_frame_count)
            elif effect_type == "slow_motion":
                result = self._create_slow_motion(cap, out, total_frames, intensity, original_frame_count)
            else:
                if self.callback:
                    self.callback("status", f"Unknown effect type: {effect_type}")
                cap.release()
                out.release()
                return None
            
            # Release resources
            cap.release()
            out.release()
            
            if result and os.path.exists(output_path):
                if self.callback:
                    self.callback("status", f"Video created: {output_path}")
                    self.callback("output_file", output_path)
                return output_path
            else:
                if self.callback:
                    self.callback("status", "Failed to create video")
                return None
                
        except Exception as e:
            if self.callback:
                self.callback("status", f"Error creating video: {e}")
            return None
    
    def _get_fourcc(self, format_name):
        """Get the appropriate fourcc code for the output format."""
        format_name = format_name.lower()
        if format_name == "mp4":
            return "mp4v"  # or "avc1" for H.264
        elif format_name == "avi":
            return "XVID"
        elif format_name == "mov":
            return "mp4v"
        else:
            return "mp4v"  # default
    
    def _create_motion_blur(self, cap, out, total_frames, intensity, original_frame_count):
        """Create a motion blur effect."""
        # Motion blur parameters
        blend_frames = max(2, int(10 * intensity))  # Number of frames to blend
        
        # Calculate frame step
        frame_step = max(1, original_frame_count / total_frames)
        
        # Initialize frame buffer
        frame_buffer = []
        
        # Process frames
        current_frame = 0
        output_frame_count = 0
        
        while output_frame_count < total_frames:
            if self.cancel_processing:
                if self.callback:
                    self.callback("status", "Processing cancelled.")
                return False
            
            # Determine which frame to read next
            frame_position = int(current_frame * frame_step) % original_frame_count
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_position)
            
            # Read frame
            ret, frame = cap.read()
            if not ret:
                break
            
            # Convert to float for blending
            frame_float = frame.astype(np.float32)
            
            # Add to buffer
            frame_buffer.append(frame_float)
            
            # Keep buffer at desired length
            if len(frame_buffer) > blend_frames:
                frame_buffer.pop(0)
            
            # If we have enough frames in buffer, create blended frame
            if len(frame_buffer) == blend_frames:
                # Blend frames
                blended_frame = np.zeros_like(frame_buffer[0])
                for f in frame_buffer:
                    blended_frame += f
                blended_frame /= len(frame_buffer)
                
                # Convert back to uint8
                blended_frame = blended_frame.astype(np.uint8)
                
                # Write to output
                out.write(blended_frame)
                output_frame_count += 1
                
                # Update progress
                if self.callback and output_frame_count % 10 == 0:
                    self.callback("progress", output_frame_count)
                    self.callback("status", f"Processed {output_frame_count} of {total_frames} frames")
            
            current_frame += 1
        
        if self.callback:
            self.callback("progress", total_frames)
            self.callback("status", f"Motion blur effect completed with {output_frame_count} frames")
        
        return output_frame_count > 0
    
    def _create_timelapse(self, cap, out, total_frames, intensity, original_frame_count):
        """Create a timelapse effect."""
        # Calculate frame step
        frame_step = max(1, original_frame_count / total_frames)
        
        # Process frames
        output_frame_count = 0
        
        for i in range(total_frames):
            if self.cancel_processing:
                if self.callback:
                    self.callback("status", "Processing cancelled.")
                return False
            
            # Calculate which frame to use
            frame_position = int(i * frame_step)
            if frame_position >= original_frame_count:
                break
            
            # Set position and read frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_position)
            ret, frame = cap.read()
            
            if not ret:
                break
            
            # Apply optional sharpening based on intensity
            if intensity > 0.5:
                kernel = np.array([[-1, -1, -1],
                                   [-1, 9, -1],
                                   [-1, -1, -1]])
                frame = cv2.filter2D(frame, -1, kernel * intensity)
            
            # Write to output
            out.write(frame)
            output_frame_count += 1
            
            # Update progress
            if self.callback:
                self.callback("progress", output_frame_count)
                if output_frame_count % 10 == 0:
                    self.callback("status", f"Processed {output_frame_count} of {total_frames} frames")
        
        if self.callback:
            self.callback("progress", total_frames)
            self.callback("status", f"Timelapse effect completed with {output_frame_count} frames")
        
        return output_frame_count > 0
    
    def _create_slow_motion(self, cap, out, total_frames, intensity, original_frame_count):
        """Create a slow motion effect with frame interpolation."""
        # Calculate how many original frames to use
        frames_to_use = min(original_frame_count, int(total_frames / (1 + intensity)))
        
        # How many interpolated frames to insert between each original frame
        interp_frames = max(1, int(intensity * 5))
        
        if self.callback:
            self.callback("status", f"Creating slow motion with {interp_frames} interpolated frames")
        
        # Read first frame
        ret, prev_frame = cap.read()
        if not ret:
            return False
        
        output_frame_count = 0
        
        # Process frames
        for i in range(1, frames_to_use):
            if self.cancel_processing:
                if self.callback:
                    self.callback("status", "Processing cancelled.")
                return False
            
            # Read next frame
            ret, next_frame = cap.read()
            if not ret:
                break
            
            # Write the previous frame
            out.write(prev_frame)
            output_frame_count += 1
            
            # Create and write interpolated frames
            for j in range(interp_frames):
                if output_frame_count >= total_frames:
                    break
                    
                # Calculate blend factor
                alpha = (j + 1) / (interp_frames + 1)
                
                # Blend frames
                interpolated = cv2.addWeighted(prev_frame, 1 - alpha, next_frame, alpha, 0)
                
                # Write interpolated frame
                out.write(interpolated)
                output_frame_count += 1
            
            # Update progress
            if self.callback and i % 5 == 0:
                self.callback("progress", min(output_frame_count, total_frames))
                self.callback("status", f"Processed {output_frame_count} of {total_frames} frames")
            
            # Move to next frame
            prev_frame = next_frame
            
            if output_frame_count >= total_frames:
                break
        
        # Write the last frame if needed
        if output_frame_count < total_frames:
            out.write(prev_frame)
            output_frame_count += 1
        
        if self.callback:
            self.callback("progress", total_frames)
            self.callback("status", f"Slow motion effect completed with {output_frame_count} frames")
        
        return output_frame_count > 0
    
    def start_processing(self, video_path, output_path=None, effect_type="motion_blur", 
                         intensity=0.5, frame_rate=30, duration=5.0, output_format="mp4"):
        """Start video processing in a separate thread."""
        if self.processing_thread and self.processing_thread.is_alive():
            if self.callback:
                self.callback("status", "Processing is already running.")
            return False
            
        self.cancel_processing = False
        self.output_files = []
        
        self.processing_thread = threading.Thread(
            target=self._process_video,
            args=(video_path, output_path, effect_type, intensity, frame_rate, duration, output_format)
        )
        self.processing_thread.daemon = True
        self.processing_thread.start()
        
        return True
    
    def _process_video(self, video_path, output_path, effect_type, intensity, frame_rate, duration, output_format):
        """Process video in a separate thread."""
        try:
            output_file = self.create_smooth_motion(
                video_path, output_path, effect_type, intensity, frame_rate, duration, output_format
            )
            
            if output_file:
                self.output_files.append(output_file)
                
            if self.callback:
                self.callback("complete", self.output_files)
                
        except Exception as e:
            if self.callback:
                self.callback("status", f"Error in processing thread: {e}")
    
    def cancel(self):
        """Cancel the processing operation."""
        self.cancel_processing = True
        if self.callback:
            self.callback("status", "Cancelling processing...")
        return True
