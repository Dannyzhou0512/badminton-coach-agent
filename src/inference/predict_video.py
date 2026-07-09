"""
Run badminton action inference on a video or an extracted pose .npy file.

Examples:
  python src/inference/predict_video.py --pose-file data/pose_features/14_Smash/example_pose.npy
  python src/inference/predict_video.py --video demo.mp4 --output outputs/demo_report.json
"""

import argparse
import json
import shutil
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np
import torch

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = ImageDraw = ImageFont = None


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src" / "action_classification") not in sys.path:
    sys.path.insert(0, str(ROOT / "src" / "action_classification"))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from court.mapper import CourtMapper  # noqa: E402

from train_pose_sequence_classifier import (  # noqa: E402
    PoseTCNGRUClassifier,
    normalize_pose_sequence,
)


KP = {
    "left_shoulder": 5,
    "right_shoulder": 6,
    "left_elbow": 7,
    "right_elbow": 8,
    "left_wrist": 9,
    "right_wrist": 10,
    "left_hip": 11,
    "right_hip": 12,
    "left_ankle": 15,
    "right_ankle": 16,
}


@lru_cache(maxsize=2)
def cached_yolo_pose_model(pose_model_path):
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise RuntimeError("ultralytics is required for --video inference. Install project dependencies first.") from exc
    return YOLO(str(pose_model_path))

SKELETON = [
    (5, 7), (7, 9), (6, 8), (8, 10),
    (5, 6), (5, 11), (6, 12), (11, 12),
    (11, 13), (13, 15), (12, 14), (14, 16),
]


def load_model(checkpoint_path, device):
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)
    model = PoseTCNGRUClassifier(
        input_dim=int(checkpoint.get("input_dim", 85)),
        num_classes=int(checkpoint.get("num_classes", 18)),
        hidden_dim=int(checkpoint.get("hidden_dim", 128)),
        dropout=0.0,
    ).to(device)
    model.load_state_dict(checkpoint["model_state"])
    model.eval()

    label_names = {int(k): v for k, v in checkpoint.get("label_names", {}).items()}
    return model, checkpoint, label_names


def sample_frame_indices(total_frames, max_frames):
    if max_frames is None or total_frames <= max_frames:
        return None
    return set(np.linspace(0, total_frames - 1, max_frames, dtype=int).tolist())


def read_sampled_frames(video_path, max_frames=None, sample_stride=1):
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30

    if sample_stride > 1:
        target_indices = set(range(0, total_frames, sample_stride))
    elif max_frames is not None and total_frames > max_frames:
        target_indices = set(np.linspace(0, total_frames - 1, max_frames, dtype=int).tolist())
    else:
        target_indices = None

    frames = []
    original_indices = []
    frame_idx = 0

    while True:
        if target_indices is not None and frame_idx not in target_indices:
            ok = cap.grab()
            if not ok:
                break
            frame_idx += 1
            continue

        ok, frame = cap.read()
        if not ok:
            break
        frames.append(frame)
        original_indices.append(frame_idx)
        frame_idx += 1

    cap.release()

    if not frames:
        raise RuntimeError(f"No frames extracted from video: {video_path}")

    return frames, original_indices, fps


def read_all_video_frames(video_path):
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    frames = []
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frames.append(frame)
    cap.release()

    if not frames:
        raise RuntimeError(f"No frames extracted from video: {video_path}")
    return frames, fps


def extract_pose_from_video(
    video_path,
    pose_model_path,
    conf_threshold=0.3,
    max_frames=None,
    batch_size=64,
    target_player="near",
    target_point=None,
    target_roi=None,
    target_bbox=None,
    sample_stride=1,
):
    pose_seq, frames, original_indices, fps = extract_pose_and_frames_from_video(
        video_path,
        pose_model_path,
        conf_threshold=conf_threshold,
        max_frames=max_frames,
        batch_size=batch_size,
        target_player=target_player,
        target_point=target_point,
        target_roi=target_roi,
        target_bbox=target_bbox,
        sample_stride=sample_stride,
    )
    return pose_seq, original_indices, fps


def extract_pose_and_frames_from_video(
    video_path,
    pose_model_path,
    conf_threshold=0.3,
    max_frames=None,
    batch_size=64,
    target_player="near",
    target_point=None,
    target_roi=None,
    target_bbox=None,
    sample_stride=1,
):
    frames, original_indices, fps = read_sampled_frames(video_path, max_frames=max_frames, sample_stride=sample_stride)
    model = cached_yolo_pose_model(str(Path(pose_model_path).resolve()))
    yolo_device = "cuda" if torch.cuda.is_available() else "cpu"
    yolo_half = yolo_device == "cuda"
    print(f"[INFO] YOLO pose inference device={yolo_device}, half={yolo_half}, frames={len(frames)}, batch_size={batch_size}, sample_stride={sample_stride}")
    sequences = []
    previous_center = None
    frame_counter = 0
    for start in range(0, len(frames), batch_size):
        try:
            results = model(
                frames[start : start + batch_size],
                verbose=False,
                conf=conf_threshold,
                device=yolo_device,
                half=yolo_half,
            )
        except Exception:
            results = model(frames[start : start + batch_size], verbose=False, conf=conf_threshold)
        for result in results:
            keypoints, previous_center = result_to_keypoints(
                result,
                target_player=target_player,
                target_point=target_point,
                target_roi=target_roi,
                target_bbox=target_bbox,
                previous_center=previous_center if target_bbox is not None or frame_counter >= 8 else None,
            )
            sequences.append(keypoints)
            frame_counter += 1

    return np.asarray(sequences, dtype=np.float32), frames, original_indices, fps


def keypoint_center(xy, conf=None):
    if conf is not None:
        valid = conf > 0.2
        if np.any(valid):
            return np.mean(xy[valid], axis=0)
    return np.mean(xy, axis=0)


def person_anchor(xy, conf=None):
    foot_indices = [KP["left_ankle"], KP["right_ankle"]]
    if conf is not None:
        valid_feet = [idx for idx in foot_indices if conf[idx] > 0.2]
        if valid_feet:
            return np.mean(xy[valid_feet], axis=0)

        lower_body = [KP["left_hip"], KP["right_hip"]]
        valid_lower = [idx for idx in lower_body if conf[idx] > 0.2]
        if valid_lower:
            return np.mean(xy[valid_lower], axis=0)

    return keypoint_center(xy, conf)


