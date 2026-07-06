"""
Train a hierarchical badminton action classifier.

Stage 1 predicts a coarse action group. Stage 2 predicts the final action
inside the predicted group. This is useful when most errors are between
similar actions such as Lift/Clear/Push Shot or Smash/Tap Smash/Cut.
"""

import argparse
import copy
import json
import random
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler

from train_pose_sequence_classifier import (
    FocalLoss,
    PoseSequenceDataset,
    PoseTCNGRUClassifier,
    discover_pose_files,
    get_input_dim,
    label_display_name,
    save_evaluation_artifacts,
    set_seed,
)


ACTION_GROUPS = {
    "serve": [0, 13],
    "backcourt": [2, 10, 12],
    "smash_attack": [3, 9, 14],
    "front_midcourt": [1, 4, 5, 6, 7, 8],
    "drive_flat": [11, 15, 16, 17],
}


def build_label_to_group():
    label_to_group = {}
    group_names = list(ACTION_GROUPS.keys())
    for group_idx, group_name in enumerate(group_names):
        for label in ACTION_GROUPS[group_name]:
            if label in label_to_group:
                raise ValueError(f"Label {label} appears in multiple groups")
            label_to_group[label] = group_idx
    return label_to_group, group_names


def make_sampler(labels, num_classes):
    counts = np.bincount(labels, minlength=num_classes)
    sample_weights = np.array([1.0 / max(counts[label], 1) for label in labels], dtype=np.float64)
    return WeightedRandomSampler(sample_weights, num_samples=len(sample_weights), replacement=True)


def make_loss(loss_name, class_weights, focal_gamma):
    if loss_name == "focal":
        return FocalLoss(class_weights=class_weights, gamma=focal_gamma)
    if loss_name == "cross_entropy":
        return nn.CrossEntropyLoss(weight=class_weights)
    raise ValueError(f"Unknown loss: {loss_name}")


class RelabeledPoseDataset(Dataset):
    def __init__(self, samples, target_labels, seq_len=64, augment=False, feature_set="base"):
        if len(samples) != len(target_labels):
            raise ValueError("samples and target_labels must have the same length")
        self.base = PoseSequenceDataset(samples, seq_len=seq_len, augment=augment, feature_set=feature_set)
        self.target_labels = torch.LongTensor(target_labels)

    def __len__(self):
        return len(self.base)

    def __getitem__(self, idx):
        x, _ = self.base[idx]
        return x, self.target_labels[idx]


def train_single_classifier(
    name,
    train_samples,
    train_targets,
    val_samples,
    val_targets,
    num_classes,
    args,
    balance_mode,
    loss_name,
):
    input_dim = get_input_dim(args.feature_set)
    device = torch.device("cuda" if torch.cuda.is_available() and not args.cpu else "cpu")

    train_targets = np.array(train_targets, dtype=np.int64)
    val_targets = np.array(val_targets, dtype=np.int64)
    counts = np.bincount(train_targets, minlength=num_classes)
    class_weights = torch.tensor(1.0 / np.maximum(counts, 1), dtype=torch.float32)
    class_weights = class_weights / class_weights.sum() * num_classes

    if balance_mode in ["class_weight", "both"]:
        loss_weights = class_weights.to(device)
    else:
        loss_weights = None

    if balance_mode in ["sampler", "both"]:
        sampler = make_sampler(train_targets, num_classes)
        shuffle = False
    else:
        sampler = None
        shuffle = True

    train_loader = DataLoader(
        RelabeledPoseDataset(
            train_samples,
            train_targets,
            seq_len=args.seq_len,
            augment=True,
            feature_set=args.feature_set,
        ),
        batch_size=args.batch_size,
        sampler=sampler,
        shuffle=shuffle,
        num_workers=args.num_workers,
        pin_memory=torch.cuda.is_available(),
    )
    val_loader = DataLoader(
        RelabeledPoseDataset(
            val_samples,
            val_targets,
            seq_len=args.seq_len,
            augment=False,
            feature_set=args.feature_set,
        ),
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=torch.cuda.is_available(),
    )

    model = PoseTCNGRUClassifier(
        input_dim=input_dim,
        num_classes=num_classes,
        hidden_dim=args.hidden_dim,
        dropout=args.dropout,
    ).to(device)
    criterion = make_loss(loss_name, loss_weights, args.focal_gamma)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)

    best_state = None
    best_macro_f1 = -1.0
    patience = 0
    print(
        f"\nTraining {name}: train={len(train_samples)} val={len(val_samples)} "
        f"classes={num_classes} balance={balance_mode} loss={loss_name}"
    )

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
        val_loss, val_acc, val_macro_f1 = evaluate_simple(model, val_loader, device)
        train_loss = total_loss / len(train_loader.dataset)

        if val_macro_f1 > best_macro_f1:
            best_macro_f1 = val_macro_f1
            best_state = copy.deepcopy(model.state_dict())
            patience = 0
        else:
            patience += 1

        if epoch == 1 or epoch % args.log_every == 0:
            print(
                f"{name} epoch {epoch:03d}/{args.epochs} "
                f"train_loss={train_loss:.4f} val_loss={val_loss:.4f} "
                f"val_acc={val_acc:.4f} val_macro_f1={val_macro_f1:.4f} "
                f"best={best_macro_f1:.4f}"
            )

        if patience >= args.patience:
            print(f"{name} early stopping at epoch {epoch}")
            break

    model.load_state_dict(best_state)
    return model


