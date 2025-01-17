import tkinter as tk
from tkinter import filedialog, ttk
import numpy as np
import rawpy
from PIL import Image, ImageTk, ExifTags
import threading
import subprocess
import os
import psutil
import sys
from fractions import Fraction
import math

# Get the script directory and the path to exiftool
script_directory = os.path.dirname(os.path.abspath(sys.argv[0]))
exiftool_path = os.path.join(script_directory, "exiftool.exe")

def get_exposure_time(file_path):
    """Get the exposure time from EXIF data as a Fraction."""
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

def update_preview_image(image_array):
    """Update the preview image in the UI."""
    img = Image.fromarray(np.uint8(image_array))
    img.thumbnail((600, 600))
    img_tk = ImageTk.PhotoImage(img)
    preview_image_label.config(image=img_tk)
    preview_image_label.image = img_tk

def select_files():
    """Select image files."""
    global file_paths, total_exposure_time

    file_paths = filedialog.askopenfilenames(title="Select .dng files", filetypes=[("DNG files", "*.dng")])
    if not file_paths:
        status_var.set("No files selected.")
        return

    total_exposure_time = Fraction(0)
    for file_path in file_paths:
        total_exposure_time += get_exposure_time(file_path)

    status_var.set(f"Selected {len(file_paths)} files.")
    details_var.set('\n'.join(file_paths))
    app.update_idletasks()

def start_stacking():
    """Start processing the images."""
    if not file_paths:
        status_var.set("No files selected.")
        return

    selected_methods = []
    if mean_var.get():
        selected_methods.append('Mean')
    if max_var.get():
        selected_methods.append('Maximum')
    if min_var.get():
        selected_methods.append('Minimum')
    if sigma_clip_var.get():
        selected_methods.append('Sigma Clipping')

    if not selected_methods:
        status_var.set("No stacking methods selected.")
        return

    # Get CPU and RAM limits
    cpu_limit = cpu_limit_var.get()  # percentage
    ram_limit = ram_limit_var.get()  # in MB

    # Start processing in a separate thread
    threading.Thread(target=process_images, args=(file_paths, selected_methods, cpu_limit, ram_limit)).start()

def process_images(file_paths, selected_methods, cpu_limit, ram_limit):
    """Process images with resource limits."""
    global images, output_files
    output_files = []
    images = []
    total_files = len(file_paths)

    # Estimate memory usage per image
    with rawpy.imread(file_paths[0]) as raw:
        img = raw.postprocess()
        img_size = img.nbytes / (1024 * 1024)  # in MB

    # Calculate how many images can be loaded into memory based on RAM limit
    max_images_in_memory = max(1, int(ram_limit // img_size))

    status_var.set("Processing images...")
    progress_var.set(0)
    progress_bar.config(maximum=total_files)
    app.update_idletasks()

    # Load images in batches
    images = []
    batch_size = max_images_in_memory
    for i in range(0, total_files, batch_size):
        images.clear()
        batch_paths = file_paths[i:i+batch_size]
        for index, file_path in enumerate(batch_paths):
            with rawpy.imread(file_path) as raw:
                img = raw.postprocess().astype(np.float32)
            images.append(img)
            progress_var.set(i + index + 1)
            status_var.set(f"Loaded image {i + index + 1}/{total_files}")
            app.update_idletasks()

            # Update CPU and memory utilization
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            details_var.set(f"Loading images...\nCPU utilization: {cpu_percent}%\nMemory utilization: {memory_percent}%")
            app.update_idletasks()

        # Now process the batch with each stacking method
        for stacking_method in selected_methods:
            status_var.set(f"Processing {stacking_method} stacking...")
            current_method_var.set(f"Running: {stacking_method}")
            app.update_idletasks()

            # Depending on the stacking method, process accordingly
            # For 'Mean', 'Maximum', 'Minimum', we can process in batches
            if stacking_method == 'Mean':
                if i == 0:
                    sum_image = np.sum(images, axis=0)
                    count = len(images)
                else:
                    sum_image += np.sum(images, axis=0)
                    count += len(images)
                if i + batch_size >= total_files:
                    stacked_image = sum_image / count
            elif stacking_method == 'Maximum':
                if i == 0:
                    stacked_image = np.max(images, axis=0)
                else:
                    stacked_image = np.maximum(stacked_image, np.max(images, axis=0))
            elif stacking_method == 'Minimum':
                if i == 0:
                    stacked_image = np.min(images, axis=0)
                else:
                    stacked_image = np.minimum(stacked_image, np.min(images, axis=0))
            elif stacking_method == 'Sigma Clipping':
                # Sigma Clipping requires all images
                # If RAM limit is exceeded, we need to process in a way that limits memory usage
                # Here we can process batches and store intermediate results
                # For simplicity, we can skip sigma clipping if RAM limit is too low
                if i == 0:
                    all_images = np.array(images)
                else:
                    all_images = np.concatenate((all_images, images), axis=0)
                if i + batch_size >= total_files:
                    # Now perform sigma clipping
                    mean = np.mean(all_images, axis=0)
                    std = np.std(all_images, axis=0)
                    sigma = 2  # Adjust sigma value as needed
                    mask = np.abs(all_images - mean) <= sigma * std
                    clipped_stack = np.where(mask, all_images, np.nan)
                    stacked_image = np.nanmean(clipped_stack, axis=0)
                    stacked_image = np.nan_to_num(stacked_image)
            else:
                continue  # Unknown stacking method

            # Update preview image
            if i + batch_size >= total_files:
                update_preview_image(stacked_image)

                # Save the stacked image with EXIF data
                stacked_image = np.clip(stacked_image, 0, 255).astype(np.uint8)
                img = Image.fromarray(stacked_image)
                img_exif = img.getexif()
                img_exif[33434] = (total_exposure_time.numerator, total_exposure_time.denominator)

                # Save file
                save_dir = os.path.dirname(file_paths[0])
                first_file_name = os.path.splitext(os.path.basename(file_paths[0]))[0]
                total_exposure_time_float = float(total_exposure_time)
                save_filename = f"{first_file_name}_{stacking_method}_{total_exposure_time_float:.2f}s.tiff"
                save_path = os.path.join(save_dir, save_filename)
                img.save(save_path, exif=img_exif)

                # Provide feedback and display the file path of the image created
                status_var.set(f"Saved {stacking_method} stacked image to {save_path}")
                app.update_idletasks()

                output_files.append(save_path)

        # Update CPU and memory utilization
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent
        details_var.set(f"Processing images...\nCPU utilization: {cpu_percent}%\nMemory utilization: {memory_percent}%")
        app.update_idletasks()

    # Display all output file paths
    files_created = "\n".join(output_files)
    details_var.set(f"Files created:\n{files_created}")

    status_var.set("All stacking methods completed.")
    current_method_var.set("")
    app.bell()

app = tk.Tk()
app.title("DNG Averager")
app.configure(bg='#f0f0f0')

frame = ttk.Frame(app, padding="20 20 20 20")
frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

title_font = ('Arial', 14, 'bold')
label_font = ('Arial', 12)

title_label = ttk.Label(frame, text="DNG Averager", font=title_font)
title_label.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 20))