def bbox_iou(box_a, box_b):
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b
    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)
    inter_w = max(0.0, inter_x2 - inter_x1)
    inter_h = max(0.0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - inter_area
    if union <= 0:
        return 0.0
    return float(inter_area / union)


def normalized_bbox_to_pixels(target_bbox, frame_w, frame_h):
    if target_bbox is None:
        return None
    x1, y1, x2, y2 = target_bbox
    x1, x2 = sorted((float(x1), float(x2)))
    y1, y2 = sorted((float(y1), float(y2)))
    x1 = np.clip(x1, 0.0, 1.0) * frame_w
    x2 = np.clip(x2, 0.0, 1.0) * frame_w
    y1 = np.clip(y1, 0.0, 1.0) * frame_h
    y2 = np.clip(y2, 0.0, 1.0) * frame_h
    return np.asarray([x1, y1, x2, y2], dtype=np.float32)


def select_person_index(result, target_player="near", previous_center=None, target_point=None, target_roi=None, target_bbox=None):
    if result.keypoints is None or len(result.keypoints) == 0:
        return None

    xy_all = result.keypoints.xy.cpu().numpy()
    conf_all = result.keypoints.conf.cpu().numpy()
    boxes_xyxy = result.boxes.xyxy.cpu().numpy() if result.boxes is not None and len(result.boxes) > 0 else None
    box_conf = result.boxes.conf.cpu().numpy() if result.boxes is not None and len(result.boxes) > 0 else np.ones(len(xy_all))

    centers = []
    anchors = []
    areas = []
    for idx, xy in enumerate(xy_all):
        centers.append(keypoint_center(xy, conf_all[idx]))
        anchors.append(person_anchor(xy, conf_all[idx]))
        if boxes_xyxy is not None and idx < len(boxes_xyxy):
            x1, y1, x2, y2 = boxes_xyxy[idx]
            areas.append(max(float((x2 - x1) * (y2 - y1)), 1.0))
        else:
            width = np.ptp(xy[:, 0])
            height = np.ptp(xy[:, 1])
            areas.append(max(float(width * height), 1.0))

    centers = np.asarray(centers, dtype=np.float32)
    anchors = np.asarray(anchors, dtype=np.float32)
    areas = np.asarray(areas, dtype=np.float32)
    area_norm = areas / max(float(np.max(areas)), 1.0)
    mode = (target_player or "near").lower()

    frame_h, frame_w = result.orig_shape[:2] if hasattr(result, "orig_shape") else (1, 1)
    frame_diag = max(float(np.linalg.norm([frame_w, frame_h])), 1.0)
    anchor_x = anchors[:, 0] / max(float(frame_w), 1.0)
    anchor_y = anchors[:, 1] / max(float(frame_h), 1.0)
    continuity = np.zeros(len(anchors), dtype=np.float32)
    if previous_center is not None:
        continuity = np.linalg.norm(anchors - previous_center, axis=1) / frame_diag
    roi_penalty = np.zeros(len(anchors), dtype=np.float32)
    if target_roi is not None:
        x1, y1, x2, y2 = target_roi
        inside = (anchor_x >= x1) & (anchor_x <= x2) & (anchor_y >= y1) & (anchor_y <= y2)
        roi_penalty = np.where(inside, 0.0, 1.0).astype(np.float32)

    if mode in {"manual_box", "bbox", "首帧目标框"} and target_bbox is not None:
        target_box = normalized_bbox_to_pixels(target_bbox, frame_w, frame_h)
        target_center = np.asarray(
            [(target_box[0] + target_box[2]) / 2.0, (target_box[1] + target_box[3]) / 2.0],
            dtype=np.float32,
        )
        target_dist = np.linalg.norm(anchors - target_center, axis=1) / frame_diag
        if boxes_xyxy is not None:
            ious = np.asarray(
                [
                    bbox_iou(boxes_xyxy[idx], target_box) if idx < len(boxes_xyxy) else 0.0
                    for idx in range(len(anchors))
                ],
                dtype=np.float32,
            )
        else:
            ious = np.zeros(len(anchors), dtype=np.float32)
        if previous_center is not None:
            scores = 0.72 * continuity + 0.20 * target_dist + 0.70 * roi_penalty - 0.10 * ious - 0.04 * area_norm
        else:
            scores = target_dist + 0.80 * roi_penalty - 0.35 * ious - 0.05 * area_norm - 0.03 * box_conf
        return int(np.argmin(scores))

    if mode in {"custom", "target", "自定义目标点"} and target_point is not None:
        target = np.asarray([target_point[0] * frame_w, target_point[1] * frame_h], dtype=np.float32)
        target_dist = np.linalg.norm(anchors - target, axis=1) / frame_diag
        scores = target_dist + 0.28 * continuity + 1.2 * roi_penalty - 0.04 * area_norm - 0.03 * box_conf
        return int(np.argmin(scores))

    if mode in {"left", "画面左侧"}:
        scores = anchor_x + 0.30 * continuity + 1.2 * roi_penalty - 0.04 * area_norm
        return int(np.argmin(scores))
    if mode in {"right", "画面右侧"}:
        scores = (1.0 - anchor_x) + 0.30 * continuity + 1.2 * roi_penalty - 0.04 * area_norm
        return int(np.argmin(scores))
    if mode in {"far", "top", "远端球员", "上半场"}:
        scores = anchor_y + 0.25 * continuity + 1.2 * roi_penalty - 0.03 * area_norm
        return int(np.argmin(scores))
    if mode in {"largest", "最大框"}:
        scores = (1.0 - area_norm) + 0.25 * continuity + 1.2 * roi_penalty - 0.03 * box_conf
        return int(np.argmin(scores))

    # Default for badminton broadcast/training videos: the tracked player is often
    # closer to camera, so the lower/larger person is the safer initial anchor.
    scores = (1.0 - anchor_y) + 0.25 * continuity + 1.2 * roi_penalty - 0.08 * area_norm - 0.03 * box_conf
    return int(np.argmin(scores))


def result_to_keypoints(result, target_player="near", previous_center=None, target_point=None, target_roi=None, target_bbox=None):
    best_idx = select_person_index(
        result,
        target_player=target_player,
        previous_center=previous_center,
        target_point=target_point,
        target_roi=target_roi,
        target_bbox=target_bbox,
    )
    if best_idx is None:
        return np.zeros((17, 3), dtype=np.float32), previous_center

    xy = result.keypoints.xy[best_idx].cpu().numpy()
    conf = result.keypoints.conf[best_idx].cpu().numpy()
    center = person_anchor(xy, conf)
    return np.concatenate([xy, conf[:, None]], axis=1).astype(np.float32), center


def predict_probabilities(model, checkpoint, pose_seq, device):
    seq_len = int(checkpoint.get("seq_len", 64))
    feature_set = checkpoint.get("feature_set", "base")
    features = normalize_pose_sequence(pose_seq, seq_len=seq_len, feature_set=feature_set)
    x = torch.from_numpy(features).unsqueeze(0).to(device)

    with torch.no_grad():
        logits = model(x)
        probs = torch.softmax(logits, dim=1)[0].cpu().numpy()
    return probs


def topk_from_probs(probs, topk=5):
    top_indices = probs.argsort()[::-1][:topk]
    return [(int(idx), float(probs[idx])) for idx in top_indices]


def predict_pose_sequence(model, checkpoint, pose_seq, device, topk=5):
    probs = predict_probabilities(model, checkpoint, pose_seq, device)
    return topk_from_probs(probs, topk=topk)


def predict_windows(model, checkpoint, pose_seq, device, window_size=64, stride=32, topk=3):
    if len(pose_seq) == 0:
        return [], None

    if len(pose_seq) <= window_size:
        probs = predict_probabilities(model, checkpoint, pose_seq, device)
        return [
            {
                "start": 0,
                "end": len(pose_seq),
                "top_predictions": topk_from_probs(probs, topk=topk),
            }
        ], probs

    windows = []
    probs_list = []
    starts = list(range(0, max(1, len(pose_seq) - window_size + 1), stride))
    if starts[-1] + window_size < len(pose_seq):
        starts.append(len(pose_seq) - window_size)

    for start in starts:
        end = min(len(pose_seq), start + window_size)
        probs = predict_probabilities(model, checkpoint, pose_seq[start:end], device)
        probs_list.append(probs)
        windows.append(
            {
                "start": int(start),
                "end": int(end),
                "top_predictions": topk_from_probs(probs, topk=topk),
            }
        )

    aggregate_probs = np.mean(np.stack(probs_list, axis=0), axis=0)
    return windows, aggregate_probs


def frame_window_labels(windows, num_frames):
    labels = [None] * num_frames
    for window in windows:
        label, confidence = window["top_predictions"][0]
        for idx in range(window["start"], min(window["end"], num_frames)):
            if labels[idx] is None or confidence > labels[idx][1]:
                labels[idx] = (label, confidence)
    return labels


def window_label_at_frame(windows, frame_idx):
    best = None
    for window in windows:
        if window["start"] <= frame_idx < window["end"]:
            label, confidence = window["top_predictions"][0]
            if best is None or confidence > best[1]:
                best = (label, confidence)
    return best


def map_sample_windows_to_original_frames(windows, sampled_indices, total_frames):
    if not windows:
        return []
    mapped = []
    last_frame = total_frames - 1
    for window in windows:
        start_sample = min(window["start"], len(sampled_indices) - 1)
        end_sample = min(max(window["end"] - 1, start_sample), len(sampled_indices) - 1)
        start_frame = int(sampled_indices[start_sample])
        end_frame = int(sampled_indices[end_sample]) + 1
        mapped.append(
            {
                "start": max(0, start_frame),
                "end": min(last_frame + 1, max(end_frame, start_frame + 1)),
                "top_predictions": window["top_predictions"],
            }
        )

    mapped[0]["start"] = 0
    mapped[-1]["end"] = total_frames
    for idx in range(1, len(mapped)):
        previous_end = mapped[idx - 1]["end"]
        if mapped[idx]["start"] > previous_end:
            mapped[idx]["start"] = previous_end
    return mapped


@lru_cache(maxsize=8)
def unicode_font(font_size):
    if ImageFont is None:
        return None
    font_candidates = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/simsun.ttc",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for font_path in font_candidates:
        if Path(font_path).exists():
            try:
                return ImageFont.truetype(font_path, font_size)
            except Exception:
                continue
    return ImageFont.load_default()


def draw_unicode_text(frame, text, origin, font_size=26, color=(255, 255, 255), cv_scale=0.8, thickness=2):
    if not text:
        return frame
    if all(ord(char) < 128 for char in str(text)) or Image is None or ImageDraw is None:
        cv2.putText(frame, str(text), origin, cv2.FONT_HERSHEY_SIMPLEX, cv_scale, color, thickness)
        return frame
    font = unicode_font(font_size)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(rgb)
    draw = ImageDraw.Draw(image)
    draw.text(origin, str(text), font=font, fill=(color[2], color[1], color[0]))
    return cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)


