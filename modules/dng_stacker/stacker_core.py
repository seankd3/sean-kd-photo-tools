import os
import sys
import numpy as np
import rawpy
from PIL import Image, ExifTags
import threading
import psutil
from fractions import Fraction
import concurrent.futures

class DNGStacker:
    """Core functionality for stacking DNG images."""
    
    def __init__(self, callback=None):
        self.callback = callback
        self.images = []
        self.file_paths = []
        self.total_exposure_time = Fraction(0)
        self.cancel_processing = False
        self.processing_thread = None
        self.output_files = []
        
        # Get the path to exiftool
        script_directory = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.exiftool_path = os.path.join(script_directory, "exiftool.exe")

    def get_exposure_time(self, file_path):
        """Get the exposure time from EXIF data as a Fraction."""
        try:
            with Image.open(file_path) as image:
                img_exif = image.getexif()
                for (k, v) in img_exif.items():
                    if ExifTags.TAGS.get(k) == 'ExposureTime':
                        exposure_time = v
                        if isinstance(exposure_time, tuple) and len(exposure_time) == 2:
                            # Exposure time is a fraction
                            return Fraction(exposure_time[0], exposure_time[1])
                        else:
                            # Exposure time is a float
                            return Fraction(exposure_time)
            return Fraction(0)
        except Exception as e:
            if self.callback:
                self.callback("status", f"Error reading exposure time: {e}")
            return Fraction(0)
    
    def set_file_paths(self, file_paths):
        """Set the file paths to process."""
        self.file_paths = file_paths
        self.total_exposure_time = Fraction(0)
        
        # Calculate total exposure time
        for file_path in file_paths:
            self.total_exposure_time += self.get_exposure_time(file_path)
            
        return len(file_paths)
    
    def start_processing(self, methods, cpu_limit, ram_limit):
        """Start processing images in a background thread."""
        if self.processing_thread and self.processing_thread.is_alive():
            if self.callback:
                self.callback("status", "Processing is already running.")
            return False
            
        self.cancel_processing = False
        self.processing_thread = threading.Thread(
            target=self.process_images, 
            args=(self.file_paths, methods, cpu_limit, ram_limit)
        )
        self.processing_thread.daemon = True
        self.processing_thread.start()
        return True
    
    def cancel(self):
        """Cancel the processing operation."""
        self.cancel_processing = True
        if self.callback:
            self.callback("status", "Cancelling processing...")
        return True
    
    def process_images(self, file_paths, selected_methods, cpu_limit, ram_limit):
        """Process images with resource limits."""
        self.output_files = []
        total_files = len(file_paths)
        
        if total_files == 0:
            if self.callback:
                self.callback("status", "No files to process.")
            return
        
        # Estimate memory usage per image
        with rawpy.imread(file_paths[0]) as raw:
            img = raw.postprocess()
            img_size = img.nbytes / (1024 * 1024)  # in MB
        
        # Calculate how many images can be loaded into memory based on RAM limit
        max_images_in_memory = max(1, int(ram_limit // img_size))
        
        if self.callback:
            self.callback("status", "Processing images...")
            self.callback("progress", 0)
            self.callback("max_progress", total_files)
        
        # Process images in batches
        batch_size = max_images_in_memory
        
        # Initialize stacked images for each method
        stacked_images = {}
        counts = {}
        
        # Process each batch
        for i in range(0, total_files, batch_size):
            if self.cancel_processing:
                if self.callback:
                    self.callback("status", "Processing cancelled.")
                return
                
            # Load a batch of images
            batch_paths = file_paths[i:i+batch_size]
            batch_images = []
            
            # Use ThreadPoolExecutor for parallel loading
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(os.cpu_count(), 4)) as executor:
                # Submit tasks
                future_to_index = {executor.submit(self.load_raw_image, path): idx 
                                   for idx, path in enumerate(batch_paths)}
                
                # Process completed tasks
                for future in concurrent.futures.as_completed(future_to_index):
                    idx = future_to_index[future]
                    try:
                        img = future.result()
                        if img is not None:
                            batch_images.append((idx, img))
                    except Exception as e:
                        if self.callback:
                            self.callback("status", f"Error processing image: {e}")
            
            # Sort images by original index
            batch_images.sort(key=lambda x: x[0])
            batch_images = [img for _, img in batch_images]
            
            if not batch_images:
                continue
                
            # Update progress
            if self.callback:
                self.callback("progress", i + len(batch_images))
                self.callback("status", f"Loaded images {i + 1}-{min(i + len(batch_images), total_files)} of {total_files}")
                
                # Update CPU and memory utilization
                cpu_percent = psutil.cpu_percent()
                memory_percent = psutil.virtual_memory().percent
                self.callback("details", f"CPU: {cpu_percent}% | Memory: {memory_percent}%")
            
            # Process the batch for each stacking method
            for method in selected_methods:
                if self.cancel_processing:
                    break
                    
                if self.callback:
                    self.callback("status", f"Applying {method} stacking method...")
                    self.callback("current_method", method)
                
                if method == 'Mean':
                    # Initialize or update sum_image
                    if 'Mean' not in stacked_images:
                        stacked_images['Mean'] = np.sum(batch_images, axis=0)
                        counts['Mean'] = len(batch_images)
                    else:
                        stacked_images['Mean'] += np.sum(batch_images, axis=0)
                        counts['Mean'] += len(batch_images)
                
                elif method == 'Maximum':
                    # Initialize or update max_image
                    batch_max = np.max(batch_images, axis=0)
                    if 'Maximum' not in stacked_images:
                        stacked_images['Maximum'] = batch_max
                    else:
                        stacked_images['Maximum'] = np.maximum(stacked_images['Maximum'], batch_max)
                
                elif method == 'Minimum':
                    # Initialize or update min_image
                    batch_min = np.min(batch_images, axis=0)
                    if 'Minimum' not in stacked_images:
                        stacked_images['Minimum'] = batch_min
                    else:
                        stacked_images['Minimum'] = np.minimum(stacked_images['Minimum'], batch_min)
                
                elif method == 'Sigma Clipping':
                    # For Sigma Clipping, we need all images
                    # Here we implement a memory-efficient approach
                    if i == 0:
                        # First batch - calculate running mean and variance
                        if 'Sigma_Mean' not in stacked_images:
                            stacked_images['Sigma_Mean'] = np.mean(batch_images, axis=0)
                            stacked_images['Sigma_Var'] = np.var(batch_images, axis=0)
                            counts['Sigma'] = len(batch_images)
                    else:
                        # Update running mean and variance using Welford's online algorithm
                        for img in batch_images:
                            counts['Sigma'] += 1
                            delta = img - stacked_images['Sigma_Mean']
                            stacked_images['Sigma_Mean'] += delta / counts['Sigma']
                            delta2 = img - stacked_images['Sigma_Mean']
                            stacked_images['Sigma_Var'] += delta * delta2
                
                # Clear batch data to free memory
                del batch_images
                
            # Check if we're at the last batch
            if i + batch_size >= total_files:
                # Finalize each stacking method
                for method in selected_methods:
                    if self.cancel_processing:
                        break
                    
                    if method == 'Mean':
                        final_image = stacked_images['Mean'] / counts['Mean']
                    elif method in ['Maximum', 'Minimum']:
                        final_image = stacked_images[method]
                    elif method == 'Sigma Clipping':
                        # Finalize Sigma Clipping
                        sigma = 2.0  # Adjustable sigma parameter
                        mean = stacked_images['Sigma_Mean']
                        std = np.sqrt(stacked_images['Sigma_Var'] / (counts['Sigma'] - 1))
                        
                        # Re-process all images with sigma clipping
                        sigma_sum = np.zeros_like(mean)
                        sigma_count = np.zeros_like(mean)
                        
                        for j in range(0, total_files, batch_size):
                            sigma_batch = file_paths[j:j+batch_size]
                            for file_path in sigma_batch:
                                with rawpy.imread(file_path) as raw:
                                    img = raw.postprocess().astype(np.float32)
                                    # Apply mask based on sigma threshold
                                    mask = np.abs(img - mean) <= sigma * std
                                    sigma_sum[mask] += img[mask]
                                    sigma_count[mask] += 1
                        
                        # Calculate final image (avoiding division by zero)
                        mask = sigma_count > 0
                        final_image = np.zeros_like(mean)
                        final_image[mask] = sigma_sum[mask] / sigma_count[mask]
                        # For pixels with zero count, use original mean
                        final_image[~mask] = mean[~mask]
                    
                    # Save the stacked image
                    self.save_stacked_image(final_image, method, file_paths[0])
        
        if self.callback:
            self.callback("status", "Processing complete!")
            self.callback("progress", total_files)
        
        return self.output_files
    
    def load_raw_image(self, file_path):
        """Load a raw image file."""
        try:
            with rawpy.imread(file_path) as raw:
                return raw.postprocess().astype(np.float32)
        except Exception as e:
            if self.callback:
                self.callback("status", f"Error loading image {file_path}: {e}")
            return None
    
    def save_stacked_image(self, image_array, method, reference_file):
        """Save the stacked image with EXIF data."""
        try:
            # Clip values to valid range
            image_array = np.clip(image_array, 0, 255).astype(np.uint8)
            
            # Create PIL image
            img = Image.fromarray(image_array)
            
            # Copy EXIF data from first image
            try:
                with Image.open(reference_file) as ref_img:
                    exif_dict = ref_img.getexif()
                    # Update Exposure Time with total exposure
                    if exif_dict is not None:
                        for tag_id, tag_name in ExifTags.TAGS.items():
                            if tag_name == 'ExposureTime':
                                exif_dict[tag_id] = (self.total_exposure_time.numerator, 
                                                     self.total_exposure_time.denominator)
            except Exception as e:
                if self.callback:
                    self.callback("status", f"Warning: Could not copy EXIF data: {e}")
                exif_dict = None
            
            # Save file
            save_dir = os.path.dirname(reference_file)
            first_file_name = os.path.splitext(os.path.basename(reference_file))[0]
            total_exposure_time_float = float(self.total_exposure_time)
            save_filename = f"{first_file_name}_{method}_{total_exposure_time_float:.2f}s.tiff"
            save_path = os.path.join(save_dir, save_filename)
            
            # Save with EXIF data
            img.save(save_path, format='TIFF', exif=exif_dict)
            
            if self.callback:
                self.callback("status", f"Saved {method} stacked image to {save_path}")
            
            self.output_files.append(save_path)
            return save_path
            
        except Exception as e:
            if self.callback:
                self.callback("status", f"Error saving image: {e}")
            return None
