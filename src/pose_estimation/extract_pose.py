"""
Batch Pose Extraction Script for VideoBadminton Dataset
Uses YOLOv8-Pose pretrained model to extract keypoints from all videos.
"""

import cv2
import numpy as np
from pathlib import Path
from tqdm import tqdm
import yaml
from ultralytics import YOLO
import argparse

# COCO 17 keypoint names
KEYPOINT_NAMES = [
    'nose', 'left_eye', 'right_eye', 'left_ear', 'right_ear',
    'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
    'left_wrist', 'right_wrist', 'left_hip', 'right_hip',
    'left_knee', 'right_knee', 'left_ankle', 'right_ankle'
]

# Skeleton connections for visualization
SKELETON = [
    [5, 7], [7, 9], [6, 8], [8, 10],  # arms
    [5, 6], [5, 11], [6, 12], [11, 12],  # torso
    [11, 13], [13, 15], [12, 14], [14, 16]  # legs
]


class PoseExtractor:
    def __init__(self, model_path='yolov8s-pose.pt', conf_threshold=0.3):
        self.model = YOLO(model_path)
        self.conf_threshold = conf_threshold
        print(f"Loaded pose model: {model_path}")

    def extract_from_video(self, video_path, max_frames=None):
        """
        Extract pose keypoints from a video file.
        Returns: (T, 17, 3) array of [x, y, confidence]
        """
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            print(f"Warning: Cannot open video {video_path}")
            return None

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if max_frames and total_frames > max_frames:
            frame_indices = np.linspace(0, total_frames - 1, max_frames, dtype=int)
        else:
            frame_indices = None

        frames = []
        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_indices is not None:
                if frame_idx in frame_indices:
                    frames.append(frame)
            else:
                frames.append(frame)
            frame_idx += 1
        cap.release()

        if len(frames) == 0:
            return None

        results = self.model(frames, verbose=False, conf=self.conf_threshold)

        sequence = []
        for r in results:
            if r.keypoints is not None and len(r.keypoints) > 0:
                if r.boxes is not None and len(r.boxes) > 0:
                    confs = r.boxes.conf.cpu().numpy()
                    best_idx = int(np.argmax(confs))
                else:
                    best_idx = 0

                kpts = r.keypoints.xy[best_idx].cpu().numpy()
                kconf = r.keypoints.conf[best_idx].cpu().numpy()
                kpts_3d = np.concatenate([kpts, kconf[:, None]], axis=1)
                sequence.append(kpts_3d)
            else:
                sequence.append(np.zeros((17, 3)))

        return np.array(sequence, dtype=np.float32)

    def process_dataset(self, dataset_root, output_root):
        """Process entire VideoBadminton dataset."""
        dataset_root = Path(dataset_root)
        output_root = Path(output_root)
        output_root.mkdir(parents=True, exist_ok=True)

        category_dirs = sorted([d for d in dataset_root.iterdir() if d.is_dir() and not d.name.startswith('__')])

        stats = {'processed': 0, 'failed': 0, 'total_frames': 0}

        for cat_dir in tqdm(category_dirs, desc='Categories'):
            cat_name = cat_dir.name
            cat_out = output_root / cat_name
            cat_out.mkdir(parents=True, exist_ok=True)

            video_files = sorted(cat_dir.glob('*.mp4'))
            for video_file in tqdm(video_files, desc=f'{cat_name}', leave=False):
                save_path = cat_out / f"{video_file.stem}_pose.npy"
                if save_path.exists():
                    stats['processed'] += 1
                    continue

                pose_seq = self.extract_from_video(video_file)
                if pose_seq is not None:
                    np.save(save_path, pose_seq)
                    stats['processed'] += 1
                    stats['total_frames'] += len(pose_seq)
                else:
                    stats['failed'] += 1

        print(f"\nExtraction complete!")
        print(f"  Videos processed: {stats['processed']}")
        print(f"  Videos failed: {stats['failed']}")
        print(f"  Total frames: {stats['total_frames']}")
        return stats


def main():
    parser = argparse.ArgumentParser(description='Extract pose keypoints from VideoBadminton Dataset')
    parser.add_argument('--config', type=str, default='configs/dataset.yaml')
    parser.add_argument('--model', type=str, default=None)
    parser.add_argument('--dataset', type=str, default=None)
    parser.add_argument('--output', type=str, default=None)
    args = parser.parse_args()

    with open(args.config, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    dataset_root = args.dataset or config['dataset_root']
    output_dir = args.output or config['pose_output_dir']
    model_path = args.model or config.get('pose_model', 'yolov8s-pose.pt')
    conf_thresh = config.get('conf_threshold', 0.3)

    print(f"Dataset: {dataset_root}")
    print(f"Output: {output_dir}")
    print(f"Model: {model_path}")

    extractor = PoseExtractor(model_path, conf_thresh)
    extractor.process_dataset(dataset_root, output_dir)


if __name__ == '__main__':
    main()
