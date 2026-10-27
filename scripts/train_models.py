# scripts/train_models.py — Phase 3: Train Two Models and Evaluate
#
# MODEL A — Isolation Forest (UNSUPERVISED)
#   Trained on BENIGN rows only. Learns what "normal" looks like.
#   Anything that deviates from normal gets a high anomaly score.
#
# MODEL B — XGBoost (SUPERVISED)
#   Trained on all labelled classes. Predicts the specific attack type.
#
# Together they give us: anomaly signal (broad net) + class label (specific name).
#
# RUN: python scripts/train_models.py

import sys
import os
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import joblib
import matplotlib
matplotlib.use("Agg")          # Non-interactive backend — works without a display
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.ensemble import IsolationForest
from sklearn.metrics import (
    classification_report, confusion_matrix,
    accuracy_score, precision_score, recall_score, f1_score,
    precision_recall_fscore_support,
)
from xgboost import XGBClassifier

import config


# ── Load Phase 2 outputs ──────────────────────────────────────────────────────

def load_data():
    proc = Path(config.PROCESSED_DATA_DIR)
    X_train    = np.load(proc / "X_train.npy")
    X_test     = np.load(proc / "X_test.npy")
    y_train    = np.load(proc / "y_train.npy")
    y_test     = np.load(proc / "y_test.npy")
    le         = joblib.load(os.path.join(config.MODELS_DIR, "label_encoder.joblib"))
    feat_names = (proc / "feature_names.txt").read_text().splitlines()
    print(f"Loaded: X_train={X_train.shape}  X_test={X_test.shape}")
    print(f"Classes: {list(le.classes_)}")
    return X_train, X_test, y_train, y_test, le, feat_names


# ── Model A: Isolation Forest ─────────────────────────────────────────────────

def train_isolation_forest(X_train, y_train, le):
    """
    HOW IT WORKS:
    Build 100 random decision trees. Each tree randomly picks a feature and
    a random split point, dividing the data in half, repeating until every
    point is alone (isolated).

    - NORMAL points sit in dense clusters -> need MANY splits to isolate (long path).
    - ANOMALOUS points are outliers -> isolated in FEW splits (short path).

    The anomaly score = average path length across all trees.
    Short path = anomaly. Long path = normal.

    We train ONLY on BENIGN rows so the model's idea of "normal" is benign traffic.
    Anything that looks different from that gets flagged.
    """
    benign_idx = list(le.classes_).index("BENIGN")
    X_benign = X_train[y_train == benign_idx]
    print(f"\n[Isolation Forest] Training on {len(X_benign):,} BENIGN rows only...")

    model = IsolationForest(
        n_estimators=config.ISOLATION_FOREST_CONTAMINATION and 100,
        contamination=config.ISOLATION_FOREST_CONTAMINATION,
        random_state=config.RANDOM_STATE,
        n_jobs=-1,
    )
    # n_estimators workaround: config doesn't define it separately, use 100
    model.set_params(n_estimators=100)
    model.fit(X_benign)
    print("[Isolation Forest] Training complete.")
    return model


def evaluate_isolation_forest(model, X_test, y_test, le):
    """
    Isolation Forest can't predict specific classes — it only outputs:
      - predict(): +1 = normal, -1 = anomaly
      - score_samples(): raw score (more negative = more anomalous)

    So we evaluate it as a BINARY detector:
    Does it correctly flag attack rows as anomalies?
    """
    benign_idx = list(le.classes_).index("BENIGN")
    y_binary_true = (y_test != benign_idx).astype(int)   # 0=benign, 1=attack
    y_binary_pred = (model.predict(X_test) == -1).astype(int)

    # Raw anomaly scores — flip sign so higher = more anomalous
    raw_scores = -model.score_samples(X_test)
    # Normalise to [0, 1]
    norm_scores = (raw_scores - raw_scores.min()) / (raw_scores.max() - raw_scores.min() + 1e-9)

    acc = accuracy_score(y_binary_true, y_binary_pred)
    p   = precision_score(y_binary_true, y_binary_pred, zero_division=0)
    r   = recall_score(y_binary_true, y_binary_pred, zero_division=0)
    f   = f1_score(y_binary_true, y_binary_pred, zero_division=0)

    print(f"\n[Isolation Forest] Binary anomaly detection evaluation:")
    print(f"  Accuracy:  {acc:.3f}")
    print(f"  Precision: {p:.3f}  (of all rows flagged anomaly, what fraction was a real attack?)")
    print(f"  Recall:    {r:.3f}  (of all real attacks, what fraction did IF catch?)")
    print(f"  F1:        {f:.3f}")

    return norm_scores


# ── Model B: XGBoost ──────────────────────────────────────────────────────────

def train_xgboost(X_train, y_train, le):
    """
    HOW IT WORKS:
    XGBoost = Extreme Gradient Boosting.

    Step 1: Build a simple decision tree. It makes some mistakes.
    Step 2: Build a second tree that focuses on the rows the first tree got wrong.
    Step 3: Build a third tree that fixes what's still wrong. Repeat 200 times.

    Final prediction = weighted vote of all 200 trees.

    This "correcting mistakes iteratively" technique is called GRADIENT BOOSTING.
    The "extreme" part means it uses mathematical optimisation to make it fast.

    Unlike Isolation Forest, XGBoost needs LABELS — it learns by example.
    """
    n_classes = len(le.classes_)
    print(f"\n[XGBoost] Training on {len(X_train):,} rows, {n_classes} classes...")
    model = XGBClassifier(
        n_estimators=config.XGBOOST_N_ESTIMATORS,
        max_depth=config.XGBOOST_MAX_DEPTH,
        learning_rate=0.1,
        objective="multi:softprob",
        num_class=n_classes,
        random_state=config.RANDOM_STATE,
        n_jobs=-1,
        eval_metric="mlogloss",
        verbosity=0,
    )
    model.fit(X_train, y_train)
    print("[XGBoost] Training complete.")
    return model


