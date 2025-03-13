import os
import threading
import numpy as np
from PIL import Image, ImageSequence
import imageio

class GIFCreator:
    """Core functionality for creating animated GIFs from sequences of images."""
    
    def __init__(self, callback=None):
        self.callback = callback
        self.cancel_processing = False
        self.processing_thread = None
        self.output_files = []
    
    def create_gif(self, file_paths, output_path=None, fps=10, loop=0, optimize=True, quality=85, resize_factor=1.0):
        """Create an animated GIF from a sequence of images."""
        try:
            if not file_paths:
                if self.callback:
                    self.callback("status", "No image files provided.")
                return None
            
            # Sort files by name if there are multiple
            file_paths = sorted(file_paths)
            
            # Create default output path if none provided
            if not output_path:
                # Use directory of first image and a default name
                first_dir = os.path.dirname(file_paths[0])
                output_path = os.path.join(first_dir, "animated.gif")
            
            # Calculate duration in ms from fps
            duration = 1000 // fps
            
            if self.callback:
                self.callback("status", f"Creating GIF with {len(file_paths)} frames at {fps} fps")
                self.callback("progress", 0)
                self.callback("max_progress", len(file_paths))
            
            # Method 1: Using PIL
            if optimize:
                images = []
                
                for i, file_path in enumerate(file_paths):
                    if self.cancel_processing:
                        if self.callback:
                            self.callback("status", "Processing cancelled.")
                        return None
                    
                    # Open the image
                    img = Image.open(file_path)
                    
                    # Resize if needed
                    if resize_factor != 1.0:
                        new_width = int(img.width * resize_factor)
                        new_height = int(img.height * resize_factor)
                        img = img.resize((new_width, new_height), Image.LANCZOS)
                    
                    # Convert to RGB if needed
                    if img.mode == 'RGBA':
                        # Use white as background color
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        background.paste(img, mask=img.split()[3])
                        img = background
                    elif img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    images.append(img)
                    
                    if self.callback:
                        self.callback("progress", i + 1)
                        self.callback("status", f"Processed frame {i+1} of {len(file_paths)}")
                
                # Save the GIF
                images[0].save(
                    output_path,
                    save_all=True,
                    append_images=images[1:],
                    optimize=optimize,
                    duration=duration,
                    loop=loop,
                    quality=quality
                )
            
            # Method 2: Using imageio (typically produces smaller files)
            else:
                frames = []
                
                for i, file_path in enumerate(file_paths):
                    if self.cancel_processing:
                        if self.callback:
                            self.callback("status", "Processing cancelled.")
                        return None
                    
                    # Read the image
                    img = imageio.imread(file_path)
                    
                    # Resize if needed
                    if resize_factor != 1.0:
                        from skimage.transform import resize
                        new_shape = (int(img.shape[0] * resize_factor), int(img.shape[1] * resize_factor))
                        if len(img.shape) == 3:  # Color image with channels
                            img = resize(img, (new_shape[0], new_shape[1], img.shape[2]), 
                                        anti_aliasing=True, preserve_range=True).astype(img.dtype)
                        else:  # Grayscale image
                            img = resize(img, new_shape, anti_aliasing=True, preserve_range=True).astype(img.dtype)
                    
                    frames.append(img)
                    
                    if self.callback:
                        self.callback("progress", i + 1)
                        self.callback("status", f"Processed frame {i+1} of {len(file_paths)}")
                
                # Create the output directory if it doesn't exist
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                # Save the GIF
                imageio.mimsave(output_path, frames, 'GIF', duration=duration/1000, loop=loop)
            
            if self.callback:
                self.callback("status", f"GIF created: {output_path}")
                self.callback("output_file", output_path)
                
                # Generate a preview
                try:
                    # Create a smaller version for preview
                    preview_img = Image.open(output_path)
                    if self.callback:
                        self.callback("preview", preview_img)
                except Exception as e:
                    if self.callback:
                        self.callback("status", f"Warning: Could not generate preview: {e}")
            
            return output_path
                
        except Exception as e:
            if self.callback:
                self.callback("status", f"Error creating GIF: {e}")
            return None
    
    def start_processing(self, file_paths, output_path=None, fps=10, loop=0, optimize=True, quality=85, resize_factor=1.0):
        """Start GIF creation in a separate thread."""
        if self.processing_thread and self.processing_thread.is_alive():
            if self.callback:
                self.callback("status", "Processing is already running.")
            return False
            
        self.cancel_processing = False
        self.output_files = []
        
        self.processing_thread = threading.Thread(
            target=self._process_gif,
            args=(file_paths, output_path, fps, loop, optimize, quality, resize_factor)
        )
        self.processing_thread.daemon = True
        self.processing_thread.start()
        
        return True
    
    def _process_gif(self, file_paths, output_path, fps, loop, optimize, quality, resize_factor):
        """Process GIF creation in a separate thread."""
        try:
            output_file = self.create_gif(file_paths, output_path, fps, loop, optimize, quality, resize_factor)
            
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
