"""
Badminton-specific Feature Engineering
Extract domain-relevant features from pose sequences.
"""

import numpy as np
from pathlib import Path
import json
from tqdm import tqdm
import argparse

# Keypoint indices (COCO 17)
KP = {
    'nose': 0, 'left_eye': 1, 'right_eye': 2, 'left_ear': 3, 'right_ear': 4,
    'left_shoulder': 5, 'right_shoulder': 6, 'left_elbow': 7, 'right_elbow': 8,
    'left_wrist': 9, 'right_wrist': 10, 'left_hip': 11, 'right_hip': 12,
    'left_knee': 13, 'right_knee': 14, 'left_ankle': 15, 'right_ankle': 16
}


def angle_between(v1, v2):
    """Compute angle between two vectors in degrees."""
    cos = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-8)
    return np.arccos(np.clip(cos, -1, 1)) * 180 / np.pi


def safe_stats(arr):
    """Safe min/max/mean/std for potentially empty arrays."""
    if len(arr) == 0:
        return 0.0, 0.0, 0.0, 0.0
    return float(np.min(arr)), float(np.max(arr)), float(np.mean(arr)), float(np.std(arr))


def extract_badminton_features(pose_seq):
    """
    Extract badminton-specific features from pose sequence.
    pose_seq: (T, 17, 3) array of [x, y, confidence]
    Returns: dict of features
    """
    features = {}
    T = pose_seq.shape[0]

    # Skip sequences with fewer than 2 frames (cannot compute diff/velocity)
    if T < 2:
        features['sequence_length'] = T
        features['valid_frames'] = 0
        features['detection_rate'] = 0.0
        # Fill all feature keys with 0.0 to keep consistent schema
        feature_keys = [
            'elbow_angle_mean', 'elbow_angle_min', 'elbow_angle_max', 'elbow_angle_std',
            'wrist_max_height', 'wrist_height_mean', 'arm_reach_max', 'arm_reach_mean',
            'torso_angle_mean', 'torso_angle_std',
            'left_knee_angle_mean', 'left_knee_angle_min',
            'right_knee_angle_mean', 'right_knee_angle_min',
            'left_foot_displacement', 'right_foot_displacement', 'total_foot_displacement',
            'foot_spread_mean', 'foot_spread_max', 'foot_spread_min',
            'hip_height_mean', 'hip_height_std',
            'wrist_velocity_mean', 'wrist_velocity_max', 'wrist_velocity_std',
            'elbow_velocity_mean', 'elbow_velocity_max', 'elbow_velocity_std',
        ]
        for k in feature_keys:
            features[k] = 0.0
        return features

    kpts = pose_seq[:, :, :2]
    confs = pose_seq[:, :, 2]
    valid = confs > 0.3

    # 1. ARM & RACKET-SWING FEATURES
    r_shoulder = kpts[:, KP['right_shoulder']]
    r_elbow = kpts[:, KP['right_elbow']]
    r_wrist = kpts[:, KP['right_wrist']]

    vec_shoulder_elbow = r_shoulder - r_elbow
    vec_wrist_elbow = r_wrist - r_elbow
    elbow_angles = np.array([angle_between(v1, v2) for v1, v2 in zip(vec_shoulder_elbow, vec_wrist_elbow)])
    mn, mx, mg, sd = safe_stats(elbow_angles)
    features['elbow_angle_mean'] = mg
    features['elbow_angle_min'] = mn
    features['elbow_angle_max'] = mx
    features['elbow_angle_std'] = sd

    mn, mx, mg, _ = safe_stats(r_wrist[:, 1])
    features['wrist_max_height'] = mn
    features['wrist_height_mean'] = mg

    arm_reach = np.linalg.norm(r_wrist - r_shoulder, axis=1)
    _, mx, mg, _ = safe_stats(arm_reach)
    features['arm_reach_max'] = mx
    features['arm_reach_mean'] = mg

    # 2. BODY POSTURE FEATURES
    shoulder_center = (kpts[:, KP['left_shoulder']] + kpts[:, KP['right_shoulder']]) / 2
    hip_center = (kpts[:, KP['left_hip']] + kpts[:, KP['right_hip']]) / 2
    torso_vec = shoulder_center - hip_center
    torso_angles = np.arctan2(torso_vec[:, 0], -torso_vec[:, 1]) * 180 / np.pi
    _, _, mg, sd = safe_stats(np.abs(torso_angles))
    features['torso_angle_mean'] = mg
    features['torso_angle_std'] = sd

    # Knee bend
    l_knee = kpts[:, KP['left_knee']]
    r_knee = kpts[:, KP['right_knee']]
    l_ankle = kpts[:, KP['left_ankle']]
    r_ankle = kpts[:, KP['right_ankle']]

    for side, hip, knee, ankle in [('left', kpts[:, KP['left_hip']], l_knee, l_ankle),
                                    ('right', kpts[:, KP['right_hip']], r_knee, r_ankle)]:
        vec_hip_knee = hip - knee
        vec_ankle_knee = ankle - knee
        knee_angles = np.array([angle_between(v1, v2) for v1, v2 in zip(vec_hip_knee, vec_ankle_knee)])
        mn, _, mg, _ = safe_stats(knee_angles)
        features[f'{side}_knee_angle_mean'] = mg
        features[f'{side}_knee_angle_min'] = mn

    # 3. FOOTWORK & MOVEMENT FEATURES
    l_ankle_diff = np.linalg.norm(np.diff(l_ankle, axis=0), axis=1)
    r_ankle_diff = np.linalg.norm(np.diff(r_ankle, axis=0), axis=1)
    l_ankle_disp = float(np.sum(l_ankle_diff)) if len(l_ankle_diff) > 0 else 0.0
    r_ankle_disp = float(np.sum(r_ankle_diff)) if len(r_ankle_diff) > 0 else 0.0
    features['left_foot_displacement'] = l_ankle_disp
    features['right_foot_displacement'] = r_ankle_disp
    features['total_foot_displacement'] = l_ankle_disp + r_ankle_disp

    foot_spread = np.linalg.norm(l_ankle - r_ankle, axis=1)
    mn, mx, mg, _ = safe_stats(foot_spread)
    features['foot_spread_mean'] = mg
    features['foot_spread_max'] = mx
    features['foot_spread_min'] = mn

    _, _, mg, sd = safe_stats(hip_center[:, 1])
    features['hip_height_mean'] = mg
    features['hip_height_std'] = sd

    # 4. DYNAMIC FEATURES
    for joint_name, joint_idx in [('wrist', KP['right_wrist']), ('elbow', KP['right_elbow'])]:
        joint = kpts[:, joint_idx]
        velocities = np.linalg.norm(np.diff(joint, axis=0), axis=1)
        _, mx, mg, sd = safe_stats(velocities)
        features[f'{joint_name}_velocity_mean'] = mg
        features[f'{joint_name}_velocity_max'] = mx
        features[f'{joint_name}_velocity_std'] = sd

    # 5. SEQUENCE STATISTICS
    features['sequence_length'] = T
    features['valid_frames'] = int(np.sum(np.any(valid, axis=1)))
    features['detection_rate'] = float(features['valid_frames'] / T) if T > 0 else 0.0

    return features


