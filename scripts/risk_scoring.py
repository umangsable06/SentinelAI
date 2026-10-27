# scripts/risk_scoring.py — Phase 4: Risk Scoring
#
# PURPOSE:
#   Take the outputs from both models (Isolation Forest anomaly score +
#   XGBoost class probabilities) and combine them into a single risk score
#   from 0 to 10, then assign a human-readable severity label:
#       Critical (>= 8.0), High (>= 6.0), Medium (>= 4.0), Low (< 4.0)
#
#   The score formula:
#       risk = (IF_WEIGHT * if_score_normalised) + (XGB_WEIGHT * xgb_score_normalised)
#
#   IF score  : already normalised to [0,1] in Phase 3 (higher = more anomalous)
#   XGB score : 1 - P(BENIGN)  — if model is confident it is NOT benign, score is high
#   Both components are scaled to [0,10] and then combined with weights.
#
# RUN: python scripts/risk_scoring.py

import sys
import os
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import joblib

import config

# ── Weights — how much each model contributes to the final score ──────────────
#   XGBoost is a supervised model trained on labelled data → more reliable
#   Isolation Forest is unsupervised → useful signal but less precise
IF_WEIGHT  = 0.4   # 40% weight to anomaly signal
XGB_WEIGHT = 0.6   # 60% weight to supervised classification confidence


# ── Severity thresholds ───────────────────────────────────────────────────────
#   These boundaries were chosen to reflect how a SOC (Security Operations
#   Centre) would triage alerts:
#     Critical — immediate response required
#     High     — investigate within the hour
#     Medium   — review in daily triage
#     Low      — log and monitor
SEVERITY_THRESHOLDS = {
    "Critical": 8.0,
    "High":     6.0,
    "Medium":   4.0,
    "Low":      0.0,
}


def compute_risk_scores(if_norm_scores: np.ndarray, y_proba: np.ndarray, le) -> np.ndarray:
    """
    Combine Isolation Forest and XGBoost outputs into one risk score per row.

    STEP-BY-STEP:

    1. IF component:
       if_norm_scores is already [0,1] (1 = very anomalous, 0 = very normal).
       Multiply by 10 to get [0,10].

    2. XGB component:
       y_proba has one probability per class per row (shape: n_rows × 5).
       The probability of BENIGN tells us how confident XGBoost is that
       the traffic is safe. If P(BENIGN) is low, the traffic is likely an attack.
       XGB threat score = 1 - P(BENIGN), scaled to [0,10].

    3. Combine:
       risk = (IF_WEIGHT × if_component) + (XGB_WEIGHT × xgb_component)
       This gives a final score in [0,10].
    """
    # Get the index of BENIGN in the label encoder
    benign_idx = list(le.classes_).index("BENIGN")

    # Step 1 — IF component scaled to [0,10]
    if_component = if_norm_scores * 10.0

    # Step 2 — XGB component: how NOT-benign is this row?
    p_benign = y_proba[:, benign_idx]          # probability of being benign
    xgb_component = (1.0 - p_benign) * 10.0   # invert: high attack confidence → high score

    # Step 3 — Weighted combination
    risk_scores = (IF_WEIGHT * if_component) + (XGB_WEIGHT * xgb_component)

    # Clip to [0,10] to handle any floating-point edge cases
    return np.clip(risk_scores, 0.0, 10.0)


def assign_severity(score: float) -> str:
    """
    Map a numeric risk score to a human-readable severity level.
    Thresholds are defined in SEVERITY_THRESHOLDS above.
    """
    if score >= SEVERITY_THRESHOLDS["Critical"]:
        return "Critical"
    elif score >= SEVERITY_THRESHOLDS["High"]:
        return "High"
    elif score >= SEVERITY_THRESHOLDS["Medium"]:
        return "Medium"
    else:
        return "Low"