files_label = ttk.Label(frame, text="Select DNG files to average:", font=label_font)
files_label.grid(row=1, column=0, sticky=tk.W, padx=(10, 0))
select_files_button = ttk.Button(frame, text="Select files", command=select_files)
select_files_button.grid(row=1, column=1, sticky=tk.E, padx=(0, 10))

# Add a label for stacking methods
stacking_label = ttk.Label(frame, text="Select stacking methods:", font=label_font)
stacking_label.grid(row=2, column=0, sticky=tk.W, padx=(10, 0))

# Define BooleanVars for checkboxes
mean_var = tk.BooleanVar(value=True)
max_var = tk.BooleanVar(value=False)
min_var = tk.BooleanVar(value=False)
sigma_clip_var = tk.BooleanVar(value=False)

# Create checkboxes
mean_check = ttk.Checkbutton(frame, text='Mean', variable=mean_var)
mean_check.grid(row=2, column=1, sticky=tk.W)

max_check = ttk.Checkbutton(frame, text='Maximum', variable=max_var)
max_check.grid(row=3, column=1, sticky=tk.W)

min_check = ttk.Checkbutton(frame, text='Minimum', variable=min_var)
min_check.grid(row=4, column=1, sticky=tk.W)

sigma_clip_check = ttk.Checkbutton(frame, text='Sigma Clipping', variable=sigma_clip_var)
sigma_clip_check.grid(row=5, column=1, sticky=tk.W)

# Add CPU and RAM limit sliders
cpu_limit_label = ttk.Label(frame, text="CPU Limit (%):", font=label_font)
cpu_limit_label.grid(row=6, column=0, sticky=tk.W, padx=(10, 0))
cpu_limit_var = tk.IntVar(value=100)
cpu_limit_slider = ttk.Scale(frame, from_=10, to=100, orient=tk.HORIZONTAL, variable=cpu_limit_var)
cpu_limit_slider.grid(row=6, column=1, sticky=(tk.W, tk.E), padx=(0, 10))

ram_limit_label = ttk.Label(frame, text="RAM Limit (MB):", font=label_font)
ram_limit_label.grid(row=7, column=0, sticky=tk.W, padx=(10, 0))
ram_limit_var = tk.IntVar(value=4096)
ram_limit_slider = ttk.Scale(frame, from_=256, to=16384, orient=tk.HORIZONTAL, variable=ram_limit_var)
ram_limit_slider.grid(row=7, column=1, sticky=(tk.W, tk.E), padx=(0, 10))

start_button = ttk.Button(frame, text="Start Stacking", command=start_stacking)
start_button.grid(row=8, column=1, sticky=tk.E, padx=(0, 10), pady=(10, 0))

status_var = tk.StringVar()
status_label = ttk.Label(frame, textvariable=status_var, font=label_font)
status_label.grid(row=9, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=(10, 0), pady=(10, 0))

current_method_var = tk.StringVar()
current_method_label = ttk.Label(frame, textvariable=current_method_var, font=label_font)
current_method_label.grid(row=10, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=(10, 0))

progress_var = tk.IntVar()
progress_bar = ttk.Progressbar(frame, variable=progress_var, mode='determinate')
progress_bar.grid(row=11, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=(10, 10), pady=(10, 0))

details_var = tk.StringVar()
details_label = ttk.Label(frame, textvariable=details_var, font=label_font, wraplength=400, justify=tk.LEFT)
details_label.grid(row=12, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=(10, 0), pady=(10, 0))

preview_image_label = ttk.Label(frame)
preview_image_label.grid(row=13, column=0, columnspan=2, padx=(10, 10), pady=(10, 0))

# Initialize file_paths and total_exposure_time
file_paths = []
total_exposure_time = Fraction(0)
output_files = []

app.mainloop()