def evaluate_xgboost(model, X_test, y_test, le, feat_names):
    """
    Evaluate on the held-out test set (data the model has never seen).
    Print a full classification report + save charts.
    """
    y_pred  = model.predict(X_test)
    y_proba = model.predict_proba(X_test)
    class_names = list(le.classes_)

    print("\n" + "=" * 60)
    print("[XGBoost] Classification Report")
    print("=" * 60)
    print(classification_report(y_test, y_pred, target_names=class_names, zero_division=0))

    print("What these metrics mean:")
    print("  Precision — Of all 'DDoS' predictions, how many were actually DDoS?")
    print("              Low = many false alarms.")
    print("  Recall    — Of all actual DDoS rows in the test set, how many did we catch?")
    print("              Low = attacks slipping through undetected.")
    print("  F1        — Harmonic mean of Precision and Recall.")
    print("  Support   — Number of test rows for each class.")
    print()

    # Flag weak classes
    prec, rec, f1, sup = precision_recall_fscore_support(
        y_test, y_pred, labels=list(range(len(class_names))), zero_division=0
    )
    print("Weakness analysis:")
    weak = False
    for i, cls in enumerate(class_names):
        if f1[i] < 0.70 and sup[i] > 0:
            print(f"  WARNING: {cls}: F1={f1[i]:.2f}  Precision={prec[i]:.2f}  Recall={rec[i]:.2f}  Support={sup[i]}")
            weak = True
    if not weak:
        print("  All classes with test samples have F1 >= 0.70.")
    print()
    print("NOTE: Weakness on 'Other' is expected — it is a catch-all class with")
    print("few and varied examples. BruteForce can look like normal SSH traffic.")

    save_confusion_matrix(y_test, y_pred, class_names)
    save_feature_importance(model, feat_names)

    return y_pred, y_proba


def save_confusion_matrix(y_true, y_pred, class_names):
    """
    A confusion matrix grid shows correct predictions (diagonal) vs
    mistakes (off-diagonal). For example: row=DDoS, col=Other means
    a DDoS was misclassified as Other.
    """
    os.makedirs(config.REPORTS_DIR, exist_ok=True)
    cm = confusion_matrix(y_true, y_pred, labels=list(range(len(class_names))))
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(
        cm, annot=True, fmt="d", cmap="Blues",
        xticklabels=class_names, yticklabels=class_names, ax=ax,
    )
    ax.set_xlabel("Predicted label", fontsize=12)
    ax.set_ylabel("True label", fontsize=12)
    ax.set_title("XGBoost Confusion Matrix (Test Set)", fontsize=14)
    plt.tight_layout()
    out = os.path.join(config.REPORTS_DIR, "confusion_matrix.png")
    plt.savefig(out, dpi=150)
    plt.close()
    print(f"Saved: {out}")


def save_feature_importance(model, feat_names):
    """
    Shows which features the XGBoost model used most when splitting its trees.
    High importance = that column was a strong signal for distinguishing attack types.
    """
    importance = model.feature_importances_
    top_n = min(20, len(feat_names))
    idx = np.argsort(importance)[::-1][:top_n]
    top_names  = [feat_names[i] for i in idx]
    top_scores = [importance[i]  for i in idx]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(top_names[::-1], top_scores[::-1], color="steelblue")
    ax.set_xlabel("Importance Score", fontsize=12)
    ax.set_title(f"XGBoost Top {top_n} Feature Importances", fontsize=14)
    plt.tight_layout()
    out = os.path.join(config.REPORTS_DIR, "feature_importance.png")
    plt.savefig(out, dpi=150)
    plt.close()
    print(f"Saved: {out}")


# ── Save models ───────────────────────────────────────────────────────────────

def save_models(if_model, xgb_model):
    os.makedirs(config.MODELS_DIR, exist_ok=True)
    joblib.dump(if_model,  config.ISOLATION_FOREST_MODEL)
    joblib.dump(xgb_model, config.XGBOOST_MODEL)
    print(f"\nSaved models:")
    print(f"  {config.ISOLATION_FOREST_MODEL}")
    print(f"  {config.XGBOOST_MODEL}")


# ── Main pipeline ─────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("SentinelAI — Phase 3: Train Models and Evaluate")
    print("=" * 60)

    X_train, X_test, y_train, y_test, le, feat_names = load_data()

    # Model A: Isolation Forest
    if_model   = train_isolation_forest(X_train, y_train, le)
    norm_scores = evaluate_isolation_forest(if_model, X_test, y_test, le)

    # Model B: XGBoost
    xgb_model        = train_xgboost(X_train, y_train, le)
    y_pred, y_proba   = evaluate_xgboost(xgb_model, X_test, y_test, le, feat_names)

    # Save both models
    save_models(if_model, xgb_model)

    # Save test predictions for Phase 4 (risk scoring)
    proc = Path(config.PROCESSED_DATA_DIR)
    np.save(proc / "y_pred_xgb.npy",    y_pred)
    np.save(proc / "y_proba_xgb.npy",   y_proba)
    np.save(proc / "if_norm_scores.npy", norm_scores)
    print(f"Saved test predictions to {proc}")

    print("\n" + "=" * 60)
    print("Phase 3 complete.")
    print("Run Phase 4 with: python scripts/risk_scoring.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
