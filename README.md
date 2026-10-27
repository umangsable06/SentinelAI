# SentinelAI — AI-Powered Network Threat Detection

A college project (MCA) that uses machine learning and AI to detect suspicious
network traffic in real time, explain threats in plain English, and display them
on an interactive dashboard.

---

## Project Structure

```
Sentinel AI/
├── data/
│   ├── raw/          ← Put your CICIDS2017 CSV files here
│   └── processed/    ← Cleaned data is saved here automatically
├── models/           ← Trained ML models saved here (.joblib)
├── src/              ← Core Python modules (cleaning, training, scoring)
├── dashboard/        ← Streamlit web dashboard files
├── scripts/          ← Utility scripts (simulation, DB reset, etc.)
├── reports/          ← Auto-generated HTML/PDF reports
├── config.py         ← ALL settings in one place (paths, thresholds, model names)
├── requirements.txt  ← All Python packages needed
├── .env.example      ← Template for your API key (copy → .env)
└── LEARNING_NOTES.md ← Phase-by-phase learning guide for viva prep
```

---

## Setup Instructions

### 1. Create and activate a virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up your API key
```bash
# Copy the example file
copy .env.example .env      # Windows
cp .env.example .env        # Mac/Linux

# Then open .env and paste your Anthropic API key
```

### 4. Download the dataset
- Go to: https://www.unb.ca/cic/datasets/ids-2017.html
- Download the CSV files
- Place them in `data/raw/`

---

## Running Each Phase

Each phase adds a new capability. Run them in order:

| Phase | What it does | Command |
|-------|-------------|---------|
| 0 | Setup (done) | — |
| 1 | Load & clean data | `python scripts/phase1_load_data.py` |
| 2 | Feature engineering | `python scripts/phase2_features.py` |
| 3 | Train models | `python scripts/phase3_train.py` |
| 4 | Risk scoring | `python scripts/phase4_risk_score.py` |
| 5 | AI explanations | `python scripts/phase5_explain.py` |
| 6 | Dashboard | `streamlit run dashboard/app.py` |
| 7 | Simulation | `python scripts/phase7_simulate.py` |

---

## Tech Stack

| Tool | Purpose |
|------|---------|
| Pandas / NumPy | Data loading and manipulation |
| scikit-learn | Isolation Forest (unsupervised anomaly detection) |
| XGBoost | Supervised classification (attack vs. benign) |
| joblib | Save and load trained models |
| Plotly | Interactive charts |
| Streamlit | Web dashboard (no HTML/CSS needed) |
| SQLite | Local database to store alerts |
| Anthropic Claude | Generate plain-English threat explanations |
| python-dotenv | Load API keys from .env file |

---

## Dataset

**CICIDS2017** — Canadian Institute for Cybersecurity Intrusion Detection dataset.  
Contains labeled network traffic: benign traffic and multiple attack types
(DDoS, Port Scan, Brute Force, Web Attacks, Infiltration, Botnet).

---

## Important Notes

- This is a **local** project — no cloud, no Docker required.
- Your API key lives in `.env` which is listed in `.gitignore` — it will never be committed.
- All tuneable settings (thresholds, model names, file paths) are in `config.py`.
