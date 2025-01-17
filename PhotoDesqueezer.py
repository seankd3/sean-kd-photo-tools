import os
from tkinter import Tk
from tkinter.filedialog import askdirectory
from PIL import Image
import rawpy

def desqueeze_and_convert(folder_path, desqueeze_factor=1.6):
    # Create the output folder path
    output_folder = os.path.join(folder_path, 'Desqueezed_TIFFs')
    os.makedirs(output_folder, exist_ok=True)
    
    # Loop through each file in the folder
    for filename in os.listdir(folder_path):
        if filename.lower().endswith('.dng'):
            file_path = os.path.join(folder_path, filename)
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
                    # Save the image as a TIFF in the output folder
                    output_file_path = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}.tiff")
                    desqueezed_image.save(output_file_path, format='TIFF')
                    print(f"Saved: {output_file_path}")
            except Exception as e:
                print(f"Error processing {filename}: {e}")

# Main program
if __name__ == "__main__":
    # Hide the root Tkinter window
    root = Tk()
    root.withdraw()
    # Ask the user to select a folder
    folder_path = askdirectory(title="Select Folder with DNG Files")
    if folder_path:
        desqueeze_and_convert(folder_path)
    else:
        print("No folder selected.")
