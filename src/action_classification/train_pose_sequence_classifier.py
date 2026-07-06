"""
Train a badminton action classifier directly from pose sequences.

This model uses the full temporal pose sequence instead of compressing each
video into a small set of global statistics. It is a better fit for badminton
actions, where the order of preparation, swing, contact, and recovery matters.
"""

import argparse
import copy
import csv
import json
import random
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler


KP = {
    "left_wrist": 9,
    "right_wrist": 10,
    "left_shoulder": 5,
    "right_shoulder": 6,
    "left_hip": 11,
    "right_hip": 12,
    "left_ankle": 15,
    "right_ankle": 16,
}


EXTRA_FEATURE_NAMES = [
    "hip_dx",
    "hip_dy",
    "ankle_center_dx",
    "ankle_center_dy",
    "shoulder_center_dx",
    "shoulder_center_dy",
    "foot_spread",
    "left_wrist_rel_shoulder_y",
    "right_wrist_rel_shoulder_y",
    "left_wrist_speed",
    "right_wrist_speed",
    "left_wrist_acceleration",
    "right_wrist_acceleration",
    "hip_speed",
    "ankle_center_speed",
    "torso_angle_sin",
    "torso_angle_cos",
]


BASE_INPUT_DIM = 17 * 2 + 17 + 17 * 2
MOTION_INPUT_DIM = BASE_INPUT_DIM + len(EXTRA_FEATURE_NAMES)


def get_input_dim(feature_set):
    if feature_set == "base":
        return BASE_INPUT_DIM
    if feature_set == "motion":
        return MOTION_INPUT_DIM
    raise ValueError(f"Unknown feature set: {feature_set}")


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def discover_pose_files(pose_dir, limit=None, samples_per_class=None):
    pose_dir = Path(pose_dir)
    samples = []
    label_names = {}

    for class_dir in sorted([p for p in pose_dir.iterdir() if p.is_dir()]):
        try:
            label = int(class_dir.name.split("_")[0])
        except ValueError:
            continue
        label_names[label] = class_dir.name
        class_files = sorted(class_dir.glob("*_pose.npy"))
        if samples_per_class is not None:
            class_files = class_files[:samples_per_class]
        for npy_path in class_files:
            samples.append((npy_path, label))

    if limit is not None:
        samples = samples[:limit]

    return samples, label_names


def resample_sequence(arr, seq_len):
    if len(arr) == seq_len:
        return arr
    if len(arr) == 0:
        return np.zeros((seq_len, arr.shape[1]), dtype=np.float32)
    if len(arr) == 1:
        return np.repeat(arr, seq_len, axis=0)

    old_idx = np.linspace(0.0, 1.0, len(arr))
    new_idx = np.linspace(0.0, 1.0, seq_len)
    channels = [np.interp(new_idx, old_idx, arr[:, c]) for c in range(arr.shape[1])]
    return np.stack(channels, axis=1).astype(np.float32)


