# progress.py — Visual project progress checker
# RUN: streamlit run progress.py

import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="SentinelAI — Project Progress",
    page_icon="🛡️",
    layout="centered",
)

base = Path(__file__).parent

# ── Phase definitions ─────────────────────────────────────────────────────────
phases = [
    {
        "name":  "Phase 0 — Project Setup",
        "icon":  "⚙️",
        "desc":  "Folder structure, config.py, requirements.txt, virtual environment, .env template",
        "files": [
            "config.py",
            "requirements.txt",
            ".env.example",
            ".gitignore",
        ],
        "what": "Set up the project skeleton — all folders, configuration files, and the environment before any ML code.",
    },
    {
        "name":  "Phase 1 — Data Loading & Cleaning",
        "icon":  "📂",
        "desc":  "Load CICIDS2017 CSV files, clean NaN/Infinity, fix class imbalance, save cleaned dataset",
        "files": [
            "scripts/load_data.py",
            "data/processed/cleaned_data.csv",
        ],
        "what": "Loaded and cleaned the CICIDS2017 network traffic dataset. Removed bad rows, mapped 18 attack types into 5 classes, fixed class imbalance by downsampling BENIGN traffic.",
    },
    {
        "name":  "Phase 2 — Feature Engineering",
        "icon":  "🔧",
        "desc":  "Select features, remove redundant columns, encode labels, train/test split, StandardScaler",
        "files": [
            "scripts/feature_engineering.py",
            "data/processed/X_train.npy",
            "data/processed/X_test.npy",
            "data/processed/feature_names.txt",
            "models/scaler.joblib",
            "models/label_encoder.joblib",
        ],
        "what": "Selected 77 meaningful features from 80+ columns. Split data 80/20 into train/test BEFORE scaling to prevent data leakage. Saved scaler and label encoder for reuse.",
    },
    {
        "name":  "Phase 3 — Model Training & Evaluation",
        "icon":  "🤖",
        "desc":  "Train Isolation Forest (anomaly detection) + XGBoost (attack classification), evaluate honestly",
        "files": [
            "scripts/train_models.py",
            "models/isolation_forest.joblib",
            "models/xgboost_model.joblib",
            "reports/confusion_matrix.png",
            "reports/feature_importance.png",
            "data/processed/y_pred_xgb.npy",
            "data/processed/if_norm_scores.npy",
        ],
        "what": "Trained two complementary models. Isolation Forest detects anomalies without labels (catches zero-day attacks). XGBoost classifies known attack types with high accuracy. Saved confusion matrix and feature importance charts.",
    },
    {
        "name":  "Phase 4 — Risk Scoring",
        "icon":  "🎯",
        "desc":  "Combine both model outputs into a 0–10 risk score with Critical/High/Medium/Low severity",
        "files": [
            "scripts/risk_scoring.py",
            "data/processed/alerts.csv",
        ],
        "what": "Combined Isolation Forest anomaly score (40% weight) and XGBoost attack confidence (60% weight) into a single 0–10 risk score. Assigned severity labels used by the dashboard.",
    },
    {
        "name":  "Phase 5 — AI Explanation",
        "icon":  "💬",
        "desc":  "Use Claude (Anthropic) to generate plain-English explanations for each alert",
        "files": [
            "scripts/ai_explanation.py",
        ],
        "what": "For each high-risk alert, call the Claude API to generate a plain-English explanation of why the traffic is suspicious and what action to take.",
    },
    {
        "name":  "Phase 6 — Database",
        "icon":  "🗄️",
        "desc":  "Store all alerts in SQLite database for persistent history and querying",
        "files": [
            "src/database.py",
            "data/sentinel.db",
        ],
        "what": "Persist alerts in a local SQLite database so the dashboard can show historical data and the system maintains memory across runs.",
    },
    {
        "name":  "Phase 7 — Dashboard",
        "icon":  "📊",
        "desc":  "Streamlit web dashboard with live monitoring, alert table, charts, and AI explanations",
        "files": [
            "dashboard/app.py",
        ],
        "what": "Full interactive web dashboard showing real-time threat monitoring, alert severity breakdown, model performance charts, and AI-generated explanations.",
    },
]

# ── Calculate progress ────────────────────────────────────────────────────────
done_count = 0
for p in phases:
    p["done"] = all((base / f).exists() for f in p["files"])
    if p["done"]:
        done_count += 1

pct = int(done_count / len(phases) * 100)

# ── Page header ───────────────────────────────────────────────────────────────
st.title("🛡️ SentinelAI — Project Progress")
st.caption("AI-Powered Network Intrusion Detection System")

st.divider()

# ── Overall progress bar ──────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
col1.metric("Phases Complete", f"{done_count} / {len(phases)}")
col2.metric("Progress", f"{pct}%")
col3.metric("Remaining", f"{len(phases) - done_count} phases")

st.progress(pct / 100)

st.divider()

# ── Phase cards ───────────────────────────────────────────────────────────────
st.subheader("Phase Breakdown")

for p in phases:
    if p["done"]:
        color  = "✅"
        status = "**Complete**"
        bg     = "normal"
    else:
        color  = "⏳"
        status = "**Pending**"
        bg     = "normal"

    with st.expander(f"{color}  {p['name']}  —  {status}", expanded=False):
        st.write(f"**What this phase does:**  {p['what']}")
        st.write(f"**Key outputs:**  {p['desc']}")

        st.write("**Files / Outputs:**")
        for f in p["files"]:
            exists = (base / f).exists()
            icon   = "🟢" if exists else "🔴"
            st.write(f"  {icon}  `{f}`")

st.divider()

# ── What's been built ─────────────────────────────────────────────────────────
st.subheader("What Has Been Built So Far")

built = [p for p in phases if p["done"]]
for p in built:
    st.success(f"{p['icon']}  **{p['name']}** — {p['what']}")

pending = [p for p in phases if not p["done"]]
if pending:
    st.subheader("Still To Build")
    for p in pending:
        st.info(f"{p['icon']}  **{p['name']}** — {p['what']}")

st.divider()
st.caption("SentinelAI — Built phase by phase as a learning project. Each phase builds on the previous one.")
