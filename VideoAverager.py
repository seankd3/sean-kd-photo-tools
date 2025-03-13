import cv2
import numpy as np
from tkinter import Tk
from tkinter.filedialog import askopenfilenames
from PIL import Image
import os

def select_video_files():
    Tk().withdraw()  # We don't want a full GUI, so keep the root window from appearing
    filenames = askopenfilenames(title="Select Video File(s)", filetypes=[("Video files", "*.mp4 *.avi *.mov")])
    return filenames

def average_frames(video_path):
    cap = cv2.VideoCapture(video_path)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    sum_frames = np.zeros((height, width, 3), dtype=np.float64)
    count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        sum_frames += frame
        count += 1

    if count > 0:
        avg_frame = sum_frames / count
        avg_frame = avg_frame.round().astype(np.uint8)
    else:
        avg_frame = None

    cap.release()
    return avg_frame

def save_as_tiff(image, output_path):
    img = Image.fromarray(image)
    img.save(output_path, format='TIFF')

if __name__ == "__main__":
    file_paths = select_video_files()
    if file_paths:
        for video_path in file_paths:
            avg_frame = average_frames(video_path)
            if avg_frame is not None:
                video_dir = os.path.dirname(video_path)
                video_name = os.path.splitext(os.path.basename(video_path))[0]
                output_path = os.path.join(video_dir, f"{video_name}_average_frame.tiff")
                save_as_tiff(avg_frame, output_path)
                print(f"Averaged frame saved as {output_path}")
            else:
                print(f"Could not read frames from {video_path}")
    else:
        print("No video file selected.")