def normalize_pose_sequence(pose_seq, seq_len=64, conf_threshold=0.2, feature_set="base"):
    """
    Convert raw YOLO keypoints (T, 17, 3) into a scale-normalized sequence.

    Output per frame:
      17 normalized x/y pairs
      + 17 keypoint confidences
      + 17 normalized velocity x/y pairs.
      When feature_set="motion", badminton-specific position/motion features
      are appended as an ablation experiment.
    """
    pose_seq = np.asarray(pose_seq, dtype=np.float32)
    if pose_seq.ndim != 3 or pose_seq.shape[1:] != (17, 3):
        raise ValueError(f"Expected pose shape (T, 17, 3), got {pose_seq.shape}")

    raw_xy = pose_seq[:, :, :2].copy()
    xy = raw_xy.copy()
    conf = pose_seq[:, :, 2:3].copy()
    valid = conf[:, :, 0] > conf_threshold

    left_hip = raw_xy[:, KP["left_hip"]]
    right_hip = raw_xy[:, KP["right_hip"]]
    hip_center = (left_hip + right_hip) / 2.0

    left_shoulder = raw_xy[:, KP["left_shoulder"]]
    right_shoulder = raw_xy[:, KP["right_shoulder"]]
    shoulder_center = (left_shoulder + right_shoulder) / 2.0
    shoulder_width = np.linalg.norm(left_shoulder - right_shoulder, axis=1)
    hip_width = np.linalg.norm(left_hip - right_hip, axis=1)
    body_scale = np.nanmedian(np.maximum(shoulder_width, hip_width))

    if not np.isfinite(body_scale) or body_scale < 1.0:
        flat_xy = raw_xy.reshape(-1, 2)
        body_scale = max(float(np.nanstd(flat_xy[:, 0]) + np.nanstd(flat_xy[:, 1])), 1.0)

    xy = (xy - hip_center[:, None, :]) / body_scale
    xy[~valid] = 0.0
    conf = np.clip(conf, 0.0, 1.0)

    velocity = np.diff(xy, axis=0, prepend=xy[:1])
    feature_parts = [
        xy.reshape(len(xy), -1),
        conf.reshape(len(conf), -1),
        velocity.reshape(len(velocity), -1),
    ]
    if feature_set == "motion":
        feature_parts.append(extract_position_motion_features(raw_xy, conf[:, :, 0], body_scale))
    elif feature_set != "base":
        raise ValueError(f"Unknown feature set: {feature_set}")

    features = np.concatenate(feature_parts, axis=1)
    return resample_sequence(features, seq_len)


def safe_speed(arr):
    return np.linalg.norm(np.diff(arr, axis=0, prepend=arr[:1]), axis=1, keepdims=True)


def extract_position_motion_features(raw_xy, conf, body_scale):
    left_hip = raw_xy[:, KP["left_hip"]]
    right_hip = raw_xy[:, KP["right_hip"]]
    hip_center = (left_hip + right_hip) / 2.0

    left_ankle = raw_xy[:, KP["left_ankle"]]
    right_ankle = raw_xy[:, KP["right_ankle"]]
    ankle_center = (left_ankle + right_ankle) / 2.0

    left_shoulder = raw_xy[:, KP["left_shoulder"]]
    right_shoulder = raw_xy[:, KP["right_shoulder"]]
    shoulder_center = (left_shoulder + right_shoulder) / 2.0

    left_wrist = raw_xy[:, KP["left_wrist"]]
    right_wrist = raw_xy[:, KP["right_wrist"]]

    hip_delta = (hip_center - hip_center[:1]) / body_scale
    ankle_delta = (ankle_center - ankle_center[:1]) / body_scale
    shoulder_delta = (shoulder_center - shoulder_center[:1]) / body_scale

    foot_spread = np.linalg.norm(left_ankle - right_ankle, axis=1, keepdims=True) / body_scale
    left_wrist_rel_shoulder_y = ((left_shoulder[:, 1:2] - left_wrist[:, 1:2]) / body_scale)
    right_wrist_rel_shoulder_y = ((right_shoulder[:, 1:2] - right_wrist[:, 1:2]) / body_scale)

    left_wrist_speed = safe_speed(left_wrist / body_scale)
    right_wrist_speed = safe_speed(right_wrist / body_scale)
    left_wrist_acc = safe_speed(np.diff(left_wrist / body_scale, axis=0, prepend=left_wrist[:1] / body_scale))
    right_wrist_acc = safe_speed(np.diff(right_wrist / body_scale, axis=0, prepend=right_wrist[:1] / body_scale))
    hip_speed = safe_speed(hip_center / body_scale)
    ankle_speed = safe_speed(ankle_center / body_scale)

    torso_vec = shoulder_center - hip_center
    torso_angle = np.arctan2(torso_vec[:, 0:1], -torso_vec[:, 1:2])
    torso_angle_sin = np.sin(torso_angle)
    torso_angle_cos = np.cos(torso_angle)

    features = np.concatenate(
        [
            hip_delta,
            ankle_delta,
            shoulder_delta,
            foot_spread,
            left_wrist_rel_shoulder_y,
            right_wrist_rel_shoulder_y,
            left_wrist_speed,
            right_wrist_speed,
            left_wrist_acc,
            right_wrist_acc,
            hip_speed,
            ankle_speed,
            torso_angle_sin,
            torso_angle_cos,
        ],
        axis=1,
    ).astype(np.float32)

    required_conf = [
        KP["left_hip"],
        KP["right_hip"],
        KP["left_ankle"],
        KP["right_ankle"],
        KP["left_shoulder"],
        KP["right_shoulder"],
        KP["left_wrist"],
        KP["right_wrist"],
    ]
    valid_frame = np.mean(conf[:, required_conf] > 0.2, axis=1, keepdims=True)
    features *= valid_frame
    return np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0)