def evaluate_simple(model, loader, device):
    model.eval()
    criterion = nn.CrossEntropyLoss()
    all_preds = []
    all_labels = []
    total_loss = 0.0

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
    return total_loss / len(loader.dataset), acc, macro_f1


def predict_loader(model, samples, args):
    device = torch.device("cuda" if torch.cuda.is_available() and not args.cpu else "cpu")
    loader = DataLoader(
        PoseSequenceDataset(samples, seq_len=args.seq_len, augment=False, feature_set=args.feature_set),
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=torch.cuda.is_available(),
    )
    model.eval()
    preds = []
    probs = []
    with torch.no_grad():
        for x, _ in loader:
            logits = model(x.to(device))
            prob = torch.softmax(logits, dim=1)
            preds.extend(prob.argmax(dim=1).cpu().numpy())
            probs.extend(prob.max(dim=1).values.cpu().numpy())
    return np.array(preds, dtype=np.int64), np.array(probs, dtype=np.float32)


def train(args):
    set_seed(args.seed)
    samples, label_names = discover_pose_files(args.pose_dir, args.limit, args.samples_per_class)
    if not samples:
        raise RuntimeError(f"No *_pose.npy files found under {args.pose_dir}")

    label_to_group, group_names = build_label_to_group()
    labels = np.array([label for _, label in samples], dtype=np.int64)
    missing = sorted(set(labels.tolist()) - set(label_to_group.keys()))
    if missing:
        raise ValueError(f"Labels missing from ACTION_GROUPS: {missing}")

    train_samples, val_samples = train_test_split(
        samples,
        test_size=args.val_ratio,
        random_state=args.seed,
        stratify=labels,
    )
    train_labels = np.array([label for _, label in train_samples], dtype=np.int64)
    val_labels = np.array([label for _, label in val_samples], dtype=np.int64)
    train_groups = np.array([label_to_group[label] for label in train_labels], dtype=np.int64)
    val_groups = np.array([label_to_group[label] for label in val_labels], dtype=np.int64)

    print(f"Samples: {len(samples)} | Train: {len(train_samples)} | Val: {len(val_samples)}")
    print(f"Feature set: {args.feature_set} | Input dim: {get_input_dim(args.feature_set)}")
    print("Groups:")
    for idx, group_name in enumerate(group_names):
        members = ", ".join(label_display_name(label, label_names) for label in ACTION_GROUPS[group_name])
        print(f"  {idx}: {group_name} -> {members}")

    group_model = train_single_classifier(
        "coarse_group",
        train_samples,
        train_groups,
        val_samples,
        val_groups,
        len(group_names),
        args,
        args.coarse_balance_mode,
        args.coarse_loss,
    )

    group_models = {}
    group_local_to_global = {}
    for group_idx, group_name in enumerate(group_names):
        global_labels = ACTION_GROUPS[group_name]
        local_map = {label: local_idx for local_idx, label in enumerate(global_labels)}
        group_local_to_global[group_idx] = global_labels

        group_train_samples = [sample for sample, label in zip(train_samples, train_labels) if label in local_map]
        group_train_targets = [local_map[label] for label in train_labels if label in local_map]
        group_val_samples = [sample for sample, label in zip(val_samples, val_labels) if label in local_map]
        group_val_targets = [local_map[label] for label in val_labels if label in local_map]

        group_models[group_idx] = train_single_classifier(
            f"fine_{group_name}",
            group_train_samples,
            group_train_targets,
            group_val_samples,
            group_val_targets,
            len(global_labels),
            args,
            args.fine_balance_mode,
            args.fine_loss,
        )

    coarse_preds, coarse_conf = predict_loader(group_model, val_samples, args)
    final_preds = []
    fine_conf = []
    for group_idx in sorted(group_models.keys()):
        indices = np.where(coarse_preds == group_idx)[0]
        if len(indices) == 0:
            continue
        subset_samples = [val_samples[i] for i in indices]
        local_preds, local_conf = predict_loader(group_models[group_idx], subset_samples, args)
        global_labels = group_local_to_global[group_idx]
        for val_index, local_pred, conf in zip(indices, local_preds, local_conf):
            while len(final_preds) <= val_index:
                final_preds.append(None)
                fine_conf.append(0.0)
            final_preds[val_index] = global_labels[int(local_pred)]
            fine_conf[val_index] = float(conf)

    final_preds = np.array(final_preds, dtype=np.int64)
    coarse_acc = accuracy_score(val_groups, coarse_preds)
    final_acc = accuracy_score(val_labels, final_preds)
    final_macro_f1 = f1_score(val_labels, final_preds, average="macro", zero_division=0)

    labels_for_report = sorted(label_names.keys())
    target_names = [label_display_name(label, label_names) for label in labels_for_report]
    print("\nHierarchical validation results")
    print(f"Coarse group accuracy: {coarse_acc:.4f}")
    print(f"Final accuracy:        {final_acc:.4f}")
    print(f"Final macro F1:        {final_macro_f1:.4f}")
    print(
        classification_report(
            val_labels,
            final_preds,
            labels=labels_for_report,
            target_names=target_names,
            digits=3,
            zero_division=0,
        )
    )

    save_dir = Path(args.save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    eval_dir = save_evaluation_artifacts(val_labels, final_preds, label_names, save_dir)

    checkpoint = {
        "model_name": "HierarchicalPoseTCNGRUClassifier",
        "feature_set": args.feature_set,
        "input_dim": get_input_dim(args.feature_set),
        "seq_len": args.seq_len,
        "hidden_dim": args.hidden_dim,
        "action_groups": ACTION_GROUPS,
        "group_names": group_names,
        "label_names": {str(k): v for k, v in sorted(label_names.items())},
        "metrics": {
            "coarse_group_accuracy": coarse_acc,
            "final_accuracy": final_acc,
            "final_macro_f1": final_macro_f1,
        },
        "training_modes": {
            "coarse_balance_mode": args.coarse_balance_mode,
            "coarse_loss": args.coarse_loss,
            "fine_balance_mode": args.fine_balance_mode,
            "fine_loss": args.fine_loss,
        },
        "group_model_state": group_model.state_dict(),
        "fine_model_states": {str(k): v.state_dict() for k, v in group_models.items()},
    }
    torch.save(checkpoint, save_dir / "hierarchical_pose_tcn_gru.pt")
    with open(save_dir / "hierarchical_config.json", "w", encoding="utf-8") as f:
        serializable = dict(checkpoint)
        serializable.pop("group_model_state")
        serializable.pop("fine_model_states")
        json.dump(serializable, f, indent=2, ensure_ascii=False)

    print(f"\nSaved: {save_dir / 'hierarchical_pose_tcn_gru.pt'}")
    print(f"Evaluation artifacts saved to: {eval_dir}")


def main():
    parser = argparse.ArgumentParser(description="Train hierarchical badminton action classifier")
    parser.add_argument("--pose-dir", type=str, default="data/pose_features")
    parser.add_argument("--save-dir", type=str, default="models/hierarchical")
    parser.add_argument("--seq-len", type=int, default=64)
    parser.add_argument("--feature-set", type=str, default="base", choices=["base", "motion"])
    parser.add_argument("--hidden-dim", type=int, default=128)
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--dropout", type=float, default=0.25)
    parser.add_argument("--focal-gamma", type=float, default=1.5)
    parser.add_argument(
        "--coarse-balance-mode",
        type=str,
        default="both",
        choices=["none", "class_weight", "sampler", "both"],
    )
    parser.add_argument(
        "--fine-balance-mode",
        type=str,
        default="class_weight",
        choices=["none", "class_weight", "sampler", "both"],
    )
    parser.add_argument("--coarse-loss", type=str, default="focal", choices=["focal", "cross_entropy"])
    parser.add_argument("--fine-loss", type=str, default="cross_entropy", choices=["focal", "cross_entropy"])
    parser.add_argument("--val-ratio", type=float, default=0.2)
    parser.add_argument("--patience", type=int, default=15)
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