def build_alert_dataframe(
    risk_scores:  np.ndarray,
    y_pred:       np.ndarray,
    y_test:       np.ndarray,
    y_proba:      np.ndarray,
    if_scores:    np.ndarray,
    le,
    cleaned_df:   pd.DataFrame,
    test_indices: np.ndarray,
) -> pd.DataFrame:
    """
    Assemble one row per network flow with:
      - Source/Destination IP (from cleaned data)
      - Predicted attack class
      - True label (for evaluation)
      - Risk score
      - Severity label
      - Individual model component scores
    """
    class_names = list(le.classes_)

    alerts = pd.DataFrame({
        "Source IP":       cleaned_df.iloc[test_indices]["Source IP"].values,
        "Destination IP":  cleaned_df.iloc[test_indices]["Destination IP"].values,
        "True Label":      [class_names[i] for i in y_test],
        "Predicted Label": [class_names[i] for i in y_pred],
        "Risk Score":      np.round(risk_scores, 2),
        "Severity":        [assign_severity(s) for s in risk_scores],
        "IF Score (0-10)": np.round(if_scores * 10.0, 2),
        "XGB Score (0-10)":np.round((1 - y_proba[:, list(le.classes_).index("BENIGN")]) * 10.0, 2),
    })

    # Sort by risk score descending — highest risk at the top
    alerts = alerts.sort_values("Risk Score", ascending=False).reset_index(drop=True)
    return alerts


def print_summary(alerts: pd.DataFrame):
    """Print a clear, readable summary of the scoring results."""
    print("\n" + "=" * 60)
    print("RISK SCORING SUMMARY")
    print("=" * 60)

    total = len(alerts)
    print(f"Total flows scored: {total:,}\n")

    print("Severity breakdown:")
    for sev in ["Critical", "High", "Medium", "Low"]:
        count = (alerts["Severity"] == sev).sum()
        pct   = count / total * 100
        bar   = "#" * int(pct / 2)
        print(f"  {sev:<10} {count:>5,}  ({pct:5.1f}%)  {bar}")

    print(f"\nRisk score statistics:")
    print(f"  Mean:   {alerts['Risk Score'].mean():.2f}")
    print(f"  Max:    {alerts['Risk Score'].max():.2f}")
    print(f"  Min:    {alerts['Risk Score'].min():.2f}")
    print(f"  Median: {alerts['Risk Score'].median():.2f}")

    print("\nTop 10 highest-risk flows:")
    print(alerts[[
        "Source IP", "Predicted Label", "Risk Score", "Severity",
        "IF Score (0-10)", "XGB Score (0-10)"
    ]].head(10).to_string(index=False))

    print("\nSample of LOW risk flows:")
    low = alerts[alerts["Severity"] == "Low"]
    if len(low) > 0:
        print(low[[
            "Source IP", "Predicted Label", "Risk Score", "Severity"
        ]].tail(5).to_string(index=False))


def main():
    print("=" * 60)
    print("SentinelAI — Phase 4: Risk Scoring")
    print("=" * 60)

    # ── Load Phase 3 outputs ──────────────────────────────────────────────────
    proc = Path(config.PROCESSED_DATA_DIR)

    if_norm_scores = np.load(proc / "if_norm_scores.npy")
    y_proba        = np.load(proc / "y_proba_xgb.npy")
    y_pred         = np.load(proc / "y_pred_xgb.npy")
    y_test         = np.load(proc / "y_test.npy")
    le             = joblib.load(os.path.join(config.MODELS_DIR, "label_encoder.joblib"))
    cleaned_df     = pd.read_csv(proc / "cleaned_data.csv")

    print(f"Loaded {len(if_norm_scores):,} test-set flows.")
    print(f"Classes: {list(le.classes_)}")

    # ── We need the test-set row indices to look up IPs from cleaned_data ────
    # The test set was an 80/20 stratified split. We re-derive the indices
    # using the same seed to get the matching rows from cleaned_data.
    from sklearn.model_selection import train_test_split

    n_total = len(cleaned_df)
    all_idx = np.arange(n_total)
    labels  = cleaned_df["Label"].values
    _, test_idx = train_test_split(
        all_idx, test_size=0.2, random_state=42, stratify=labels
    )

    # ── Compute risk scores ───────────────────────────────────────────────────
    print("\nComputing risk scores...")
    risk_scores = compute_risk_scores(if_norm_scores, y_proba, le)

    # ── Build alert dataframe ─────────────────────────────────────────────────
    alerts = build_alert_dataframe(
        risk_scores, y_pred, y_test, y_proba,
        if_norm_scores, le, cleaned_df, test_idx
    )

    # ── Print summary ─────────────────────────────────────────────────────────
    print_summary(alerts)

    # ── Save results ──────────────────────────────────────────────────────────
    out_path = proc / "alerts.csv"
    alerts.to_csv(out_path, index=False)
    print(f"\nSaved: {out_path}")
    print(f"(This file is what the dashboard will read to display alerts.)")

    print("\n" + "=" * 60)
    print("Phase 4 complete.")
    print("Run Phase 5 with: python scripts/ai_explanation.py")
    print("=" * 60)

    return alerts


if __name__ == "__main__":
    main()