def draw_pose_on_frame(frame, keypoints, label_text=None, conf_threshold=0.3):
    output = frame.copy()
    for idx1, idx2 in SKELETON:
        if keypoints[idx1, 2] > conf_threshold and keypoints[idx2, 2] > conf_threshold:
            pt1 = (int(keypoints[idx1, 0]), int(keypoints[idx1, 1]))
            pt2 = (int(keypoints[idx2, 0]), int(keypoints[idx2, 1]))
            cv2.line(output, pt1, pt2, (0, 220, 255), 2)

    for idx in range(len(keypoints)):
        if keypoints[idx, 2] > conf_threshold:
            center = (int(keypoints[idx, 0]), int(keypoints[idx, 1]))
            cv2.circle(output, center, 4, (30, 220, 80), -1)
            cv2.circle(output, center, 4, (255, 255, 255), 1)

    if label_text:
        cv2.rectangle(output, (12, 12), (520, 66), (0, 0, 0), -1)
        output = draw_unicode_text(output, label_text, (24, 28), font_size=28, color=(255, 255, 255), cv_scale=0.85, thickness=2)
    return output


def draw_status_text(frame, text):
    if not text:
        return frame
    output = frame.copy()
    h, _ = output.shape[:2]
    cv2.rectangle(output, (12, h - 40), (320, h - 8), (0, 0, 0), -1)
    cv2.putText(output, text, (22, h - 17), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (230, 245, 255), 2)
    return output


def draw_hit_marker(frame, event_text):
    output = frame.copy()
    h, w = output.shape[:2]
    cv2.circle(output, (w - 70, 58), 22, (0, 80, 255), -1)
    cv2.circle(output, (w - 70, 58), 24, (255, 255, 255), 2)
    cv2.putText(output, "HIT", (w - 112, 108), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)
    if event_text:
        cv2.rectangle(output, (12, 72), (620, 118), (0, 0, 0), -1)
        output = draw_unicode_text(output, event_text, (24, 84), font_size=23, color=(255, 255, 255), cv_scale=0.72, thickness=2)
    return output


def footwork_centers(pose_seq, conf_threshold=0.3):
    centers = []
    for keypoints in pose_seq:
        left = keypoints[KP["left_ankle"]]
        right = keypoints[KP["right_ankle"]]
        if left[2] > conf_threshold and right[2] > conf_threshold:
            centers.append(((left[:2] + right[:2]) / 2.0).astype(np.float32))
        elif left[2] > conf_threshold:
            centers.append(left[:2].astype(np.float32))
        elif right[2] > conf_threshold:
            centers.append(right[:2].astype(np.float32))
        else:
            centers.append(None)
    return centers


