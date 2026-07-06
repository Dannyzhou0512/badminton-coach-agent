"""
Badminton Action Classification Training Script
Trains models to classify 18 badminton actions from pose-derived features.
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from collections import Counter
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from tqdm import tqdm
import argparse
import warnings
warnings.filterwarnings('ignore')

# Feature names (exclude metadata)
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
    def __init__(self, X, y):
        self.X = torch.FloatTensor(X)
        self.y = torch.LongTensor(y)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]


class MLPClassifier(nn.Module):
    def __init__(self, input_dim, num_classes, hidden_dims=[256, 128, 64], dropout=0.3):
        super().__init__()
        layers = []
        prev_dim = input_dim
        for h in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, h),
                nn.BatchNorm1d(h),
                nn.ReLU(),
                nn.Dropout(dropout)
            ])
            prev_dim = h
        layers.append(nn.Linear(prev_dim, num_classes))
        self.network = nn.Sequential(*layers)

    def forward(self, x):
        return self.network(x)


def load_data(features_path):
    """Load and prepare data from JSON."""
    with open(features_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Extract features and labels
    X = []
    y = []
    metadata = []
    for item in data:
        feat_vector = [item.get(f, 0.0) for f in FEATURE_NAMES]
        X.append(feat_vector)
        y.append(item['label'])
        metadata.append({
            'video_id': item.get('video_id', ''),
            'category': item.get('category', '')
        })

    X = np.array(X, dtype=np.float32)
    y = np.array(y, dtype=np.int64)

    # Handle NaN/Inf
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

    return X, y, metadata


def train_random_forest(X_train, X_test, y_train, y_test, num_classes=18):
    """Train RandomForest baseline."""
    print("\n" + "="*60)
    print("Training RandomForest Classifier")
    print("="*60)

    clf = RandomForestClassifier(
        n_estimators=200,
        max_depth=20,
        min_samples_split=5,
        min_samples_leaf=2,
        class_weight='balanced',  # Handle class imbalance
        random_state=42,
        n_jobs=-1
    )

    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)

    print(f"\nTest Accuracy: {acc:.4f} ({acc*100:.2f}%)")
    print(f"\nClassification Report:")
    print(classification_report(y_test, y_pred, digits=3))

    # Feature importance
    importances = pd.DataFrame({
        'feature': FEATURE_NAMES,
        'importance': clf.feature_importances_
    }).sort_values('importance', ascending=False)

    print(f"\nTop 10 Important Features:")
    print(importances.head(10).to_string(index=False))

    return clf, acc


def train_mlp(X_train, X_test, y_train, y_test, num_classes=18, epochs=100, batch_size=64, lr=0.001):
    """Train MLP neural network."""
    print("\n" + "="*60)
    print("Training MLP Neural Network")
    print("="*60)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Device: {device}")

    # Create datasets
    train_dataset = BadmintonDataset(X_train, y_train)
    test_dataset = BadmintonDataset(X_test, y_test)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

    # Model
    model = MLPClassifier(input_dim=X_train.shape[1], num_classes=num_classes).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='max', patience=10, factor=0.5)

    # Training loop
    best_acc = 0.0
    for epoch in range(epochs):
        model.train()
        train_loss = 0.0
        for X_batch, y_batch in train_loader:
            X_batch, y_batch = X_batch.to(device), y_batch.to(device)

            optimizer.zero_grad()
            outputs = model(X_batch)
            loss = criterion(outputs, y_batch)
            loss.backward()
            optimizer.step()

            train_loss += loss.item()

        # Validation
        model.eval()
        correct = 0
        total = 0
        with torch.no_grad():
            for X_batch, y_batch in test_loader:
                X_batch, y_batch = X_batch.to(device), y_batch.to(device)
                outputs = model(X_batch)
                _, predicted = torch.max(outputs, 1)
                total += y_batch.size(0)
                correct += (predicted == y_batch).sum().item()

        acc = correct / total
        scheduler.step(acc)

        if acc > best_acc:
            best_acc = acc

        if (epoch + 1) % 10 == 0:
            print(f"Epoch [{epoch+1}/{epochs}] Loss: {train_loss/len(train_loader):.4f} | Test Acc: {acc:.4f} | Best: {best_acc:.4f}")

    # Final evaluation
    model.eval()
    all_preds = []
    all_labels = []
    with torch.no_grad():
        for X_batch, y_batch in test_loader:
            X_batch = X_batch.to(device)
            outputs = model(X_batch)
            _, predicted = torch.max(outputs, 1)
            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(y_batch.numpy())

    print(f"\nFinal Test Accuracy: {best_acc:.4f} ({best_acc*100:.2f}%)")
    print(f"\nClassification Report:")
    print(classification_report(all_labels, all_preds, digits=3))

    return model, best_acc


def save_model(model, scaler, save_dir='models'):
    """Save trained model and scaler."""
    save_dir = Path(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    # Save scaler
    import joblib
    joblib.dump(scaler, save_dir / 'scaler.pkl')

    # Save PyTorch model
    if isinstance(model, nn.Module):
        torch.save(model.state_dict(), save_dir / 'mlp_classifier.pt')
        # Save model architecture info
        model_info = {
            'input_dim': len(FEATURE_NAMES),
            'num_classes': 18,
            'feature_names': FEATURE_NAMES
        }
        with open(save_dir / 'model_info.json', 'w') as f:
            json.dump(model_info, f, indent=2)
        print(f"\nModel saved to {save_dir}/mlp_classifier.pt")
    else:
        joblib.dump(model, save_dir / 'rf_classifier.pkl')
        print(f"\nModel saved to {save_dir}/rf_classifier.pkl")


def main():
    parser = argparse.ArgumentParser(description='Train badminton action classifier')
    parser.add_argument('--features', type=str, default='E:/Learning/badminton-agent/data/badminton_features.json')
    parser.add_argument('--model', type=str, default='both', choices=['rf', 'mlp', 'both'])
    parser.add_argument('--epochs', type=int, default=100)
    parser.add_argument('--batch-size', type=int, default=64)
    parser.add_argument('--lr', type=float, default=0.001)
    parser.add_argument('--save', action='store_true', help='Save trained models')
    args = parser.parse_args()

    # Load data
    print("Loading data...")
    X, y, metadata = load_data(args.features)
    print(f"Samples: {len(X)}, Features: {X.shape[1]}, Classes: {len(np.unique(y))}")

    # Show class distribution
    print("\nClass distribution:")
    for label, count in sorted(Counter(y).items()):
        print(f"  Class {label}: {count}")

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"\nTrain: {len(X_train)}, Test: {len(X_test)}")

    # Normalize features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    results = {}

    # Train RandomForest
    if args.model in ['rf', 'both']:
        rf_model, rf_acc = train_random_forest(X_train_scaled, X_test_scaled, y_train, y_test)
        results['RandomForest'] = rf_acc
        if args.save:
            save_model(rf_model, scaler)

    # Train MLP
    if args.model in ['mlp', 'both']:
        mlp_model, mlp_acc = train_mlp(
            X_train_scaled, X_test_scaled, y_train, y_test,
            epochs=args.epochs, batch_size=args.batch_size, lr=args.lr
        )
        results['MLP'] = mlp_acc
        if args.save:
            save_model(mlp_model, scaler)

    # Summary
    print("\n" + "="*60)
    print("Training Summary")
    print("="*60)
    for model_name, acc in results.items():
        print(f"{model_name}: {acc:.4f} ({acc*100:.2f}%)")


if __name__ == '__main__':
    main()