def process_all_features(pose_root, output_dir):
    """Extract features for all pose sequences and save as JSON."""
    pose_root = Path(pose_root)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    all_features = []
    category_dirs = sorted([d for d in pose_root.iterdir() if d.is_dir()])

    for cat_dir in tqdm(category_dirs, desc='Categories'):
        cat_name = cat_dir.name
        label = int(cat_name.split('_')[0])

        npy_files = sorted(cat_dir.glob('*_pose.npy'))
        for npy_file in tqdm(npy_files, desc=cat_name, leave=False):
            pose_seq = np.load(npy_file)
            feats = extract_badminton_features(pose_seq)
            feats['video_id'] = npy_file.stem.replace('_pose', '')
            feats['category'] = cat_name
            feats['label'] = label
            all_features.append(feats)

    output_file = output_dir / 'badminton_features.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_features, f, indent=2, ensure_ascii=False)

    print(f"Features extracted: {len(all_features)} videos")
    print(f"Saved to: {output_file}")
    return all_features


def main():
    parser = argparse.ArgumentParser(description='Extract badminton features from pose sequences')
    parser.add_argument('--pose-dir', type=str, default='E:/Learning/badminton-agent/data/pose_features')
    parser.add_argument('--output', type=str, default='E:/Learning/badminton-agent/data')
    args = parser.parse_args()

    process_all_features(args.pose_dir, args.output)


if __name__ == '__main__':
    main()