def court_mapper(centers, panel_w, panel_h):
    valid = np.asarray([center for center in centers if center is not None], dtype=np.float32)
    margin_x = int(panel_w * 0.12)
    margin_y = int(panel_h * 0.08)
    court_left, court_top = margin_x, margin_y
    court_right, court_bottom = panel_w - margin_x, panel_h - margin_y

    if len(valid) < 2:
        def map_point(_point):
            return ((court_left + court_right) // 2, int(court_bottom * 0.72))
        return map_point

    mins = np.percentile(valid, 5, axis=0)
    maxs = np.percentile(valid, 95, axis=0)
    span = np.maximum(maxs - mins, 1.0)

    def map_point(point):
        normalized = np.clip((point - mins) / span, 0.0, 1.0)
        x = int(court_left + normalized[0] * (court_right - court_left))
        y = int(court_top + normalized[1] * (court_bottom - court_top))
        return x, y

    return map_point


def image_court_mapper(frame_size, court_rect):
    frame_w, frame_h = frame_size
    left, top, right, bottom = court_rect

    def map_point(point):
        x_norm = np.clip(float(point[0]) / max(float(frame_w), 1.0), 0.0, 1.0)
        y_norm = np.clip(float(point[1]) / max(float(frame_h), 1.0), 0.0, 1.0)
        x = int(left + x_norm * (right - left))
        y = int(top + y_norm * (bottom - top))
        return x, y

    return map_point


def calibrated_court_mapper(court_corners, frame_size, court_rect):
    frame_w, frame_h = frame_size
    left, top, right, bottom = court_rect
    source = np.asarray(
        [
            [court_corners["top_left"][0] * frame_w, court_corners["top_left"][1] * frame_h],
            [court_corners["top_right"][0] * frame_w, court_corners["top_right"][1] * frame_h],
            [court_corners["bottom_left"][0] * frame_w, court_corners["bottom_left"][1] * frame_h],
            [court_corners["bottom_right"][0] * frame_w, court_corners["bottom_right"][1] * frame_h],
        ],
        dtype=np.float32,
    )
    destination = np.asarray(
        [
            [left, top],
            [right, top],
            [left, bottom],
            [right, bottom],
        ],
        dtype=np.float32,
    )
    matrix = cv2.getPerspectiveTransform(source, destination)

    def map_point(point):
        src = np.asarray([[[float(point[0]), float(point[1])]]], dtype=np.float32)
        mapped = cv2.perspectiveTransform(src, matrix)[0, 0]
        x = int(np.clip(mapped[0], left, right))
        y = int(np.clip(mapped[1], top, bottom))
        return x, y

    return map_point


def filter_footwork_jumps(centers):
    valid = [center for center in centers if center is not None]
    if len(valid) < 4:
        return centers

    steps = []
    previous = None
    for center in centers:
        if center is None:
            continue
        if previous is not None:
            steps.append(float(np.linalg.norm(center - previous)))
        previous = center
    if not steps:
        return centers

    threshold = max(float(np.percentile(steps, 90)) * 3.0, 35.0)
    filtered = []
    previous = None
    for center in centers:
        if center is None:
            filtered.append(None)
            continue
        if previous is not None and float(np.linalg.norm(center - previous)) > threshold:
            filtered.append(None)
            continue
        filtered.append(center)
        previous = center
    return filtered


def _resolve_court_corners(court_corners, frame_size):
    """Convert various court corner formats to pixel coordinates for CourtMapper.

    Supports:
      - dict with keys top_left, top_right, bottom_left, bottom_right (normalized)
      - list/array of 4 points (normalized [tl,tr,bl,br] or pixel [tl,tr,br,bl])
    Returns a (4, 2) float32 array of pixel coordinates in [tl, tr, br, bl] order.
    """
    frame_w, frame_h = frame_size
    if isinstance(court_corners, dict):
        ordered = [
            court_corners["top_left"],
            court_corners["top_right"],
            court_corners["bottom_right"],
            court_corners["bottom_left"],
        ]
    else:
        ordered = list(court_corners)
        if len(ordered) == 4 and np.max(np.asarray(ordered, dtype=np.float32)) <= 1.0:
            # Normalized list follows dict key order [tl, tr, bl, br];
            # remap to CourtMapper's expected [tl, tr, br, bl].
            ordered = [ordered[0], ordered[1], ordered[3], ordered[2]]
    pts = np.asarray(ordered, dtype=np.float32)
    if pts.size == 0:
        return pts
    if np.max(pts) <= 1.0:
        pts = pts.copy()
        pts[:, 0] *= frame_w
        pts[:, 1] *= frame_h
    return pts


def draw_half_court_panel(centers, frame_idx, panel_size, heat_decay=0.95, court_corners=None, frame_size=None, map_mode="image"):
    panel_w, panel_h = panel_size
    panel = np.full((panel_h, panel_w, 3), (34, 116, 88), dtype=np.uint8)
    margin_x = int(panel_w * 0.12)
    margin_y = int(panel_h * 0.08)
    left, top = margin_x, margin_y
    right, bottom = panel_w - margin_x, panel_h - margin_y
    mid_y = top + int((bottom - top) * 0.48)
    service_y = top + int((bottom - top) * 0.68)
    mid_x = (left + right) // 2

    cv2.rectangle(panel, (left, top), (right, bottom), (236, 245, 238), 2)
    cv2.line(panel, (left, mid_y), (right, mid_y), (236, 245, 238), 2)
    cv2.line(panel, (left, service_y), (right, service_y), (236, 245, 238), 1)
    cv2.line(panel, (mid_x, mid_y), (mid_x, bottom), (236, 245, 238), 1)
    cv2.putText(panel, "Footwork Tracking", (left, max(28, top - 18)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    if court_corners is not None and frame_size is not None:
        pixel_corners = _resolve_court_corners(court_corners, frame_size)
        mapper = CourtMapper(pixel_corners)

        def map_point(point):
            phys = mapper.image_to_court(point)
            # Full court is 6.1m x 13.4m; display the lower half (6.1m x 6.7m).
            x = int(np.clip(left + (float(phys[0]) / 6.1) * (right - left), left, right))
            y = int(np.clip(top + ((float(phys[1]) - 6.7) / 6.7) * (bottom - top), top, bottom))
            return x, y

        cv2.putText(panel, "COURT MAPPER", (left, top + 26), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)
    elif map_mode == "image" and frame_size is not None:
        mapper = image_court_mapper(frame_size, (left, top, right, bottom))
        cv2.putText(panel, "IMAGE MAP", (left, top + 26), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 255, 220), 2)
    else:
        mapper = court_mapper(centers, panel_w, panel_h)
    heat = np.zeros((panel_h, panel_w), dtype=np.float32)
    trace = []
    first_idx = max(0, frame_idx - 180)
    for idx in range(first_idx, frame_idx + 1):
        center = centers[idx] if idx < len(centers) else None
        if center is None:
            continue
        point = mapper(center)
        trace.append(point)
        age = frame_idx - idx
        weight = heat_decay ** age
        cv2.circle(heat, point, max(8, panel_w // 32), float(weight), -1)

    if float(np.max(heat)) > 0:
        heat_norm = np.clip(heat / np.max(heat) * 255.0, 0, 255).astype(np.uint8)
        heat_color = cv2.applyColorMap(heat_norm, cv2.COLORMAP_JET)
        mask = heat_norm > 8
        panel[mask] = cv2.addWeighted(panel, 0.48, heat_color, 0.52, 0)[mask]

    for p1, p2 in zip(trace[-80:-1], trace[-79:]):
        cv2.line(panel, p1, p2, (255, 255, 255), 2)

    if trace:
        cv2.circle(panel, trace[-1], 9, (0, 255, 255), -1)
        cv2.circle(panel, trace[-1], 14, (255, 255, 255), 2)
        cv2.putText(panel, "LIVE", (left, bottom + min(38, panel_h - bottom - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)
    else:
        cv2.putText(panel, "No foot detected", (left, bottom + min(38, panel_h - bottom - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (210, 230, 230), 2)

    return panel


def _try_opencv_h264_transcode(input_path, output_path):
    """Fallback transcode using OpenCV's avc1 fourcc when ffmpeg is unavailable."""
    cap = cv2.VideoCapture(str(input_path))
    if not cap.isOpened():
        raise RuntimeError("Cannot open input video for OpenCV transcode")

    fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 640)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 480)
    # H.264 requires even dimensions.
    width = width if width % 2 == 0 else width + 1
    height = height if height % 2 == 0 else height + 1

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = output_path.with_name(f"{output_path.stem}_h264.mp4")
    writer = cv2.VideoWriter(
        str(temp_path),
        cv2.VideoWriter_fourcc(*"avc1"),
        max(fps, 1.0),
        (width, height),
    )
    if not writer.isOpened():
        cap.release()
        raise RuntimeError("OpenCV cannot write H.264 (avc1) on this system")

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if frame.shape[1] != width or frame.shape[0] != height:
                frame = cv2.resize(frame, (width, height))
            writer.write(frame)
    finally:
        writer.release()
        cap.release()

    if not temp_path.exists() or temp_path.stat().st_size < 1024:
        raise RuntimeError("OpenCV H.264 transcode produced an empty file")

    temp_path.replace(output_path)
    return output_path


def _nvenc_available(ffmpeg):
    try:
        result = subprocess.run(
            [ffmpeg, "-h", "encoder=h264_nvenc"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return result.returncode == 0
    except Exception:
        return False


def transcode_for_browser(input_path, output_path, allow_nvenc=True):
    """Transcode a video to browser-playable H.264/mp4.

    Prefers ffmpeg with NVENC hardware encoding when available; falls back to
    libx264 software encoding; finally falls back to OpenCV avc1.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")

    if ffmpeg is None:
        return _try_opencv_h264_transcode(input_path, output_path)

    use_nvenc = allow_nvenc and _nvenc_available(ffmpeg)
    if use_nvenc:
        cmd = [
            ffmpeg,
            "-y",
            "-i",
            str(input_path),
            "-vf",
            "scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p",
            "-c:v",
            "h264_nvenc",
            "-preset",
            "p1",
            "-tune",
            "hq",
            "-cq",
            "26",
            "-b:v",
            "0",
            "-pix_fmt",
            "yuv420p",
            "-tag:v",
            "avc1",
            "-movflags",
            "+faststart",
            "-an",
            str(output_path),
        ]
    else:
        cmd = [
            ffmpeg,
            "-y",
            "-i",
            str(input_path),
            "-vf",
            "scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p",
            "-c:v",
            "libx264",
            "-profile:v",
            "baseline",
            "-level",
            "4.0",
            "-preset",
            "ultrafast",
            "-crf",
            "26",
            "-x264-params",
            "bframes=0:cabac=0:ref=1",
            "-pix_fmt",
            "yuv420p",
            "-tag:v",
            "avc1",
            "-movflags",
            "+faststart",
            "-an",
            str(output_path),
        ]
    result = subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        if use_nvenc:
            print(f"[WARN] NVENC transcode failed, falling back to libx264: {(result.stderr or '').strip()[-400:]}")
            return transcode_for_browser(input_path, output_path, allow_nvenc=False)
        raise RuntimeError(f"ffmpeg transcode failed: {(result.stderr or '').strip()[-800:]}")
    print(f"[INFO] Transcoded with {'NVENC' if use_nvenc else 'libx264'}: {input_path.name} -> {output_path.name}")
    if ffprobe is not None:
        probe = subprocess.run(
            [
                ffprobe,
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=codec_name,pix_fmt,duration",
                "-of",
                "default=noprint_wrappers=1",
                str(output_path),
            ],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if probe.returncode != 0 or "codec_name=h264" not in probe.stdout:
            raise RuntimeError(f"ffprobe validation failed: {(probe.stderr or probe.stdout or '').strip()[-800:]}")
    return output_path


def write_annotated_video(
    frames,
    pose_seq,
    windows,
    label_names,
    output_path,
    fps=30,
    conf_threshold=0.3,
    hit_events=None,
    status_text=None,
):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not frames:
        raise RuntimeError("No frames available for annotation")

    h, w = frames[0].shape[:2]
    temp_path = output_path.with_name(f"{output_path.stem}_raw.mp4")
    writer = cv2.VideoWriter(str(temp_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    labels = frame_window_labels(windows, len(frames))
    event_lookup = {}
    for event in hit_events or []:
        event_lookup[int(event["frame"])] = event

    for idx, frame in enumerate(frames):
        label_info = labels[idx] if idx < len(labels) else None
        label_text = None
        if label_info is not None:
            label, confidence = label_info
            class_name = clean_class_name(label_names.get(label, str(label)))
            label_text = f"{class_name}  {confidence:.2f}"
        annotated = draw_pose_on_frame(frame, pose_seq[idx], label_text=label_text, conf_threshold=conf_threshold)
        annotated = draw_status_text(annotated, status_text)
        if idx in event_lookup:
            event = event_lookup[idx]
            if event.get("shot_action"):
                event_text = f"Shot #{event.get('index')}  {event['shot_action']}  {event.get('shot_confidence', 0):.2f}  {event.get('quality_level', '')}"
            else:
                event_text = f"Hit event  speed={event['wrist_speed']:.2f}"
            annotated = draw_hit_marker(annotated, event_text)
        writer.write(annotated)
    writer.release()

    try:
        transcode_for_browser(temp_path, output_path)
        if temp_path != output_path and temp_path.exists():
            temp_path.unlink()
    except Exception:
        if temp_path != output_path:
            temp_path.replace(output_path)

    return output_path


def write_tracking_video(
    frames,
    pose_seq,
    windows,
    label_names,
    output_path,
    fps=30,
    conf_threshold=0.3,
    hit_events=None,
    status_text=None,
    court_corners=None,
    footwork_map_mode="image",
):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not frames:
        raise RuntimeError("No frames available for tracking video")

    h, w = frames[0].shape[:2]
    panel_w = max(360, int(h * 0.62))
    if (w + panel_w) % 2 != 0:
        panel_w += 1
    temp_path = output_path.with_name(f"{output_path.stem}_raw.mp4")
    writer = cv2.VideoWriter(str(temp_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w + panel_w, h))
    labels = frame_window_labels(windows, len(frames))
    centers = filter_footwork_jumps(footwork_centers(pose_seq, conf_threshold=conf_threshold))
    event_lookup = {int(event["frame"]): event for event in hit_events or []}
    normalized_corners = _resolve_court_corners(court_corners, (w, h)) if court_corners is not None else None

    for idx, frame in enumerate(frames):
        label_info = labels[idx] if idx < len(labels) else None
        label_text = None
        if label_info is not None:
            label, confidence = label_info
            class_name = clean_class_name(label_names.get(label, str(label)))
            label_text = f"{class_name}  {confidence:.2f}"
        annotated = draw_pose_on_frame(frame, pose_seq[idx], label_text=label_text, conf_threshold=conf_threshold)
        annotated = draw_status_text(annotated, status_text)
        if idx in event_lookup:
            event = event_lookup[idx]
            if event.get("shot_action"):
                event_text = f"Shot #{event.get('index')}  {event['shot_action']}  {event.get('shot_confidence', 0):.2f}  {event.get('quality_level', '')}"
            else:
                event_text = f"Hit event  speed={event['wrist_speed']:.2f}"
            annotated = draw_hit_marker(annotated, event_text)
        panel = draw_half_court_panel(
            centers,
            idx,
            (panel_w, h),
            court_corners=normalized_corners,
            frame_size=(w, h),
            map_mode=footwork_map_mode,
        )
        writer.write(np.hstack([annotated, panel]))
    writer.release()

    try:
        transcode_for_browser(temp_path, output_path)
        if temp_path != output_path and temp_path.exists():
            temp_path.unlink()
    except Exception:
        if temp_path != output_path:
            temp_path.replace(output_path)

    return output_path


def expand_sampled_pose_to_full(sampled_pose_seq, sampled_indices, total_frames):
    if len(sampled_pose_seq) != len(sampled_indices):
        raise ValueError("sampled_pose_seq and sampled_indices must have the same length")

    if len(sampled_indices) == 0:
        return np.zeros((total_frames, 17, 3), dtype=np.float32)

    sampled_indices_arr = np.asarray(sampled_indices, dtype=np.int64)
    first_idx = int(sampled_indices_arr[0])
    last_idx = int(sampled_indices_arr[-1])

    full_pose_seq = np.empty((total_frames, 17, 3), dtype=np.float32)
    full_pose_seq[:first_idx] = sampled_pose_seq[0]
    full_pose_seq[last_idx:] = sampled_pose_seq[-1]

    if first_idx >= last_idx:
        return full_pose_seq

    frame_indices = np.arange(first_idx, last_idx + 1, dtype=np.int64)
    right_pos = np.searchsorted(sampled_indices_arr, frame_indices, side='right')
    right_pos = np.clip(right_pos, 1, len(sampled_indices_arr) - 1)
    left_pos = right_pos - 1

    left_sample_indices = sampled_indices_arr[left_pos]
    right_sample_indices = sampled_indices_arr[right_pos]

    alpha = (frame_indices - left_sample_indices) / (right_sample_indices - left_sample_indices).astype(np.float32)
    alpha = alpha[:, None, None]

    left_poses = sampled_pose_seq[left_pos]
    right_poses = sampled_pose_seq[right_pos]

    full_pose_seq[first_idx:last_idx + 1] = (1.0 - alpha) * left_poses + alpha * right_poses

    return full_pose_seq


def map_sample_events_to_original_frames(hit_events, sampled_indices, fps):
    mapped_events = []
    if not sampled_indices:
        return mapped_events
    for event in hit_events or []:
        sample_idx = min(max(int(event["frame"]), 0), len(sampled_indices) - 1)
        mapped = dict(event)
        mapped["sample_frame"] = int(event["frame"])
        mapped["frame"] = int(sampled_indices[sample_idx])
        mapped["time_sec"] = round(float(mapped["frame"] / fps), 3)
        mapped_events.append(mapped)
    return mapped_events


def write_full_length_annotated_video(
    video_path,
    sampled_pose_seq,
    sampled_indices,
    windows,
    label_names,
    output_path,
    conf_threshold=0.3,
    hit_events=None,
    status_text=None,
    max_height=720,
    output_fps=None,
):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = shutil.which("ffmpeg")

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
    orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 640)
    orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 480)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    scale = min(1.0, max_height / float(orig_h)) if max_height else 1.0
    out_w = int(orig_w * scale)
    out_h = int(orig_h * scale)
    out_w = out_w if out_w % 2 == 0 else out_w + 1
    out_h = out_h if out_h % 2 == 0 else out_h + 1

    render_stride = 1
    if output_fps is not None:
        try:
            requested_fps = float(output_fps)
            if requested_fps > 0 and requested_fps < fps:
                render_stride = max(1, int(round(fps / requested_fps)))
        except (TypeError, ValueError):
            render_stride = 1
    render_fps = fps / float(render_stride)

    sampled_indices_list = list(sampled_indices)
    full_pose_seq = expand_sampled_pose_to_full(sampled_pose_seq, sampled_indices_list, total_frames)
    mapped_windows = map_sample_windows_to_original_frames(windows, sampled_indices_list, total_frames)
    mapped_events = map_sample_events_to_original_frames(hit_events, sampled_indices_list, fps)
    labels = frame_window_labels(mapped_windows, total_frames)
    event_lookup = {int(event["frame"]): event for event in mapped_events or []}

    pose_scale_x = out_w / float(orig_w) if orig_w > 0 else 1.0
    pose_scale_y = out_h / float(orig_h) if orig_h > 0 else 1.0

    use_nvenc = ffmpeg is not None and _nvenc_available(ffmpeg)

    if ffmpeg is not None:
        if use_nvenc:
            cmd = [
                ffmpeg, "-y",
                "-f", "rawvideo",
                "-vcodec", "rawvideo",
                "-s", f"{out_w}x{out_h}",
                "-pix_fmt", "bgr24",
                "-r", str(render_fps),
                "-i", "-",
                "-c:v", "h264_nvenc",
                "-preset", "p1",
                "-tune", "hq",
                "-cq", "26",
                "-b:v", "0",
                "-pix_fmt", "yuv420p",
                "-tag:v", "avc1",
                "-movflags", "+faststart",
                "-an",
                str(output_path),
            ]
        else:
            cmd = [
                ffmpeg, "-y",
                "-f", "rawvideo",
                "-vcodec", "rawvideo",
                "-s", f"{out_w}x{out_h}",
                "-pix_fmt", "bgr24",
                "-r", str(render_fps),
                "-i", "-",
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-crf", "26",
                "-pix_fmt", "yuv420p",
                "-tag:v", "avc1",
                "-movflags", "+faststart",
                "-an",
                str(output_path),
            ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        writer = proc.stdin
    else:
        temp_path = output_path.with_name(f"{output_path.stem}_raw.mp4")
        writer_obj = cv2.VideoWriter(str(temp_path), cv2.VideoWriter_fourcc(*"mp4v"), render_fps, (out_w, out_h))
        proc = None

    try:
        for frame_idx in range(total_frames):
            if render_stride > 1 and frame_idx % render_stride != 0:
                if not cap.grab():
                    break
                continue
            ok, frame = cap.read()
            if not ok:
                break
            if out_w != orig_w or out_h != orig_h:
                frame = cv2.resize(frame, (out_w, out_h), interpolation=cv2.INTER_AREA)

            keypoints = full_pose_seq[frame_idx].copy()
            keypoints[:, 0] *= pose_scale_x
            keypoints[:, 1] *= pose_scale_y

            label_info = labels[frame_idx] if frame_idx < len(labels) else None
            label_text = None
            if label_info is not None:
                label, confidence = label_info
                class_name = clean_class_name(label_names.get(label, str(label)))
                label_text = f"{class_name}  {confidence:.2f}"

            annotated = draw_pose_on_frame(frame, keypoints, label_text=label_text, conf_threshold=conf_threshold)
            annotated = draw_status_text(annotated, status_text)

            if frame_idx in event_lookup:
                event = event_lookup[frame_idx]
                if event.get("shot_action"):
                    event_text = f"Shot #{event.get('index')}  {event['shot_action']}  {event.get('shot_confidence', 0):.2f}  {event.get('quality_level', '')}"
                else:
                    event_text = f"Hit event  speed={event['wrist_speed']:.2f}"
                annotated = draw_hit_marker(annotated, event_text)

            if proc is not None:
                writer.write(annotated.tobytes())
            else:
                writer_obj.write(annotated)
    finally:
        cap.release()
        if proc is not None:
            writer.close()
            proc.wait()
        else:
            writer_obj.release()

    if ffmpeg is None:
        try:
            transcode_for_browser(temp_path, output_path)
            if temp_path.exists():
                temp_path.unlink()
        except Exception:
            if temp_path.exists():
                temp_path.replace(output_path)

    if use_nvenc or ffmpeg is None:
        print(f"[INFO] Annotated video encoded with {'NVENC pipe' if use_nvenc else 'OpenCV fallback'}: {output_path.name}")
    if render_stride > 1:
        print(f"[INFO] Annotated video render fps={render_fps:.2f}, stride={render_stride}, source fps={fps:.2f}")

    return output_path


def write_full_length_tracking_video(
    video_path,
    sampled_pose_seq,
    sampled_indices,
    windows,
    label_names,
    output_path,
    conf_threshold=0.3,
    hit_events=None,
    status_text=None,
    court_corners=None,
    footwork_map_mode="image",
):
    frames, fps = read_all_video_frames(video_path)
    total_frames = len(frames)
    if court_corners is None:
        from src.court.detector import auto_detect_court_corners
        corners, _mask, _debug = auto_detect_court_corners(frames[0])
        if corners is not None:
            court_corners = corners
    sampled_indices = list(sampled_indices)
    full_pose_seq = expand_sampled_pose_to_full(sampled_pose_seq, sampled_indices, total_frames)
    mapped_windows = map_sample_windows_to_original_frames(windows, sampled_indices, total_frames)
    mapped_events = map_sample_events_to_original_frames(hit_events, sampled_indices, fps)
    return write_tracking_video(
        frames,
        full_pose_seq,
        mapped_windows,
        label_names,
        output_path,
        fps=float(fps),
        conf_threshold=conf_threshold,
        hit_events=mapped_events,
        status_text=status_text,
        court_corners=court_corners,
        footwork_map_mode=footwork_map_mode,
    )


def write_shot_clips(video_path, shot_events, output_dir, pre_roll=0.15, post_roll=0.15):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    if not shot_events:
        return []

    frames, fps = read_all_video_frames(video_path)
    h, w = frames[0].shape[:2]
    written = []
    for event in shot_events:
        start_sec = max(0.0, float(event.get("clip_start_sec", event.get("time_sec", 0.0))) - pre_roll)
        end_sec = min(len(frames) / float(fps), float(event.get("clip_end_sec", event.get("time_sec", 0.0))) + post_roll)
        start_frame = max(0, int(start_sec * fps))
        end_frame = min(len(frames), max(start_frame + 1, int(end_sec * fps)))
        action = str(event.get("shot_action") or event.get("predicted_action") or "Shot").replace(" ", "_")
        output_path = output_dir / f"shot_{int(event.get('index', len(written) + 1)):02d}_{action}.mp4"
        temp_path = output_path.with_name(f"{output_path.stem}_raw.mp4")
        writer = cv2.VideoWriter(str(temp_path), cv2.VideoWriter_fourcc(*"mp4v"), float(fps), (w, h))
        title = f"Shot #{event.get('index')} | {event.get('shot_action') or event.get('predicted_action')} | {event.get('shot_confidence', event.get('confidence', 0.0)):.2f}"
        for frame in frames[start_frame:end_frame]:
            annotated = frame.copy()
            cv2.rectangle(annotated, (12, 12), (min(w - 12, 680), 62), (0, 0, 0), -1)
            cv2.putText(annotated, title, (24, 47), cv2.FONT_HERSHEY_SIMPLEX, 0.82, (255, 255, 255), 2)
            writer.write(annotated)
        writer.release()
        try:
            transcode_for_browser(temp_path, output_path)
            if temp_path != output_path and temp_path.exists():
                temp_path.unlink()
        except Exception:
            if temp_path != output_path:
                temp_path.replace(output_path)
        clip_info = dict(event)
        clip_info["clip_video"] = str(output_path)
        written.append(clip_info)
    return written


def angle_between(v1, v2):
    denom = np.linalg.norm(v1) * np.linalg.norm(v2)
    if denom < 1e-8:
        return 0.0
    cos = float(np.dot(v1, v2) / denom)
    return float(np.degrees(np.arccos(np.clip(cos, -1.0, 1.0))))


def compute_motion_summary(pose_seq, conf_threshold=0.3):
    xy = pose_seq[:, :, :2]
    conf = pose_seq[:, :, 2]
    valid_frames = np.any(conf > conf_threshold, axis=1)
    detection_rate = float(np.mean(valid_frames)) if len(valid_frames) else 0.0

    left_hip = xy[:, KP["left_hip"]]
    right_hip = xy[:, KP["right_hip"]]
    hip_center = (left_hip + right_hip) / 2.0
    left_shoulder = xy[:, KP["left_shoulder"]]
    right_shoulder = xy[:, KP["right_shoulder"]]
    shoulder_width = np.linalg.norm(left_shoulder - right_shoulder, axis=1)
    body_scale = float(np.nanmedian(shoulder_width))
    if not np.isfinite(body_scale) or body_scale < 1.0:
        body_scale = 1.0

    wrists = {
        "left": xy[:, KP["left_wrist"]],
        "right": xy[:, KP["right_wrist"]],
    }
    wrist_speeds = {
        side: np.linalg.norm(np.diff(points / body_scale, axis=0, prepend=points[:1] / body_scale), axis=1)
        for side, points in wrists.items()
    }
    dominant_side = max(wrist_speeds, key=lambda side: float(np.max(wrist_speeds[side])))
    wrist = wrists[dominant_side]
    wrist_speed = wrist_speeds[dominant_side]

    shoulder = xy[:, KP[f"{dominant_side}_shoulder"]]
    elbow = xy[:, KP[f"{dominant_side}_elbow"]]
    elbow_angles = np.array(
        [angle_between(s - e, w - e) for s, e, w in zip(shoulder, elbow, wrist)],
        dtype=np.float32,
    )

    ankle_center = (xy[:, KP["left_ankle"]] + xy[:, KP["right_ankle"]]) / 2.0
    footwork_distance = float(np.sum(np.linalg.norm(np.diff(ankle_center / body_scale, axis=0), axis=1)))
    hip_motion = float(np.sum(np.linalg.norm(np.diff(hip_center / body_scale, axis=0), axis=1)))
    wrist_above_shoulder = (shoulder[:, 1] - wrist[:, 1]) / body_scale

    return {
        "frames": int(len(pose_seq)),
        "valid_frames": int(np.sum(valid_frames)),
        "detection_rate": detection_rate,
        "dominant_side": dominant_side,
        "max_wrist_speed": float(np.max(wrist_speed)) if len(wrist_speed) else 0.0,
        "mean_wrist_speed": float(np.mean(wrist_speed)) if len(wrist_speed) else 0.0,
        "max_wrist_above_shoulder": float(np.max(wrist_above_shoulder)) if len(wrist_above_shoulder) else 0.0,
        "mean_elbow_angle": float(np.mean(elbow_angles)) if len(elbow_angles) else 0.0,
        "min_elbow_angle": float(np.min(elbow_angles)) if len(elbow_angles) else 0.0,
        "footwork_distance": footwork_distance,
        "hip_motion": hip_motion,
    }


def estimate_body_scale(xy):
    shoulder_width = np.linalg.norm(xy[:, KP["left_shoulder"]] - xy[:, KP["right_shoulder"]], axis=1)
    hip_width = np.linalg.norm(xy[:, KP["left_hip"]] - xy[:, KP["right_hip"]], axis=1)
    body_scale = float(np.nanmedian(np.maximum(shoulder_width, hip_width)))
    if not np.isfinite(body_scale) or body_scale < 1.0:
        body_scale = 1.0
    return body_scale


def dominant_wrist_track(pose_seq):
    xy = pose_seq[:, :, :2]
    body_scale = estimate_body_scale(xy)
    left = xy[:, KP["left_wrist"]]
    right = xy[:, KP["right_wrist"]]
    left_speed = np.linalg.norm(np.diff(left / body_scale, axis=0, prepend=left[:1] / body_scale), axis=1)
    right_speed = np.linalg.norm(np.diff(right / body_scale, axis=0, prepend=right[:1] / body_scale), axis=1)
    if float(np.max(right_speed)) >= float(np.max(left_speed)):
        return "right", right, right_speed, body_scale
    return "left", left, left_speed, body_scale


def detect_hit_events(pose_seq, windows=None, label_names=None, fps=30.0, min_gap_seconds=0.45):
    if len(pose_seq) < 3:
        return []

    side, wrist, wrist_speed, body_scale = dominant_wrist_track(pose_seq)
    xy = pose_seq[:, :, :2]
    shoulder = xy[:, KP[f"{side}_shoulder"]]
    wrist_above_shoulder = (shoulder[:, 1] - wrist[:, 1]) / body_scale

    threshold = max(float(np.mean(wrist_speed) + 0.9 * np.std(wrist_speed)), float(np.percentile(wrist_speed, 75)))
    min_gap = max(1, int(min_gap_seconds * fps))
    candidates = []

    for idx in range(1, len(wrist_speed) - 1):
        is_peak = wrist_speed[idx] >= wrist_speed[idx - 1] and wrist_speed[idx] >= wrist_speed[idx + 1]
        if is_peak and wrist_speed[idx] >= threshold:
            candidates.append(idx)

    selected = []
    for idx in sorted(candidates, key=lambda i: wrist_speed[i], reverse=True):
        if all(abs(idx - existing) >= min_gap for existing in selected):
            selected.append(idx)
    selected.sort()

    events = []
    for number, frame_idx in enumerate(selected, start=1):
        label_info = window_label_at_frame(windows or [], frame_idx)
        label = None
        action = None
        confidence = None
        if label_info is not None:
            label, confidence = label_info
            action = clean_class_name((label_names or {}).get(label, str(label)))
        events.append(
            {
                "index": number,
                "frame": int(frame_idx),
                "time_sec": round(float(frame_idx / fps), 3),
                "dominant_side": side,
                "wrist_speed": round(float(wrist_speed[frame_idx]), 6),
                "wrist_above_shoulder": round(float(wrist_above_shoulder[frame_idx]), 6),
                "predicted_label": label,
                "predicted_action": action,
                "confidence": round(float(confidence), 6) if confidence is not None else None,
            }
        )
    return events


def classify_hit_events(
    model,
    checkpoint,
    pose_seq,
    events,
    label_names,
    device,
    fps=30.0,
    pre_seconds=0.45,
    post_seconds=0.55,
    topk=3,
):
    if not events:
        return []

    pre_frames = max(1, int(pre_seconds * fps))
    post_frames = max(1, int(post_seconds * fps))
    classified = []
    for event in events:
        frame_idx = int(event["frame"])
        start = max(0, frame_idx - pre_frames)
        end = min(len(pose_seq), frame_idx + post_frames + 1)
        if end <= start:
            continue

        probs = predict_probabilities(model, checkpoint, pose_seq[start:end], device)
        predictions = topk_from_probs(probs, topk=topk)
        label, confidence = predictions[0]
        quality = analyze_shot_quality(pose_seq, frame_idx, start, end, fps=fps)
        enriched = dict(event)
        enriched.update(
            {
                "clip_start_frame": int(start),
                "clip_end_frame": int(end),
                "clip_start_sec": round(float(start / fps), 3),
                "clip_end_sec": round(float(end / fps), 3),
                "shot_label": int(label),
                "shot_action": clean_class_name(label_names.get(label, str(label))),
                "shot_confidence": round(float(confidence), 6),
                "quality_score": quality["quality_score"],
                "quality_level": quality["quality_level"],
                "quality_metrics": quality["metrics"],
                "quality_issues": quality["issues"],
                "quality_advice": quality["advice"],
                "shot_top_predictions": [
                    {
                        "label": int(item_label),
                        "action": clean_class_name(label_names.get(item_label, str(item_label))),
                        "confidence": round(float(item_conf), 6),
                    }
                    for item_label, item_conf in predictions
                ],
            }
        )
        classified.append(enriched)
    return classified


def score_from_range(value, low, high):
    if high <= low:
        return 50.0
    return clamp_score((float(value) - low) / (high - low) * 100.0)


def analyze_shot_quality(pose_seq, frame_idx, start, end, fps=30.0):
    clip = pose_seq[start:end]
    if len(clip) < 2:
        return {
            "quality_score": 0.0,
            "quality_level": "数据不足",
            "metrics": {},
            "issues": ["姿态片段太短"],
            "advice": ["建议使用更完整的击球片段重新分析。"],
        }

    xy = pose_seq[:, :, :2]
    body_scale = estimate_body_scale(xy)
    side, wrist, wrist_speed, _ = dominant_wrist_track(pose_seq)
    local_start = max(0, start)
    local_end = min(len(pose_seq), end)
    hit_frame = min(max(frame_idx, 0), len(pose_seq) - 1)

    shoulder = xy[:, KP[f"{side}_shoulder"]]
    wrist_above_shoulder = (shoulder[:, 1] - wrist[:, 1]) / body_scale
    hit_height = float(wrist_above_shoulder[hit_frame])
    peak_wrist_speed = float(np.max(wrist_speed[local_start:local_end])) if local_end > local_start else 0.0

    ankles = (xy[:, KP["left_ankle"]] + xy[:, KP["right_ankle"]]) / 2.0 / body_scale
    hips = (xy[:, KP["left_hip"]] + xy[:, KP["right_hip"]]) / 2.0 / body_scale
    foot_path = float(np.sum(np.linalg.norm(np.diff(ankles[local_start:local_end], axis=0), axis=1))) if local_end - local_start > 1 else 0.0
    hip_jitter = float(np.std(np.linalg.norm(np.diff(hips[local_start:local_end], axis=0), axis=1))) if local_end - local_start > 2 else 0.0

    post_end = min(len(pose_seq), hit_frame + max(2, int(0.45 * fps)))
    recovery_distance = 0.0
    if post_end > hit_frame + 1:
        recovery_distance = float(np.linalg.norm(ankles[post_end - 1] - ankles[hit_frame]))

    metrics = {
        "hit_height": round(hit_height, 4),
        "peak_wrist_speed": round(peak_wrist_speed, 4),
        "footwork_path": round(foot_path, 4),
        "hip_jitter": round(hip_jitter, 4),
        "recovery_distance": round(recovery_distance, 4),
    }

    height_score = score_from_range(hit_height, -0.15, 0.65)
    speed_score = score_from_range(peak_wrist_speed, 0.15, 1.1)
    stability_score = clamp_score(100.0 - hip_jitter * 180.0)
    recovery_score = clamp_score(100.0 - recovery_distance * 90.0)
    footwork_score = score_from_range(foot_path, 0.08, 1.3)
    quality_score = round(float(np.mean([height_score, speed_score, stability_score, recovery_score, footwork_score])), 1)

    issues = []
    advice = []
    if hit_height < 0.15:
        issues.append("击球点偏低")
        advice.append("提前启动到位，争取在身体前上方完成击球。")
    if peak_wrist_speed < 0.35:
        issues.append("挥拍加速不足")
        advice.append("练习放松引拍后快速加速，重点体会击球瞬间发力。")
    if recovery_distance > 0.75:
        issues.append("击球后回位慢")
        advice.append("击球后第一步立即回中，加入多球回位训练。")
    if hip_jitter > 0.18:
        issues.append("重心稳定性不足")
        advice.append("降低重心，击球前保持髋部稳定，减少上半身晃动。")
    if foot_path < 0.12:
        issues.append("脚步启动不明显")
        advice.append("加入分腿垫步和启动步练习，避免原地伸手够球。")

    if not issues:
        issues.append("整体动作质量较稳定")
        advice.append("继续保持当前动作节奏，可增加连续多拍稳定性训练。")

    if quality_score >= 80:
        level = "优秀"
    elif quality_score >= 65:
        level = "良好"
    elif quality_score >= 50:
        level = "一般"
    else:
        level = "需改进"

    return {
        "quality_score": quality_score,
        "quality_level": level,
        "metrics": metrics,
        "issues": issues,
        "advice": advice[:3],
    }


def clamp_score(value):
    return float(np.clip(value, 0.0, 100.0))


def compute_footwork_scores(pose_seq):
    if len(pose_seq) < 2:
        return {
            "movement": 0.0,
            "explosiveness": 0.0,
            "stability": 0.0,
            "recovery": 0.0,
            "coverage": 0.0,
            "balance": 0.0,
            "coordination": 0.0,
        }

    xy = pose_seq[:, :, :2]
    conf = pose_seq[:, :, 2] if pose_seq.shape[-1] >= 3 else np.ones(pose_seq.shape[:2], dtype=np.float32)
    lower_conf = np.mean(
        conf[:, [KP["left_hip"], KP["right_hip"], KP["left_ankle"], KP["right_ankle"]]],
        axis=1,
    )
    body_scale = estimate_body_scale(xy)
    left_ankle = xy[:, KP["left_ankle"]] / body_scale
    right_ankle = xy[:, KP["right_ankle"]] / body_scale
    ankle_center = (left_ankle + right_ankle) / 2.0
    hip_center = ((xy[:, KP["left_hip"]] + xy[:, KP["right_hip"]]) / 2.0) / body_scale
    foot_spread = np.linalg.norm(left_ankle - right_ankle, axis=1)

    valid = lower_conf > 0.18
    if np.count_nonzero(valid) >= 4:
        ankle_center = ankle_center[valid]
        hip_center = hip_center[valid]
        foot_spread = foot_spread[valid]

    step = np.linalg.norm(np.diff(ankle_center, axis=0), axis=1)
    hip_step = np.linalg.norm(np.diff(hip_center, axis=0), axis=1)
    if len(step):
        step_limit = max(float(np.percentile(step, 90)) * 2.5, 1e-6)
        step = step[step <= step_limit]
    if len(hip_step):
        hip_limit = max(float(np.percentile(hip_step, 90)) * 2.5, 1e-6)
        hip_step = hip_step[hip_step <= hip_limit]

    total_movement = float(np.sum(step))
    peak_speed = float(np.max(step)) if len(step) else 0.0
    coverage = float(np.linalg.norm(np.max(ankle_center, axis=0) - np.min(ankle_center, axis=0)))
    hip_jitter = float(np.std(hip_step) / (np.mean(hip_step) + 1e-6)) if len(hip_step) else 0.0
    spread_std = float(np.std(foot_spread) / (np.mean(foot_spread) + 1e-6))
    start_end_distance = float(np.linalg.norm(ankle_center[-1] - ankle_center[0]))
    path_length = total_movement + 1e-6
    recovery = clamp_score(100.0 - (start_end_distance / path_length) * 120.0)
    stability = clamp_score(100.0 - hip_jitter * 35.0)
    balance = clamp_score(100.0 - spread_std * 65.0)
    movement = clamp_score(total_movement / max(len(pose_seq) / 32.0, 1.0) * 28.0)
    explosiveness = clamp_score(peak_speed * 120.0)
    coverage_score = clamp_score(coverage * 55.0)
    coordination = clamp_score(stability * 0.4 + balance * 0.35 + recovery * 0.25)

    return {
        "movement": movement,
        "explosiveness": explosiveness,
        "stability": stability,
        "recovery": recovery,
        "coverage": coverage_score,
        "balance": balance,
        "coordination": coordination,
    }


def build_coach_report(report):
    summary = report["motion_summary"]
    events = report.get("hit_events", [])
    shot_events = report.get("shot_events", [])
    footwork = report.get("footwork_scores", {})
    low_scores = sorted(footwork.items(), key=lambda item: item[1])[:2]

    highlights = []
    highlights.append(f"本次主要识别动作为 {report['predicted_action']}，模型置信度为 {report['confidence']:.3f}。")
    highlights.append(f"姿态有效帧为 {summary['valid_frames']}/{summary['frames']}，检测率 {summary['detection_rate']:.3f}。")
    if shot_events:
        action_counts = {}
        for event in shot_events:
            action = event.get("shot_action") or "Unknown"
            action_counts[action] = action_counts.get(action, 0) + 1
        action_summary = "、".join(f"{action} {count} 次" for action, count in sorted(action_counts.items(), key=lambda item: item[1], reverse=True)[:4])
        highlights.append(f"系统检测到 {len(shot_events)} 个疑似击球点，并完成逐拍动作识别：{action_summary}。")
        quality_scores = [event.get("quality_score") for event in shot_events if event.get("quality_score") is not None]
        if quality_scores:
            highlights.append(f"逐拍平均质量评分为 {np.mean(quality_scores):.1f}，最低单拍评分为 {np.min(quality_scores):.1f}。")
    elif events:
        highlights.append(f"系统检测到 {len(events)} 个疑似击球点，可在标注视频中查看 Hit 标记。")
    else:
        highlights.append("系统未检测到明显击球峰值，建议检查视频是否包含完整挥拍或提高分析精度。")

    focus = []
    for key, score in low_scores:
        names = {
            "movement": "移动量",
            "explosiveness": "启动爆发",
            "stability": "重心稳定",
            "recovery": "回位能力",
            "coverage": "覆盖范围",
            "balance": "步幅平衡",
        }
        focus.append(f"{names.get(key, key)} 得分 {score:.1f}，建议作为下一轮训练重点。")
    if report["confidence"] < 0.55:
        focus.append("整体动作类别置信度偏低，长视频中可能包含多个动作，建议截取单拍片段复核。")
    low_conf_shots = [event for event in shot_events if event.get("shot_confidence", 1.0) < 0.45]
    if low_conf_shots:
        focus.append(f"有 {len(low_conf_shots)} 个击球片段置信度偏低，建议在每拍表格中优先复核这些片段。")
    issue_counts = {}
    for event in shot_events:
        for issue in event.get("quality_issues", []):
            if issue == "整体动作质量较稳定":
                continue
            issue_counts[issue] = issue_counts.get(issue, 0) + 1
    for issue, count in sorted(issue_counts.items(), key=lambda item: item[1], reverse=True)[:3]:
        focus.append(f"{issue} 出现 {count} 次，是本次复盘的优先改进点。")

    plan = [
        "进行 3 组启动步 + 回位训练，每组 30 秒，重点观察击球后是否快速回到准备位。",
        "按每拍动作识别表选择 5-10 个击球点做慢放复盘，检查击球点高度、挥拍速度和重心稳定性。",
        "下一次拍摄尽量保持全身入镜，固定机位，并优先测试 2-5 秒单拍片段。",
    ]

    return {
        "highlights": highlights,
        "focus": focus,
        "training_plan": plan,
    }


def make_training_advice(predicted_label, class_name, confidence, summary):
    advice = []
    if summary["detection_rate"] < 0.8:
        advice.append("姿态检测率偏低，建议拍摄时保持全身入镜，减少遮挡，并尽量使用固定机位。")
    if confidence < 0.55:
        advice.append("模型置信度偏低，这段动作可能和相近动作混淆，建议结合慢放视频人工复核。")

    if summary["max_wrist_above_shoulder"] < 0.2 and predicted_label in {2, 10, 12, 14}:
        advice.append("击球点可能偏低，后场或杀球动作建议提前移动到位，在身体前上方完成击球。")
    if summary["max_wrist_speed"] < 0.35 and predicted_label in {3, 9, 14, 15, 16, 17}:
        advice.append("挥拍速度峰值偏低，可以增加引拍到击球阶段的加速练习，注意放松手腕后再集中发力。")
    if summary["footwork_distance"] < 1.2 and predicted_label not in {0, 13}:
        advice.append("脚步移动量偏小，建议增加启动步和回位练习，击球后尽快回到准备位置。")
    if summary["hip_motion"] > 6.0:
        advice.append("重心移动幅度较大，击球时身体稳定性可能不足，建议降低重心并控制上半身晃动。")

    if not advice:
        advice.append(f"{class_name} 的整体动作节奏较稳定，可以继续结合多球训练巩固动作一致性。")
    return advice


def clean_class_name(raw_name):
    return raw_name.split("_", 1)[1] if "_" in raw_name else raw_name


def build_report(source, top_predictions, label_names, summary):
    predicted_label, confidence = top_predictions[0]
    class_name = clean_class_name(label_names.get(predicted_label, str(predicted_label)))
    topk = [
        {
            "label": label,
            "class_name": clean_class_name(label_names.get(label, str(label))),
            "confidence": round(conf, 6),
        }
        for label, conf in top_predictions
    ]
    return {
        "source": str(source),
        "predicted_label": predicted_label,
        "predicted_action": class_name,
        "confidence": round(confidence, 6),
        "top_predictions": topk,
        "motion_summary": {k: round(v, 6) if isinstance(v, float) else v for k, v in summary.items()},
        "training_advice": make_training_advice(predicted_label, class_name, confidence, summary),
    }


def print_report(report):
    print("\n羽动智练 - 单视频动作分析")
    print("=" * 36)
    print(f"输入: {report['source']}")
    print(f"预测动作: {report['predicted_action']} (label={report['predicted_label']})")
    print(f"置信度: {report['confidence']:.3f}")
    print("\nTop predictions:")
    for item in report["top_predictions"]:
        print(f"  {item['label']:02d} {item['class_name']:<22} {item['confidence']:.3f}")
    print("\n动作摘要:")
    summary = report["motion_summary"]
    print(f"  检测率: {summary['detection_rate']:.3f} ({summary['valid_frames']}/{summary['frames']} frames)")
    print(f"  惯用侧估计: {summary['dominant_side']}")
    print(f"  手腕峰值速度: {summary['max_wrist_speed']:.3f}")
    print(f"  脚步移动量: {summary['footwork_distance']:.3f}")
    print(f"  重心移动量: {summary['hip_motion']:.3f}")
    print("\n训练建议:")
    for idx, item in enumerate(report["training_advice"], start=1):
        print(f"  {idx}. {item}")


def main():
    parser = argparse.ArgumentParser(description="Predict badminton action from a video or pose sequence")
    parser.add_argument("--video", type=str, default=None, help="Input video path")
    parser.add_argument("--pose-file", type=str, default=None, help="Input *_pose.npy path")
    parser.add_argument("--checkpoint", type=str, default="models/pose_sequence_tcn_gru.pt")
    parser.add_argument("--pose-model", type=str, default="yolov8s-pose.pt")
    parser.add_argument("--output", type=str, default=None, help="Optional JSON report path")
    parser.add_argument("--max-frames", type=int, default=180)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--conf-threshold", type=float, default=0.3)
    parser.add_argument("--topk", type=int, default=5)
    parser.add_argument(
        "--process-every-n-frames",
        type=int,
        default=1,
        help="Process every N frames (1=all frames, 2=every second frame, etc.)",
    )
    parser.add_argument(
        "--target-player",
        choices=["near", "far", "left", "right", "custom", "manual_box", "largest"],
        default="near",
        help="Person selection strategy for multi-player videos",
    )
    parser.add_argument("--target-x", type=float, default=0.5, help="Custom target point x ratio, used with --target-player custom")
    parser.add_argument("--target-y", type=float, default=0.5, help="Custom target point y ratio, used with --target-player custom")
    parser.add_argument(
        "--target-bbox",
        type=float,
        nargs=4,
        metavar=("X1", "Y1", "X2", "Y2"),
        default=None,
        help="Normalized first-frame target box, used with --target-player manual_box",
    )
    parser.add_argument("--cpu", action="store_true")
    args = parser.parse_args()

    if bool(args.video) == bool(args.pose_file):
        raise SystemExit("Please provide exactly one of --video or --pose-file")

    device = torch.device("cuda" if torch.cuda.is_available() and not args.cpu else "cpu")
    model, checkpoint, label_names = load_model(args.checkpoint, device)

    if args.pose_file:
        source = Path(args.pose_file)
        pose_seq = np.load(source)
    else:
        source = Path(args.video)
        pose_seq = extract_pose_from_video(
            source,
            args.pose_model,
            conf_threshold=args.conf_threshold,
            max_frames=args.max_frames,
            batch_size=args.batch_size,
            target_player=args.target_player,
            target_point=(args.target_x, args.target_y) if args.target_player == "custom" else None,
            target_bbox=tuple(args.target_bbox) if args.target_bbox is not None else None,
            process_every_n_frames=args.process_every_n_frames,
        )

    top_predictions = predict_pose_sequence(model, checkpoint, pose_seq, device, topk=args.topk)
    summary = compute_motion_summary(pose_seq, conf_threshold=args.conf_threshold)
    report = build_report(source, top_predictions, label_names, summary)

    print_report(report)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\nReport saved to: {output_path}")


if __name__ == "__main__":
    main()
