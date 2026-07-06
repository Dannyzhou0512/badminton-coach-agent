"""
Pose Visualization Script
Visualize extracted pose keypoints on video frames.
"""

import cv2
import numpy as np
from pathlib import Path
import argparse
from tqdm import tqdm

SKELETON = [
    [5, 7], [7, 9], [6, 8], [8, 10],
    [5, 6], [5, 11], [6, 12], [11, 12],
    [11, 13], [13, 15], [12, 14], [14, 16]
]

KEYPOINT_COLORS = {
    'face': (255, 200, 100),
    'left_arm': (0, 255, 0),
    'right_arm': (0, 0, 255),
    'torso': (255, 0, 255),
    'left_leg': (255, 255, 0),
    'right_leg': (0, 165, 255),
}


def get_keypoint_color(idx):
    if idx <= 4:
        return KEYPOINT_COLORS['face']
    elif idx in [5, 7, 9]:
        return KEYPOINT_COLORS['left_arm']
    elif idx in [6, 8, 10]:
        return KEYPOINT_COLORS['right_arm']
    elif idx in [11, 12]:
        return KEYPOINT_COLORS['torso']
    elif idx in [13, 15]:
        return KEYPOINT_COLORS['left_leg']
    else:
        return KEYPOINT_COLORS['right_leg']


def draw_pose_on_frame(frame, keypoints, conf_threshold=0.3):
    h, w = frame.shape[:2]
    vis_frame = frame.copy()

    for connection in SKELETON:
        idx1, idx2 = connection
        if keypoints[idx1, 2] > conf_threshold and keypoints[idx2, 2] > conf_threshold:
            pt1 = (int(keypoints[idx1, 0]), int(keypoints[idx1, 1]))
            pt2 = (int(keypoints[idx2, 0]), int(keypoints[idx2, 1]))
            color = get_keypoint_color(idx1)
            cv2.line(vis_frame, pt1, pt2, color, 2)

    for idx in range(len(keypoints)):
        if keypoints[idx, 2] > conf_threshold:
            x, y = int(keypoints[idx, 0]), int(keypoints[idx, 1])
            color = get_keypoint_color(idx)
            cv2.circle(vis_frame, (x, y), 4, color, -1)
            cv2.circle(vis_frame, (x, y), 4, (255, 255, 255), 1)

    return vis_frame


def visualize_video_pose(video_path, pose_npy_path, output_path, max_frames=None, conf_threshold=0.3):
    cap = cv2.VideoCapture(str(video_path))
    pose_seq = np.load(pose_npy_path)

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0:
        fps = 30
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(output_path), fourcc, fps, (w, h))

    frame_idx = 0
    while cap.isOpened() and frame_idx < len(pose_seq):
        ret, frame = cap.read()
        if not ret:
            break
        if max_frames and frame_idx >= max_frames:
            break

        keypoints = pose_seq[frame_idx]
        vis_frame = draw_pose_on_frame(frame, keypoints, conf_threshold)
        info = f"Frame: {frame_idx} | Keypoints: {np.sum(keypoints[:, 2] > conf_threshold)}/17"
        cv2.putText(vis_frame, info, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        out.write(vis_frame)
        frame_idx += 1

    cap.release()
    out.release()
    print(f"Visualization saved: {output_path}")


def visualize_sample(dataset_root, pose_root, output_root, num_samples=3, conf_threshold=0.3):
    dataset_root = Path(dataset_root)
    pose_root = Path(pose_root)
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    category_dirs = sorted([d for d in dataset_root.iterdir() if d.is_dir() and not d.name.startswith('__')])

    for cat_dir in tqdm(category_dirs, desc='Categories'):
        cat_name = cat_dir.name
        cat_out = output_root / cat_name
        cat_out.mkdir(parents=True, exist_ok=True)

        video_files = sorted(cat_dir.glob('*.mp4'))
        if len(video_files) == 0:
            continue

        import random
        samples = random.sample(video_files, min(num_samples, len(video_files)))

        for video_file in samples:
            pose_file = pose_root / cat_name / f"{video_file.stem}_pose.npy"
            if not pose_file.exists():
                continue
            out_video = cat_out / f"{video_file.stem}_vis.mp4"
            visualize_video_pose(video_file, pose_file, out_video, conf_threshold=conf_threshold)


def main():
    parser = argparse.ArgumentParser(description='Visualize pose keypoints on videos')
    parser.add_argument('--dataset', type=str, default='G:/VideoBadminton_Dataset/VideoBadminton_Dataset')
    parser.add_argument('--pose-dir', type=str, default='E:/Learning/badminton-agent/data/pose_features')
    parser.add_argument('--output', type=str, default='E:/Learning/badminton-agent/data/visualizations')
    parser.add_argument('--samples', type=int, default=2)
    parser.add_argument('--conf', type=float, default=0.3)
    args = parser.parse_args()

    visualize_sample(args.dataset, args.pose_dir, args.output, args.samples, args.conf)


if __name__ == '__main__':
    main()