class PoseSequenceDataset(Dataset):
    def __init__(self, samples, seq_len=64, augment=False, feature_set="base"):
        self.samples = samples
        self.seq_len = seq_len
        self.augment = augment
        self.feature_set = feature_set

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        npy_path, label = self.samples[idx]
        pose_seq = np.load(npy_path)
        x = normalize_pose_sequence(pose_seq, seq_len=self.seq_len, feature_set=self.feature_set)

        if self.augment:
            x = self.augment_sequence(x)

        return torch.from_numpy(x), torch.tensor(label, dtype=torch.long)

    @staticmethod
    def augment_sequence(x):
        x = x.copy()
        coord_dims = list(range(0, 34)) + list(range(51, 85))
        x[:, coord_dims] += np.random.normal(0.0, 0.015, size=x[:, coord_dims].shape).astype(np.float32)

        if np.random.rand() < 0.3:
            scale = np.random.uniform(0.95, 1.05)
            x[:, coord_dims] *= scale

        return x.astype(np.float32)


class TemporalBlock(nn.Module):
    def __init__(self, channels, kernel_size=5, dilation=1, dropout=0.15):
        super().__init__()
        padding = dilation * (kernel_size - 1) // 2
        self.conv1 = nn.Conv1d(channels, channels, kernel_size, padding=padding, dilation=dilation)
        self.bn1 = nn.BatchNorm1d(channels)
        self.conv2 = nn.Conv1d(channels, channels, kernel_size, padding=padding, dilation=dilation)
        self.bn2 = nn.BatchNorm1d(channels)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        residual = x
        x = self.dropout(F.gelu(self.bn1(self.conv1(x))))
        x = self.dropout(F.gelu(self.bn2(self.conv2(x))))
        return x + residual


class PoseTCNGRUClassifier(nn.Module):
    def __init__(self, input_dim=BASE_INPUT_DIM, num_classes=18, hidden_dim=128, dropout=0.25):
        super().__init__()
        self.input_norm = nn.LayerNorm(input_dim)
        self.input_proj = nn.Linear(input_dim, hidden_dim)
        self.tcn = nn.Sequential(
            TemporalBlock(hidden_dim, dilation=1, dropout=dropout),
            TemporalBlock(hidden_dim, dilation=2, dropout=dropout),
            TemporalBlock(hidden_dim, dilation=4, dropout=dropout),
        )
        self.gru = nn.GRU(
            input_size=hidden_dim,
            hidden_size=hidden_dim,
            num_layers=1,
            batch_first=True,
            bidirectional=True,
        )
        self.attn = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, 1),
        )
        self.classifier = nn.Sequential(
            nn.LayerNorm(hidden_dim * 2),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, num_classes),
        )

    def forward(self, x):
        x = self.input_proj(self.input_norm(x))
        x = self.tcn(x.transpose(1, 2)).transpose(1, 2)
        x, _ = self.gru(x)
        weights = torch.softmax(self.attn(x), dim=1)
        pooled = torch.sum(x * weights, dim=1)
        return self.classifier(pooled)


