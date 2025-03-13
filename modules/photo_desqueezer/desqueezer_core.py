import os
import threading
import numpy as np
import rawpy
from PIL import Image, ExifTags

class PhotoDesqueezer:
    """Core functionality for desqueezing anamorphic DNG files."""
    
    def __init__(self, callback=None):
        self.callback = callback
        self.cancel_processing = False
        self.processing_thread = None
        self.output_files = []
        
    def desqueeze_file(self, file_path, desqueeze_factor, output_format="tiff"):
        """Desqueeze a single DNG file."""
        try:
            # Open the DNG file
            with rawpy.imread(file_path) as raw:
                # Post-process the raw image
                rgb_image = raw.postprocess()
                # Convert to a PIL Image for resizing
                image = Image.fromarray(rgb_image)
                
                # Calculate the new width
                new_width = int(image.width * desqueeze_factor)
                
                # Resize the image
                desqueezed_image = image.resize((new_width, image.height), Image.LANCZOS)
                
                # Get output file path
                output_file_path = self._get_output_path(file_path, output_format)
                
                # Copy EXIF data
                exif_data = None
                try:
                    with Image.open(file_path) as ref_img:
                        exif_data = ref_img.getexif()
                except Exception as e:
                    if self.callback:
                        self.callback("status", f"Warning: Could not copy EXIF data: {e}")
                
                # Save the image
                if output_format.lower() == "tiff":
                    desqueezed_image.save(output_file_path, format='TIFF', exif=exif_data)
                elif output_format.lower() == "jpg" or output_format.lower() == "jpeg":
                    desqueezed_image.save(output_file_path, format='JPEG', quality=95, exif=exif_data)
                elif output_format.lower() == "png":
                    desqueezed_image.save(output_file_path, format='PNG', exif=exif_data)
                else:
                    # Default to TIFF
                    desqueezed_image.save(output_file_path, format='TIFF', exif=exif_data)
                
                # Return the output file path
                return output_file_path
                
        except Exception as e:
            if self.callback:
                self.callback("status", f"Error processing {file_path}: {e}")
            return None
    
    def _get_output_path(self, input_path, output_format):
        """Generate the output file path."""
        # Get the directory and filename
        directory = os.path.dirname(input_path)
        filename = os.path.splitext(os.path.basename(input_path))[0]
        
        # Create the output directory if it doesn't exist
        output_dir = os.path.join(directory, 'Desqueezed')
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate the output file path
        output_path = os.path.join(output_dir, f"{filename}_desqueezed.{output_format.lower()}")
        
        return output_path
    
    def start_batch_processing(self, file_paths, desqueeze_factor, output_format="tiff"):
        """Start batch processing of multiple files."""
        if self.processing_thread and self.processing_thread.is_alive():
            if self.callback:
                self.callback("status", "Processing is already running.")
            return False
            
        self.cancel_processing = False
        self.output_files = []
        
        self.processing_thread = threading.Thread(
            target=self._process_batch,
            args=(file_paths, desqueeze_factor, output_format)
        )
        self.processing_thread.daemon = True
        self.processing_thread.start()
        
        return True
    
    def _process_batch(self, file_paths, desqueeze_factor, output_format):
        """Process a batch of files."""
        total_files = len(file_paths)
        
        if self.callback:
            self.callback("status", f"Processing {total_files} files...")
            self.callback("progress", 0)
            self.callback("max_progress", total_files)
        
        for i, file_path in enumerate(file_paths):
            if self.cancel_processing:
                if self.callback:
                    self.callback("status", "Processing cancelled.")
                break
            
            if self.callback:
                self.callback("status", f"Processing file {i+1} of {total_files}: {os.path.basename(file_path)}")
            
            # Process the file
            output_file = self.desqueeze_file(file_path, desqueeze_factor, output_format)
            
            if output_file:
                self.output_files.append(output_file)
                if self.callback:
                    self.callback("output_file", output_file)
            
            if self.callback:
                self.callback("progress", i + 1)
        
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
