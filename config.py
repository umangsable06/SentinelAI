"""
config.py — Central configuration for SentinelAI
=================================================
WHY THIS FILE EXISTS:
  Instead of scattering magic numbers and file paths all over the codebase,
  we keep them all here. If you want to change the contamination rate or
  swap a file path, you only touch ONE file — this one.

RULE: Never hardcode paths, thresholds, or model names in other files.
      Always import them from here.
"""

import os

# ─────────────────────────────────────────────
# FILE PATHS
# ─────────────────────────────────────────────

# Root directory of the project (wherever this file lives)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Where the raw CICIDS2017 CSV files go (downloaded by the user)
RAW_DATA_DIR = os.path.join(BASE_DIR, "data", "raw")

# Where cleaned/processed data is saved after Phase 1
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, "data", "processed")

# Specific file names used across phases
RAW_DATA_FILE = os.path.join(RAW_DATA_DIR, "cicids2017.csv")
PROCESSED_DATA_FILE = os.path.join(PROCESSED_DATA_DIR, "cicids2017_cleaned.csv")
FEATURES_FILE = os.path.join(PROCESSED_DATA_DIR, "features.csv")

# Where trained models are saved (Phase 3)
MODELS_DIR = os.path.join(BASE_DIR, "models")
ISOLATION_FOREST_MODEL = os.path.join(MODELS_DIR, "isolation_forest.joblib")
XGBOOST_MODEL = os.path.join(MODELS_DIR, "xgboost_model.joblib")

# SQLite database for storing alerts (Phase 6)
DB_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DB_DIR, "sentinel.db")

# Reports output folder
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

# ─────────────────────────────────────────────
# MODEL HYPERPARAMETERS
# ─────────────────────────────────────────────

# Isolation Forest: what fraction of data we expect to be anomalous
# 0.05 means "we expect about 5% of traffic to be suspicious"
# Increase this if you're getting too few alerts; decrease for fewer false alarms
ISOLATION_FOREST_CONTAMINATION = 0.05

# Random seed — keeps results reproducible every time you run the code
RANDOM_STATE = 42

# XGBoost settings
XGBOOST_N_ESTIMATORS = 100   # Number of trees to build
XGBOOST_MAX_DEPTH = 6        # How deep each tree can grow

# ─────────────────────────────────────────────
# RISK SCORING THRESHOLDS (Phase 4)
# ─────────────────────────────────────────────

# Anomaly scores below this → HIGH risk (more negative = more anomalous)
RISK_HIGH_THRESHOLD = -0.1

# Anomaly scores between this and HIGH → MEDIUM risk
RISK_MEDIUM_THRESHOLD = 0.05

# Everything above MEDIUM threshold → LOW risk

# ─────────────────────────────────────────────
# AI EXPLANATION SETTINGS (Phase 5)
# ─────────────────────────────────────────────

# Which Claude model to use for generating explanations
# claude-3-haiku is fast and cheap; swap for claude-3-5-sonnet for richer output
CLAUDE_MODEL = "claude-3-haiku-20240307"

# Maximum tokens Claude is allowed to use in its response
CLAUDE_MAX_TOKENS = 512

# ─────────────────────────────────────────────
# DASHBOARD SETTINGS (Phase 6)
# ─────────────────────────────────────────────

# How many recent alerts to show on the dashboard at once
DASHBOARD_MAX_ALERTS = 100

# Streamlit page title
DASHBOARD_TITLE = "SentinelAI — Network Threat Dashboard"