class FocalLoss(nn.Module):
    def __init__(self, class_weights=None, gamma=1.5, label_smoothing=0.03):
        super().__init__()
        self.register_buffer("class_weights", class_weights)
        self.gamma = gamma
        self.label_smoothing = label_smoothing

    def forward(self, logits, target):
        ce = F.cross_entropy(
            logits,
            target,
            weight=self.class_weights,
            reduction="none",
            label_smoothing=self.label_smoothing,
        )
        pt = torch.exp(-ce)
        return (((1.0 - pt) ** self.gamma) * ce).mean()


def make_sampler(labels, num_classes):
    counts = np.bincount(labels, minlength=num_classes)
    sample_weights = np.array([1.0 / max(counts[label], 1) for label in labels], dtype=np.float64)
    return WeightedRandomSampler(sample_weights, num_samples=len(sample_weights), replacement=True)


def evaluate(model, loader, device):
    model.eval()
    all_preds = []
    all_labels = []
    total_loss = 0.0
    criterion = nn.CrossEntropyLoss()

    with torch.no_grad():
        for x, y in loader:
            x = x.to(device)
            y = y.to(device)
            logits = model(x)
            total_loss += criterion(logits, y).item() * len(y)
            all_preds.extend(logits.argmax(dim=1).cpu().numpy())
            all_labels.extend(y.cpu().numpy())

    acc = accuracy_score(all_labels, all_preds)
    macro_f1 = f1_score(all_labels, all_preds, average="macro", zero_division=0)
    return total_loss / len(loader.dataset), acc, macro_f1, all_labels, all_preds


def label_display_name(label, label_names):
    raw_name = label_names.get(label, str(label))
    return raw_name.split("_", 1)[1] if "_" in raw_name else raw_name


