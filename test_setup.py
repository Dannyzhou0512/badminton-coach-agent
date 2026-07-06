"""
Quick test script - Run this after installation to verify setup.
Tests pose extraction on a single video.
"""

from ultralytics import YOLO
import cv2
import numpy as np
from pathlib import Path

import torch
print(f"Device: {'GPU - ' + torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")

print("Testing YOLOv8-Pose setup...")

model = YOLO('yolov8s-pose.pt')
print(f"Model loaded: {model.ckpt_path}")

dataset_root = Path("G:/VideoBadminton_Dataset/VideoBadminton_Dataset")
category_dirs = sorted([d for d in dataset_root.iterdir() if d.is_dir() and not d.name.startswith('__')])

test_video = None
for cat_dir in category_dirs:
    videos = sorted(cat_dir.glob('*.mp4'))
    if videos:
        test_video = videos[0]
        break

if test_video is None:
    print("No video found!")
    exit(1)

print(f"Test video: {test_video}")

cap = cv2.VideoCapture(str(test_video))
frames = []
while True:
    ret, frame = cap.read()
    if not ret:
        break
    frames.append(frame)
cap.release()

print(f"Video frames: {len(frames)}")

results = model(frames[:10], verbose=False)

for i, r in enumerate(results[:3]):
    if r.keypoints is not None and len(r.keypoints) > 0:
        n_kpts = len(r.keypoints.conf[0])
        conf_mean = float(r.keypoints.conf[0].mean())
        print(f"Frame {i}: Detected {n_kpts} keypoints, avg confidence: {conf_mean:.3f}")
    else:
        print(f"Frame {i}: No person detected")

print("\nSetup verified successfully! Ready to process the full dataset.")
