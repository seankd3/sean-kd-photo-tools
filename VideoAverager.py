import cv2
import numpy as np
from tkinter import Tk
from tkinter.filedialog import askopenfilename
from PIL import Image
from tqdm import tqdm
import os

def select_video_file():
    Tk().withdraw()  # We don't want a full GUI, so keep the root window from appearing
    filename = askopenfilename(title="Select Video File", filetypes=[("Video files", "*.mp4 *.avi *.mov")])
    return filename

def average_frames(video_path):
    cap = cv2.VideoCapture(video_path)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Initialize an array to store the sum of all frames
    sum_frames = np.zeros((height, width, 3), np.float32)

    for _ in tqdm(range(frame_count), desc="Processing frames"):
        ret, frame = cap.read()
        if not ret:
            break
        sum_frames += frame

    # Calculate the average
    avg_frame = sum_frames / frame_count
    avg_frame = np.array(np.round(avg_frame), dtype=np.uint8)

    cap.release()
    return avg_frame

def save_as_tiff(image, output_path):
    img = Image.fromarray(image)
    img.save(output_path, format='TIFF')

if __name__ == "__main__":
    video_path = select_video_file()
    if video_path:
        avg_frame = average_frames(video_path)
        video_dir = os.path.dirname(video_path)
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        output_path = os.path.join(video_dir, f"{video_name}_average_frame.tiff")
        save_as_tiff(avg_frame, output_path)
        print(f"Averaged frame saved as {output_path}")
    else:
        print("No video file selected.")