def save_evaluation_artifacts(y_true, y_pred, label_names, save_dir):
    save_dir = Path(save_dir)
    eval_dir = save_dir / "evaluation"
    eval_dir.mkdir(parents=True, exist_ok=True)

    labels = sorted(label_names.keys())
    target_names = [label_display_name(label, label_names) for label in labels]

    cm = confusion_matrix(y_true, y_pred, labels=labels)
    np.savetxt(eval_dir / "confusion_matrix.csv", cm, fmt="%d", delimiter=",")

    precision, recall, f1, support = precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=labels,
        zero_division=0,
    )
    with open(eval_dir / "per_class_metrics.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["label", "class_name", "precision", "recall", "f1", "support"])
        for i, label in enumerate(labels):
            writer.writerow(
                [
                    label,
                    target_names[i],
                    f"{precision[i]:.6f}",
                    f"{recall[i]:.6f}",
                    f"{f1[i]:.6f}",
                    int(support[i]),
                ]
            )

    report = classification_report(
        y_true,
        y_pred,
        labels=labels,
        target_names=target_names,
        digits=4,
        zero_division=0,
        output_dict=True,
    )
    with open(eval_dir / "classification_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    confusions = []
    for true_idx, true_label in enumerate(labels):
        for pred_idx, pred_label in enumerate(labels):
            if true_label == pred_label:
                continue
            count = int(cm[true_idx, pred_idx])
            if count > 0:
                confusions.append((count, true_label, pred_label))
    confusions.sort(reverse=True)

    with open(eval_dir / "top_confusions.txt", "w", encoding="utf-8") as f:
        f.write("Top misclassifications\n")
        f.write("======================\n")
        for count, true_label, pred_label in confusions[:30]:
            true_name = label_display_name(true_label, label_names)
            pred_name = label_display_name(pred_label, label_names)
            f.write(f"{count:4d} | true {true_label:02d} {true_name} -> pred {pred_label:02d} {pred_name}\n")

    try:
        import matplotlib.pyplot as plt

        fig_size = max(10, len(labels) * 0.65)
        fig, ax = plt.subplots(figsize=(fig_size, fig_size))
        im = ax.imshow(cm, interpolation="nearest", cmap="Blues")
        ax.figure.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        ax.set(
            xticks=np.arange(len(labels)),
            yticks=np.arange(len(labels)),
            xticklabels=[f"{label:02d}" for label in labels],
            yticklabels=[f"{label:02d}" for label in labels],
            ylabel="True label",
            xlabel="Predicted label",
            title="Validation Confusion Matrix",
        )
        threshold = cm.max() / 2.0 if cm.size else 0
        for i in range(cm.shape[0]):
            for j in range(cm.shape[1]):
                if cm[i, j] > 0:
                    ax.text(
                        j,
                        i,
                        str(cm[i, j]),
                        ha="center",
                        va="center",
                        color="white" if cm[i, j] > threshold else "black",
                        fontsize=7,
                    )
        fig.tight_layout()
        fig.savefig(eval_dir / "confusion_matrix.png", dpi=180)
        plt.close(fig)
    except Exception as exc:
        with open(eval_dir / "confusion_matrix_png_skipped.txt", "w", encoding="utf-8") as f:
            f.write(f"Could not save PNG confusion matrix: {exc}\n")

    return eval_dir


def train(args):
    set_seed(args.seed)
    samples, label_names = discover_pose_files(args.pose_dir, args.limit, args.samples_per_class)
    if not samples:
        raise RuntimeError(f"No *_pose.npy files found under {args.pose_dir}")

    labels = np.array([label for _, label in samples], dtype=np.int64)
    num_classes = int(labels.max()) + 1
    train_samples, val_samples = train_test_split(
        samples,
        test_size=args.val_ratio,
        random_state=args.seed,
        stratify=labels,
    )

    train_labels = np.array([label for _, label in train_samples], dtype=np.int64)
    counts = np.bincount(train_labels, minlength=num_classes)
    class_weights = torch.tensor(1.0 / np.maximum(counts, 1), dtype=torch.float32)
    class_weights = class_weights / class_weights.sum() * num_classes

    train_loader = DataLoader(
        PoseSequenceDataset(
            train_samples,
            seq_len=args.seq_len,
            augment=True,
            feature_set=args.feature_set,
        ),
        batch_size=args.batch_size,
        sampler=make_sampler(train_labels, num_classes),
        num_workers=args.num_workers,
        pin_memory=torch.cuda.is_available(),
    )
    val_loader = DataLoader(
        PoseSequenceDataset(
            val_samples,
            seq_len=args.seq_len,
            augment=False,
            feature_set=args.feature_set,
        ),
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=torch.cuda.is_available(),
    )

    device = torch.device("cuda" if torch.cuda.is_available() and not args.cpu else "cpu")
    input_dim = get_input_dim(args.feature_set)
    model = PoseTCNGRUClassifier(
        input_dim=input_dim,
        num_classes=num_classes,
        hidden_dim=args.hidden_dim,
        dropout=args.dropout,
    ).to(device)
    criterion = FocalLoss(class_weights=class_weights.to(device), gamma=args.focal_gamma)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)

    print(f"Samples: {len(samples)} | Train: {len(train_samples)} | Val: {len(val_samples)}")
    print(f"Classes: {num_classes} | Device: {device}")
    print(f"Feature set: {args.feature_set} | Input dim: {input_dim}")
    print(f"Class weight ratio: {(class_weights.max() / class_weights.min()).item():.2f}x")

    best_state = None
    best_macro_f1 = -1.0
    patience = 0

    for epoch in range(1, args.epochs + 1):
        model.train()
        total_loss = 0.0
        for x, y in train_loader:
            x = x.to(device)
            y = y.to(device)
            optimizer.zero_grad()
            loss = criterion(model(x), y)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=3.0)
            optimizer.step()
            total_loss += loss.item() * len(y)

        scheduler.step()
        val_loss, val_acc, val_macro_f1, _, _ = evaluate(model, val_loader, device)
        train_loss = total_loss / len(train_loader.dataset)

        if val_macro_f1 > best_macro_f1:
            best_macro_f1 = val_macro_f1
            best_state = copy.deepcopy(model.state_dict())
            patience = 0
        else:
            patience += 1

        if epoch == 1 or epoch % args.log_every == 0:
            print(
                f"Epoch {epoch:03d}/{args.epochs} "
                f"train_loss={train_loss:.4f} val_loss={val_loss:.4f} "
                f"val_acc={val_acc:.4f} val_macro_f1={val_macro_f1:.4f} "
                f"best_macro_f1={best_macro_f1:.4f}"
            )

        if patience >= args.patience:
            print(f"Early stopping at epoch {epoch}")
            break

    model.load_state_dict(best_state)
    _, val_acc, val_macro_f1, y_true, y_pred = evaluate(model, val_loader, device)
    print("\nFinal validation results")
    print(f"Accuracy: {val_acc:.4f}")
    print(f"Macro F1:  {val_macro_f1:.4f}")
    labels_for_report = sorted(label_names.keys())
    target_names = [label_display_name(label, label_names) for label in labels_for_report]
    print(
        classification_report(
            y_true,
            y_pred,
            labels=labels_for_report,
            target_names=target_names,
            digits=3,
            zero_division=0,
        )
    )

    save_dir = Path(args.save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    eval_dir = save_evaluation_artifacts(y_true, y_pred, label_names, save_dir)
    checkpoint = {
        "model_state": model.state_dict(),
        "model_name": "PoseTCNGRUClassifier",
        "input_dim": input_dim,
        "feature_set": args.feature_set,
        "seq_len": args.seq_len,
        "hidden_dim": args.hidden_dim,
        "num_classes": num_classes,
        "extra_feature_names": EXTRA_FEATURE_NAMES if args.feature_set == "motion" else [],
        "label_names": {str(k): v for k, v in sorted(label_names.items())},
        "metrics": {"val_accuracy": val_acc, "val_macro_f1": val_macro_f1},
    }
    torch.save(checkpoint, save_dir / "pose_sequence_tcn_gru.pt")
    with open(save_dir / "pose_sequence_labels.json", "w", encoding="utf-8") as f:
        json.dump(checkpoint["label_names"], f, indent=2, ensure_ascii=False)
    print(f"\nSaved: {save_dir / 'pose_sequence_tcn_gru.pt'}")
    print(f"Evaluation artifacts saved to: {eval_dir}")


def main():
    parser = argparse.ArgumentParser(description="Train pose-sequence badminton action classifier")
    parser.add_argument("--pose-dir", type=str, default="data/pose_features")
    parser.add_argument("--save-dir", type=str, default="models")
    parser.add_argument("--seq-len", type=int, default=64)
    parser.add_argument("--feature-set", type=str, default="base", choices=["base", "motion"])
    parser.add_argument("--hidden-dim", type=int, default=128)
    parser.add_argument("--epochs", type=int, default=120)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--dropout", type=float, default=0.25)
    parser.add_argument("--focal-gamma", type=float, default=1.5)
    parser.add_argument("--val-ratio", type=float, default=0.2)
    parser.add_argument("--patience", type=int, default=20)
    parser.add_argument("--log-every", type=int, default=5)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--limit", type=int, default=None, help="Optional quick-debug sample limit")
    parser.add_argument("--samples-per-class", type=int, default=None, help="Optional balanced quick-debug limit")
    parser.add_argument("--cpu", action="store_true")
    args = parser.parse_args()
    train(args)


if __name__ == "__main__":
    main()
