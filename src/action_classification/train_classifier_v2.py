"""
Badminton Action Classification v3 - Stable Version
- Class weighting for imbalance
- Light data augmentation
- Simple 3-layer MLP (proven effective)
- Early stopping
"""

import json
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import argparse
import warnings
warnings.filterwarnings('ignore')

FEATURE_NAMES = [
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
    'sequence_length', 'valid_frames', 'detection_rate'
]

class BadmintonDataset(Dataset):
    def __init__(self, X, y, augment=False, noise_std=0.02):
        self.X = torch.FloatTensor(X)
        self.y = torch.LongTensor(y)
        self.augment = augment
        self.noise_std = noise_std

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        x = self.X[idx].clone()
        if self.augment:
            x = x + torch.randn_like(x) * self.noise_std
        return x, self.y[idx]

class MLPClassifier(nn.Module):
    def __init__(self, input_dim, num_classes, hidden_dims=[256, 128, 64], dropout=0.3):
        super().__init__()
        layers = []
        prev_dim = input_dim
        for h in hidden_dims:
            layers.extend([nn.Linear(prev_dim, h), nn.ReLU(), nn.Dropout(dropout)])
            prev_dim = h
        layers.append(nn.Linear(prev_dim, num_classes))
        self.network = nn.Sequential(*layers)

    def forward(self, x):
        return self.network(x)

def compute_class_weights(y, num_classes):
    counts = np.bincount(y, minlength=num_classes)
    weights = 1.0 / (counts + 1e-6)
    return torch.FloatTensor(weights / weights.sum() * num_classes)

def load_data(features_path):
    with open(features_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    X = np.array([[item.get(f, 0.0) for f in FEATURE_NAMES] for item in data], dtype=np.float32)
    y = np.array([item['label'] for item in data], dtype=np.int64)
    return np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0), y

def train_model(X_train, X_test, y_train, y_test, num_classes=18, epochs=150, batch_size=64, lr=0.001):
    print("\n" + "="*60)
    print("Training MLP v3 (Stable)")
    print("="*60)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Device: {device}")

    class_weights = compute_class_weights(y_train, num_classes).to(device)
    print(f"Class weight ratio: {class_weights.max()/class_weights.min():.2f}x")

    train_loader = DataLoader(BadmintonDataset(X_train, y_train, augment=True), batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(BadmintonDataset(X_test, y_test, augment=False), batch_size=batch_size, shuffle=False)

    model = MLPClassifier(input_dim=X_train.shape[1], num_classes=num_classes).to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='max', patience=10, factor=0.5)

    best_acc, patience_counter, best_state = 0.0, 0, None

    for epoch in range(epochs):
        model.train()
        for Xb, yb in train_loader:
            Xb, yb = Xb.to(device), yb.to(device)
            optimizer.zero_grad()
            loss = criterion(model(Xb), yb)
            loss.backward()
            optimizer.step()

        # Evaluation
        model.eval()
        correct = 0
        with torch.no_grad():
            for Xb, yb in test_loader:
                correct += (model(Xb.to(device)).argmax(1) == yb.to(device)).sum().item()
        acc = correct / len(test_loader.dataset)
        scheduler.step(acc)

        if acc > best_acc:
            best_acc, patience_counter, best_state = acc, 0, model.state_dict().copy()
        else:
            patience_counter += 1

        if (epoch + 1) % 10 == 0:
            print(f"Epoch [{epoch+1}/{epochs}] Test: {acc:.4f} | Best: {best_acc:.4f}")

        if patience_counter >= 25:
            print(f"Early stopping at epoch {epoch+1}")
            break

    model.load_state_dict(best_state)

    all_preds, all_labels = [], []
    with torch.no_grad():
        for Xb, yb in test_loader:
            all_preds.extend(model(Xb.to(device)).argmax(1).cpu().numpy())
            all_labels.extend(yb.numpy())

    print(f"\nFinal Accuracy: {best_acc:.4f} ({best_acc*100:.2f}%)")
    print(classification_report(all_labels, all_preds, digits=3))

    cm = confusion_matrix(all_labels, all_preds)
    print("\nPer-class Accuracy:")
    for i, a in enumerate(cm.diagonal() / cm.sum(axis=1)):
        print(f"  Class {i:2d}: {a:.3f}")

    return model, best_acc

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--features', type=str, default='D:/badminton-agent/data/badminton_features.json')
    parser.add_argument('--epochs', type=int, default=150)
    parser.add_argument('--batch-size', type=int, default=64)
    parser.add_argument('--lr', type=float, default=0.001)
    args = parser.parse_args()

    print("Loading data...")
    X, y = load_data(args.features)
    print(f"Samples: {len(X)}, Features: {X.shape[1]}, Classes: {len(np.unique(y))}")

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    model, acc = train_model(X_train_s, X_test_s, y_train, y_test,
                             epochs=args.epochs, batch_size=args.batch_size, lr=args.lr)

    Path('models').mkdir(exist_ok=True)
    torch.save(model.state_dict(), 'models/mlp_classifier_v3.pt')
    print("\nModel saved to models/mlp_classifier_v3.pt")

if __name__ == '__main__':
    main()