# scripts/feature_engineering.py — Phase 2: Feature Engineering
#
# PURPOSE: Select features, remove redundant columns, encode labels,
# split into train/test (BEFORE scaling), scale, and save everything.
#
# RUN: python scripts/feature_engineering.py

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import os
import numpy as np
import pandas as pd
import joblib
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split

import config
from scripts.load_data import FEATURE_COLUMNS

TEST_SIZE   = 0.2
RANDOM_SEED = 42
CORR_THRESHOLD = 0.98


def load_cleaned():
    path = Path(config.PROCESSED_DATA_DIR) / "cleaned_data.csv"
    if not path.exists():
        raise FileNotFoundError(f"Run Phase 1 first: python scripts/load_data.py\n(Missing: {path})")
    df = pd.read_csv(path)
    print(f"Loaded cleaned data: {df.shape[0]:,} rows × {df.shape[1]} columns")
    return df


def select_features(df):
    available = [c for c in FEATURE_COLUMNS if c in df.columns]
    missing   = [c for c in FEATURE_COLUMNS if c not in df.columns]
    if missing:
        print(f"[Feature select] {len(missing)} columns not in data — skipping them.")
    print(f"Using {len(available)} feature columns.")
    return df[available].copy(), available


def remove_constant(X):
    const_cols = X.columns[X.std() == 0].tolist()
    if const_cols:
        print(f"[Low variance] Dropping {len(const_cols)} constant columns: {const_cols[:5]}{'...' if len(const_cols)>5 else ''}")
        X = X.drop(columns=const_cols)
    else:
        print("[Low variance] No constant columns.")
    return X


def remove_correlated(X, threshold=CORR_THRESHOLD):
    corr = X.corr().abs()
    upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
    to_drop = [c for c in upper.columns if any(upper[c] > threshold)]
    if to_drop:
        print(f"[High corr] Dropping {len(to_drop)} columns (threshold={threshold}).")
        X = X.drop(columns=to_drop)
    else:
        print(f"[High corr] No columns above {threshold}.")
    print(f"Features remaining: {len(X.columns)}")
    return X


def main():
    print("=" * 60)
    print("SentinelAI — Phase 2: Feature Engineering")
    print("=" * 60)

    df = load_cleaned()
    X, feat_names = select_features(df)
    y = df["Label"]

    # Remove unhelpful columns
    X = remove_constant(X)
    X = remove_correlated(X)
    feat_names = list(X.columns)

    # Encode labels  (BENIGN=0, BruteForce=1, DDoS=2, Other=3, PortScan=4)
    le = LabelEncoder()
    y_enc = le.fit_transform(y)
    print(f"\nLabel encoding:")
    for i, cls in enumerate(le.classes_):
        print(f"  {i} -> {cls:<15} ({(y_enc==i).sum():,} rows)")

    # Split BEFORE scaling (prevents data leakage)
    X_train_df, X_test_df, y_train, y_test = train_test_split(
        X, y_enc, test_size=TEST_SIZE, random_state=RANDOM_SEED, stratify=y_enc
    )
    print(f"\nSplit: {len(X_train_df):,} train / {len(X_test_df):,} test")

    # Scale (fit ONLY on train, apply to both)
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train_df)
    X_test  = scaler.transform(X_test_df)
    print("Scaled with StandardScaler (fit on train only).")

    # Save
    proc = Path(config.PROCESSED_DATA_DIR)
    proc.mkdir(parents=True, exist_ok=True)
    Path(config.MODELS_DIR).mkdir(parents=True, exist_ok=True)

    np.save(proc / "X_train.npy", X_train)
    np.save(proc / "X_test.npy",  X_test)
    np.save(proc / "y_train.npy", y_train)
    np.save(proc / "y_test.npy",  y_test)
    (proc / "feature_names.txt").write_text("\n".join(feat_names))

    joblib.dump(scaler, os.path.join(config.MODELS_DIR, "scaler.joblib"))
    joblib.dump(le,     os.path.join(config.MODELS_DIR, "label_encoder.joblib"))

    print(f"\nSaved arrays + scaler + label encoder to:")
    print(f"  {proc}")
    print(f"  {config.MODELS_DIR}")
    print(f"\nPhase 2 complete. Run Phase 3: python scripts/train_models.py")
    return feat_names, le


if __name__ == "__main__":
    main()
