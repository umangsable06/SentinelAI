# SentinelAI — Learning Notes
> Your viva preparation guide. Updated after every phase.
> Read each section before your viva — the Q&As are written to help you explain things in your own words.

---

## Phase 0 — Project Setup

### What This Phase Does
Phase 0 creates the skeleton of the project — all the folders and configuration files — before writing a single line of real logic. Think of it like building the rooms of a house before putting in furniture. No machine learning happens here.

### Folder Structure

| Folder / File | What it is | Why it exists |
|---|---|---|
| `data/raw/` | Original CICIDS2017 CSV files | Keep raw data untouched — a standard data science practice |
| `data/processed/` | Cleaned and transformed data | Separation: raw data is never overwritten |
| `models/` | Saved trained model files | Training takes time; save once, reuse forever |
| `scripts/` | One runnable Python file per phase | Clean entry points; one script = one job |
| `src/` | Reusable Python modules | Logic shared between scripts lives here |
| `dashboard/` | Streamlit web dashboard | UI code separate from ML logic |
| `reports/` | Generated charts and images | Output for submission and the dashboard |
| `config.py` | Central settings file | One place to change any path, threshold, or parameter |
| `requirements.txt` | All Python packages needed | Anyone can recreate the environment with one command |
| `.env.example` | API key template | Shows what secrets are needed without exposing them |
| `.gitignore` | Git exclusion list | Prevents secrets and large files being uploaded to GitHub |

### Key Concepts

**Virtual environment** — An isolated Python installation just for this project. Without it, installing a package for one project could break another. The `venv/` folder contains this isolated environment.

**requirements.txt** — A text file listing every Python library with a minimum version. Running `pip install -r requirements.txt` installs everything at once, making the project fully reproducible on any computer.

**config.py** — Instead of writing the same file path or threshold number in ten different scripts, you define it once here and import it everywhere. If you need to change a value, you change it in exactly one place.

**.env file** — Stores secrets like the Anthropic API key. If you wrote the key directly in your code and pushed to GitHub, anyone could steal it. The `.env` file is listed in `.gitignore` so it is never committed. The `python-dotenv` library reads it at runtime.

**joblib** — A library for saving Python objects (especially ML models) to disk. Training a model can take minutes on a laptop. Saving it means you train once and load instantly every time after that.

### Viva Q&A

**Q: Why use a virtual environment instead of installing packages globally?**
A: Different projects may need different versions of the same library. Global installation causes version conflicts. A virtual environment gives each project its own isolated Python installation, so they never interfere with each other.

**Q: Why is the API key stored in a .env file and not in the code?**
A: If the key is hardcoded in source code and the code is pushed to GitHub, anyone who sees it can use my Anthropic account and run up charges. The .env file is excluded from Git via .gitignore so it never leaves my machine. The code reads the key at runtime using python-dotenv.

**Q: What is config.py and why is it better than hardcoding values?**
A: config.py is the single source of truth for every setting — file paths, model names, thresholds, weights. If I want to change the risk scoring threshold or swap a file path, I change it in one place and every script that imports it picks up the change automatically. Hardcoding the same value in ten files is a maintenance nightmare.

---

## Phase 1 — Data Loading and Cleaning

### What This Phase Does
The script `scripts/load_data.py` loads the raw CICIDS2017 CSV files, cleans structural problems in the data, fixes class imbalance, and saves a clean dataset ready for Phase 2. If no CSV files are found, it generates a small synthetic dataset so the rest of the pipeline can still run.

### About the CICIDS2017 Dataset
CICIDS2017 (Canadian Institute for Cybersecurity Intrusion Detection System 2017) is a publicly available, labelled network traffic dataset. Researchers set up a realistic office network and ran real attack tools against it over several days while recording all traffic. Each row in the dataset represents one **network flow** — a summary of all packets between two IP addresses during one connection.

The dataset contains labels for many attack types: DDoS, PortScan, FTP-Patator, SSH-Patator, Bot, Web Attacks, Heartbleed, and more. This project collapses them into 5 classes: **BENIGN, DDoS, PortScan, BruteForce, Other**.

**Important limitation:** CICIDS2017 is lab-generated traffic, not traffic from a real company network. Attack patterns in the real world may differ. This is acknowledged as a project limitation.

### The 9 Cleaning Steps

**1. Load CSVs** — Up to 50,000 rows per file are loaded (controlled by `SAMPLE_SIZE` in config.py) to keep training fast on a laptop.

**2. Clean column names** — CICIDS2017 column names sometimes have a leading space (` Label` instead of `Label`). These are stripped to prevent errors later.

**3. Replace infinity and drop NaN** — Some flow statistics divide by flow duration. If duration is zero, the result is infinity. ML models cannot process infinity or NaN. Infinity is replaced with NaN, then all NaN rows are dropped. Dropping is safer than guessing a fill value, which would introduce fake patterns.

**4. Drop duplicates** — Some flows get recorded twice. Duplicates add noise without adding information.

**5. Map labels to 5 classes** — 18 specific CICIDS2017 sub-types are collapsed into 5 meaningful classes using a mapping table. Unknown labels become "Other".

**6. Simulate IP addresses** — CICIDS2017 does not always include IP columns. When missing, plausible-looking IPs are generated: attackers use `10.0.x.x`, victims use `192.168.x.x`. These are clearly marked as SIMULATED — not real addresses. They exist only for the dashboard display.

**7. Fix class imbalance** — About 80% of CICIDS2017 rows are BENIGN. A model trained on this could score 80% accuracy by predicting "BENIGN" for everything — without catching a single attack. This is called **class imbalance**. Fix: keep only 3× as many BENIGN rows as the largest attack class (controlled by `BENIGN_DOWNSAMPLE_RATIO`).

**8. Print summary** — Final shape and label distribution are printed so the user can verify the data looks correct.

**9. Save cleaned_data.csv** — Saved to `data/processed/cleaned_data.csv`. This is what Phase 2 reads.

### Synthetic Fallback
When no CSV is found in `data/raw/`, a 2,000-row fake dataset is generated automatically. DDoS rows get 50× higher flow rates, PortScan gets 5× higher packet rates, others get generic random values. This lets the entire pipeline run end-to-end for demonstration. It is clearly labelled as not real traffic throughout.

### Key Concepts

**Network flow** — A summary of all packets exchanged between two IPs during one connection. Instead of logging millions of individual packets, CICIDS2017 logs one row per flow with statistics.

**NaN (Not a Number)** — A placeholder for missing or invalid data. Pandas uses it where a value doesn't exist or a calculation failed.

**Class imbalance** — When one category has far more rows than others. Can cause a model to ignore minority classes because predicting the majority class always gives high accuracy.

**Downsampling** — Randomly removing rows from the majority class to create a more balanced training set.

### Viva Q&A

**Q: What is the CICIDS2017 dataset and why did you choose it?**
A: CICIDS2017 is a publicly available, labelled network intrusion detection dataset from the Canadian Institute for Cybersecurity. It contains real attack traffic captured in a controlled lab environment across multiple days. I chose it because it is widely used in academic IDS research, is freely downloadable, and contains the attack types most relevant to this project.

**Q: Why do you drop rows with infinity or NaN instead of filling them?**
A: Infinity values come from division by zero in flow statistics — for example, bytes per second when the flow duration is zero. These are measurement errors, not meaningful data. Filling them with a guess like zero or the mean would introduce false patterns. Dropping them is safer — we lose a small number of rows but the remaining data is trustworthy.

**Q: What is class imbalance and how did you address it?**
A: Class imbalance means one class dominates the dataset. In CICIDS2017, about 80% of rows are BENIGN. A naive model could score 80% accuracy by always predicting BENIGN — never detecting a single attack. I addressed this by downsampling: randomly removing excess BENIGN rows until the ratio of BENIGN to attacks is 3:1. This forces the model to actually learn attack patterns.

---

## Phase 2 — Feature Engineering

### What This Phase Does
The script `scripts/feature_engineering.py` takes the cleaned dataset and prepares the numerical arrays that ML models train on. It selects useful columns, removes redundant ones, encodes text labels as numbers, splits into training and test sets, and scales all values to the same range.

### Step 1 — Feature Selection
From 80+ columns, only the columns describing network behaviour are kept, grouped by what they measure:

- **Timing** (Flow Duration, Inter-Arrival Time): DDoS attacks are so fast that gaps between packets drop near zero. PortScan creates many rapid short flows.
- **Volume** (Total Packets, Total Bytes): DDoS sends enormous volumes. BruteForce sends many small login attempts.
- **Rate** (Bytes/s, Packets/s): These spike dramatically during DDoS.
- **Packet size statistics** (Mean, Std, Min, Max): PortScan uses tiny probe packets. Normal HTTPS has larger, varied packets.
- **TCP flag counts** (SYN, FIN, RST, PSH, ACK): PortScan sends SYN without completing handshakes. BruteForce shows repeated connection attempts.
- **Destination Port**: SSH BruteForce targets port 22. HTTP attacks target ports 80 and 443.

Metadata columns (Source IP, Destination IP) are excluded — they are identifiers, not features.

### Step 2 — Remove Constant Columns
If a column has the same value in every row (standard deviation = 0), the model learns nothing from it. These are dropped automatically.

### Step 3 — Remove Highly Correlated Columns
If two columns have a correlation above 0.98, they are measuring almost the same thing. Keeping both adds no information but slows training. One from each highly correlated pair is dropped.

### Step 4 — Encode Labels
ML models need numbers, not text. `LabelEncoder` converts class names to integers alphabetically:
- BENIGN=0, BruteForce=1, DDoS=2, Other=3, PortScan=4

The encoder is saved to `models/label_encoder.joblib` so predictions can be converted back to readable names later.

### Step 5 — Train/Test Split (Before Scaling)
80% of data → training. 20% → held-out test set. The split uses **stratification** so each class has the same proportion in both sets.

**This split happens BEFORE scaling to prevent data leakage.**

**Data leakage explained:** If you scale all data first and then split, the scaler calculates its mean and standard deviation using test set values. The test set is supposed to simulate future unknown traffic — it must not influence the training process at all, not even indirectly. Correct order: split first → fit scaler on training data only → apply same scaler to test data.

**Analogy:** Like a student seeing the exam answers before the exam. The score looks great but does not reflect real knowledge.

### Step 6 — StandardScaler
Features have vastly different ranges. Flow Duration can be 0–120,000,000 microseconds. SYN Flag Count is 0–5. Without scaling, the large-valued features dominate the model just because of their size, not their importance. StandardScaler converts every column to mean=0, standard deviation=1:

```
scaled_value = (original_value - column_mean) / column_std
```

The scaler is saved to `models/scaler.joblib` so live predictions later use the exact same transformation.

### Outputs Saved
- `data/processed/X_train.npy` — scaled training features (1,600 rows × 77 features)
- `data/processed/X_test.npy` — scaled test features (400 rows × 77 features)
- `data/processed/y_train.npy` — training labels (integers)
- `data/processed/y_test.npy` — test labels (integers)
- `data/processed/feature_names.txt` — ordered list of feature column names
- `models/scaler.joblib` — fitted StandardScaler
- `models/label_encoder.joblib` — fitted LabelEncoder

### Viva Q&A

**Q: What is data leakage and why is it a problem?**
A: Data leakage means the test set accidentally influences the training process, making the model appear better than it really is. In this project, the main risk is fitting the StandardScaler on all data before splitting. I prevent this by always splitting first, then fitting the scaler on training data only, and applying it to the test set without refitting.

**Q: Why do you scale features and which scaler did you use?**
A: I use StandardScaler, which converts each feature to mean 0, standard deviation 1. Features have very different ranges — Flow Duration can be millions while flag counts are 0 or 1. Without scaling, large-valued features dominate the model not because they are important, but because they are numerically big. Scaling gives every feature an equal starting position.

**Q: Why remove highly correlated features?**
A: If two columns have a correlation above 0.98, they are almost identical — they carry the same information. Keeping both does not help the model but does slow down training and can cause instability. Removing redundant features makes the model leaner and faster without losing accuracy.

---

## Phase 3 — Model Training and Evaluation

### What This Phase Does
The script `scripts/train_models.py` trains two different machine learning models and evaluates them honestly on the held-out test set. Both models are saved to disk and two evaluation charts are produced.

### Model A — Isolation Forest (Unsupervised)

Trained only on BENIGN rows. It learns what "normal" traffic looks like. Anything that deviates from normal gets a high anomaly score.

**How it works:** The algorithm builds 100 random decision trees. Each tree randomly picks a feature and a random cut-point, dividing the data in half. It keeps splitting until every data point is alone (isolated).

- Normal points sit in dense clusters — they need MANY splits to isolate (long path through the tree).
- Anomalous points are outliers far from the cluster — they get isolated in FEW splits (short path).

The anomaly score = average path length across all 100 trees. Short path = anomaly. Long path = normal.

Because it is trained only on BENIGN traffic, it defines "normal" as benign patterns. Any traffic that looks different — including attack types it has never been told about — will have a short path and high anomaly score. This is called **zero-day detection**: catching novel attacks without having seen them during training.

**Evaluation results (synthetic data):**
Accuracy: 0.42 | Precision: 0.66 | Recall: 0.08 | F1: 0.14

The low recall is expected on synthetic data where attack features overlap heavily with BENIGN features. On real CICIDS2017 data, attacks have much more distinctive statistical signatures.

### Model B — XGBoost (Supervised)

Trained on all labelled classes. Predicts the specific attack type for each flow.

**How it works:** XGBoost = Extreme Gradient Boosting. It builds decision trees one after another in sequence:
1. Tree 1 makes predictions — some are wrong.
2. Tree 2 focuses on correcting the rows Tree 1 got wrong.
3. Tree 3 fixes what is still wrong. This repeats 100 times.

The final prediction is a weighted vote across all 100 trees. This "learn from mistakes" approach is called **gradient boosting**. The "extreme" part means it uses second-order mathematical gradients to make each correction as efficient as possible.

**Evaluation results (synthetic data):**

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| BENIGN | 0.63 | 0.98 | 0.76 | 160 |
| BruteForce | 0.00 | 0.00 | 0.00 | 40 |
| DDoS | 1.00 | 1.00 | 1.00 | 80 |
| Other | 0.00 | 0.00 | 0.00 | 40 |
| PortScan | 1.00 | 0.81 | 0.90 | 80 |

DDoS and PortScan score high because the synthetic generator made them visually distinct (50× and 5× flow/packet rates). BruteForce and Other score zero because they were generated with the same random values as BENIGN — no pattern to learn. This is a known limitation of the synthetic fallback and is acknowledged as such.

### Why Use Two Models?

| | Isolation Forest | XGBoost |
|---|---|---|
| Type | Unsupervised | Supervised |
| Needs labels | No | Yes |
| Trained on | BENIGN only | All 5 classes |
| Output | Anomaly score 0–1 | Class name + probability |
| Detects novel attacks | Yes | No |
| Gives specific label | No | Yes |

Isolation Forest catches anything that looks abnormal. XGBoost names the specific attack type. Together they provide breadth and depth, combined in Phase 4.

### Outputs Saved
- `models/isolation_forest.joblib`
- `models/xgboost_model.joblib`
- `reports/confusion_matrix.png`
- `reports/feature_importance.png`
- `data/processed/y_pred_xgb.npy`, `y_proba_xgb.npy`, `if_norm_scores.npy`

### Viva Q&A

**Q: How does Isolation Forest detect anomalies?**
A: It builds 100 random decision trees where each tree randomly selects a feature and split point, recursively partitioning the data. Normal points sit in dense clusters and need many splits to isolate — long paths. Anomalous points are outliers and get isolated in very few splits — short paths. I trained it only on BENIGN traffic, so anything that does not look like normal traffic gets a high anomaly score, including attack types it has never seen before.

**Q: What is XGBoost and why did you choose it?**
A: XGBoost is a gradient boosting algorithm that builds decision trees sequentially, where each tree corrects the mistakes of the previous one. I chose it because it consistently outperforms simpler classifiers on tabular data, handles the scale of CICIDS2017 well, and is widely used in academic network intrusion detection papers.

**Q: What is the difference between precision and recall, and which matters more for security?**
A: Precision is "of all the alarms I raised, how many were real threats?" — low precision means analysts waste time on false alarms. Recall is "of all actual attacks, how many did I catch?" — low recall means real attacks slip through undetected. For a security system, recall matters more. A missed attack can cause serious damage. A false alarm just wastes analyst time. I would accept lower precision to keep recall high.

**Q: Why are BruteForce and Other weak in your results?**
A: I am running on synthetic fallback data, not the real CICIDS2017 dataset. The synthetic generator creates these classes with the same random distributions as BENIGN — there is no meaningful pattern to learn. On the real dataset, BruteForce shows repeated connection attempts to port 22 (SSH) or 21 (FTP) with characteristic flag patterns that the model would detect clearly. I acknowledge this as a limitation of demonstrating the system without the real data.

---

## Phase 4 — Risk Scoring

### What This Phase Does
The script `scripts/risk_scoring.py` takes the raw outputs from both Phase 3 models and combines them into a single **risk score from 0 to 10** for every network flow. It then assigns a human-readable severity label (Critical, High, Medium, Low) and saves the complete alert table to `data/processed/alerts.csv`.

### The Problem This Phase Solves
After Phase 3 we have two separate signals:
- Isolation Forest: a raw anomaly score (a negative float — more negative = more anomalous)
- XGBoost: a probability for each of the 5 classes (e.g. 92% DDoS, 5% BENIGN, 3% Other)

Neither is easy to act on directly. A security analyst cannot triage "minus 0.23 anomaly score". They need a clear, consistent priority scale. Phase 4 converts both outputs into one number from 0–10.

### The Scoring Formula

```
risk_score = (0.4 × IF_component) + (0.6 × XGB_component)
```

**IF component (40% weight):**
The normalised anomaly score from Phase 3 (already 0–1) is multiplied by 10 to give 0–10. Higher = more anomalous.

**XGB component (60% weight):**
```
XGB_component = (1 - P(BENIGN)) × 10
```
If XGBoost is 95% confident the flow is NOT benign, the XGB component is 9.5. If it is 90% confident the flow IS benign, the component is only 1.0.

**Why XGBoost gets higher weight (60%):** It is a supervised model trained on labelled examples, making it more reliable on known attack types. Isolation Forest is unsupervised and less precise, but valuable for catching novel patterns.

### Severity Thresholds

| Severity | Score Range | Meaning |
|---|---|---|
| Critical | 8.0 – 10.0 | Immediate response required |
| High | 6.0 – 7.9 | Investigate within the hour |
| Medium | 4.0 – 5.9 | Review in daily triage |
| Low | 0.0 – 3.9 | Log and monitor |

These thresholds mirror how a real Security Operations Centre (SOC) would prioritise alerts.

### Results on the Test Set

| Severity | Count | Percentage |
|---|---|---|
| Critical | 77 | 19.2% |
| High | 70 | 17.5% |
| Medium | 50 | 12.5% |
| Low | 203 | 50.7% |

Mean risk score: 4.95 | Max: 9.06 | Min: 0.79

The top-scoring flows are all DDoS and PortScan — exactly as expected since those have distinctive patterns in the synthetic data. BENIGN flows cluster at the bottom with scores under 2. This confirms the formula is working correctly.

### Output Saved
`data/processed/alerts.csv` — one row per network flow containing:
- Source IP, Destination IP
- True Label (ground truth)
- Predicted Label (XGBoost prediction)
- Risk Score (0–10)
- Severity (Critical / High / Medium / Low)
- IF Score component and XGB Score component separately

This file is the primary input to the dashboard in Phase 7.

### Viva Q&A

**Q: How do you combine two different model outputs into one risk score?**
A: I normalise each model's output to the same 0–10 scale and then take a weighted average. The Isolation Forest anomaly score is already normalised to 0–1, so I multiply by 10. For XGBoost, I use 1 minus the probability of being BENIGN, scaled to 10 — so high attack confidence gives a high component. I give XGBoost 60% weight because it is supervised and more reliable on known attacks, and Isolation Forest 40% because it is unsupervised but valuable for novelty detection.

**Q: Why did you choose those specific severity thresholds?**
A: The thresholds (Critical ≥ 8, High ≥ 6, Medium ≥ 4, Low < 4) are modelled on how a real Security Operations Centre triages alerts. Critical means immediate response. High means investigate within an hour. Medium can wait for a daily review. Low is just logged for monitoring. The values were chosen so that only clearly high-confidence, high-anomaly flows reach Critical — avoiding alert fatigue.

**Q: What is alert fatigue and how does your scoring help?**
A: Alert fatigue happens when a security system generates so many alerts that analysts stop taking them seriously — they assume most are false alarms. By assigning a risk score and severity label, my system lets analysts focus on Critical and High alerts first, where both models agree the traffic is genuinely suspicious. Low-scoring flows are still logged but do not demand immediate attention. This prioritisation reduces alert fatigue.

**Q: What does the alerts.csv file contain and why is it important?**
A: It contains one row per scored network flow with the predicted attack type, risk score, severity level, and individual model component scores. It is the output that bridges the ML pipeline to the user-facing dashboard. The dashboard reads this file to display the alert table, severity breakdown chart, and attack distribution chart.

---
<!-- Phase 5, 6, 7 notes will be appended here as they are completed -->

---

## Phase 5 — AI Explanation

### What This Phase Does
The script `scripts/ai_explanation.py` adds a plain-English explanation to every alert produced in Phase 4. For each Medium, High, or Critical alert it answers three questions: why does this traffic look suspicious, what is the attacker likely trying to do, and what should the analyst do right now.

The explanation is added as a new column called `AI Explanation` and the result is saved as `data/processed/alerts_with_explanations.csv`.

### Two Modes — Claude API and Fallback

**With an Anthropic API key (real AI explanations):**
If a valid API key is placed in the `.env` file, the script sends each alert to Claude (Anthropic's AI model) and receives a unique, context-aware explanation for that specific flow — referencing the exact risk score, source IP, attack type, and confidence values.

**Without an API key (rule-based fallback):**
Built-in template explanations are used instead. There is one template per attack class (DDoS, PortScan, BruteForce, Other, BENIGN), each enriched with the numeric values from that specific row. The project works fully end-to-end without a paid API key.

### Why Only Medium/High/Critical Alerts Get Explanations
Low-severity alerts get a short standard note ("No immediate action required — logged for monitoring"). Generating a full AI explanation for every single alert including Low-risk benign traffic would waste API tokens and analyst attention. This is the same prioritisation logic used in real security systems.

### What an Explanation Looks Like

**Critical — PortScan (Risk 9.06/10):**
"This flow exhibits port scanning behaviour. The pattern of many short connections to different destination ports is a classic reconnaissance technique — the attacker is probing the target to discover which services are running and potentially vulnerable. Recommended action: Block the source IP and review firewall rules to close unnecessary open ports."

**Medium — BruteForce (Risk 5.91/10):**
"This flow shows signs of a brute force attack. Repeated connection attempts to the same port suggest an automated tool is trying many username/password combinations to gain unauthorised access. Recommended action: Temporarily block the source IP, enable account lockout policies, and consider switching SSH to key-based authentication."

### Key Concepts

**Large Language Model (LLM)** — An AI model trained on vast amounts of text that can understand and generate human language. Claude is Anthropic's LLM, used here to translate technical network statistics into plain English.

**Prompt engineering** — The practice of crafting the text you send to an AI model to get a useful, focused response. The prompt in Phase 5 gives Claude the alert details and tells it exactly what to include in the response (why suspicious, what the attacker wants, what action to take).

**API (Application Programming Interface)** — A way for your code to communicate with an external service. Here the Anthropic API receives an alert, processes it with Claude, and returns an explanation in seconds.

**Rate limiting** — APIs restrict how many requests you can make per second. The script adds a 0.5 second delay between calls to stay within Anthropic's free tier limits.

### Outputs Saved
- `data/processed/alerts_with_explanations.csv` — full alerts table with an extra `AI Explanation` column

### Viva Q&A

**Q: Why did you add an AI explanation layer to the system?**
A: Raw model outputs — anomaly scores and class labels — are not immediately useful to a junior security analyst. They need to know what the threat means and what to do about it. By adding Claude as an explanation layer, I convert technical ML outputs into actionable intelligence. This bridges the gap between the algorithm and the human who acts on the alert.

**Q: How do you use the Claude API in your project?**
A: I build a structured prompt containing the alert details — attack type, risk score, source IP, and the two model component scores — and send it to Claude using the Anthropic Python library. Claude returns a 3–4 sentence explanation that covers why the traffic looks suspicious, what the attacker is likely doing, and what the analyst should do. The response is stored in the alerts database alongside the ML outputs.

**Q: What happens if the API key is not available or the API call fails?**
A: The script has a graceful fallback. If no API key is found in the .env file, it uses built-in rule-based template explanations instead. If an API call fails mid-run, that specific alert falls back to the template. The system never crashes — it degrades gracefully. This is important for reliability: an intrusion detection system must keep running even if an external dependency is unavailable.

---

## Phase 6 — Database

### What This Phase Does
The module `src/database.py` creates a local SQLite database (`data/sentinel.db`) and stores all alerts from Phase 5 inside it. The dashboard queries this database instead of reading CSV files directly.

### Why a Database Instead of CSV Files?

A CSV file has two fundamental problems for a running system:
- Every time you regenerate alerts, the old ones are overwritten — no history
- You cannot filter or sort efficiently without loading the entire file into memory

A database solves both. SQLite stores every alert permanently and allows efficient queries: "give me only Critical alerts" or "show me the 10 highest-risk flows" are answered instantly without loading all records first.

### Why SQLite Specifically?
SQLite is a file-based database — no server to install, no configuration, no separate process to run. The entire database lives in a single file: `data/sentinel.db`. It is built into Python's standard library, so no extra package is needed. It is the most widely deployed database engine in the world (every Android and iOS device contains one).

For a production security system you would use PostgreSQL or MySQL to support multiple users and larger datasets. For a laptop-based learning project, SQLite is the correct choice.

### Database Table Structure

The `alerts` table has these columns:

| Column | Type | What it stores |
|---|---|---|
| `id` | INTEGER | Auto-incrementing unique row ID |
| `timestamp` | TEXT | When the alert was created |
| `source_ip` | TEXT | Attacker IP address |
| `destination_ip` | TEXT | Target IP address |
| `true_label` | TEXT | Ground truth class |
| `predicted_label` | TEXT | XGBoost prediction |
| `risk_score` | REAL | Combined risk score 0–10 |
| `severity` | TEXT | Critical / High / Medium / Low |
| `if_score` | REAL | Isolation Forest component |
| `xgb_score` | REAL | XGBoost component |
| `ai_explanation` | TEXT | Plain-English explanation |

Indexes are created on `severity`, `risk_score`, and `timestamp` to make filtering fast.

### Key Concepts

**SQLite** — A file-based relational database. Data is stored in tables with rows and columns, and queried using SQL (Structured Query Language). No server required.

**SQL (Structured Query Language)** — The language used to interact with databases. Example: `SELECT * FROM alerts WHERE severity = 'Critical' ORDER BY risk_score DESC` reads all Critical alerts, sorted highest risk first.

**Index** — A database structure that makes searching faster. Without an index, finding all Critical alerts requires scanning every row. With an index on the severity column, SQLite jumps directly to the matching rows. Like an index in a book.

**Primary key** — A column that uniquely identifies each row. The `id` column is an auto-incrementing integer that SQLite assigns automatically.

**`conn.row_factory = sqlite3.Row`** — Makes each database row behave like a dictionary, so you can access columns by name (`row['risk_score']`) instead of by position (`row[5]`). Much more readable.

### Four Reusable Functions

| Function | What it does |
|---|---|
| `init_db()` | Creates the database file and tables if they don't exist yet |
| `insert_alerts()` | Loads alerts from CSV into the database |
| `fetch_alerts()` | Reads alerts back with optional severity/risk filters |
| `get_stats()` | Returns summary counts for the dashboard header |

### Viva Q&A

**Q: Why did you use a database instead of just reading the CSV file in the dashboard?**
A: A database provides persistent storage and efficient querying. A CSV is overwritten every time the pipeline runs, so historical alerts would be lost. A database keeps every alert permanently. It also allows efficient filtering — the dashboard can query "show only Critical alerts above risk 8.0" without loading all 400 rows. In a real production system processing thousands of flows per minute, this difference becomes critical.

**Q: What is SQL and how do you use it in this project?**
A: SQL stands for Structured Query Language. It is the standard language for querying relational databases. In this project I use parameterised SQL queries to filter alerts by severity and minimum risk score. For example: `SELECT * FROM alerts WHERE severity = ? AND risk_score >= ? ORDER BY risk_score DESC`. The question marks are placeholders that prevent SQL injection — a security vulnerability where malicious input could manipulate the query.

**Q: What is SQL injection and how did you prevent it?**
A: SQL injection is an attack where a user provides input containing SQL commands that get executed by the database. For example, if severity was set to `' OR '1'='1`, a naive query would return all rows regardless of severity. I prevent this by using parameterised queries — the inputs are passed as separate parameters, not concatenated into the query string, so they are treated as data and never as executable SQL.

---

## Phase 7 — Dashboard

### What This Phase Does
The file `dashboard/app.py` is a full Streamlit web application that ties together everything built in Phases 1–6 into a visual, interactive interface. It reads live data from the SQLite database and displays it across four pages.

Run it with: `venv\Scripts\streamlit.exe run dashboard/app.py`

### The Four Pages

**Page 1 — Overview**
The main landing page. Shows:
- Five metric cards at the top: Total alerts, Critical count, High count, Medium count, Low count
- Severity breakdown donut chart with colour-coded slices
- Attack type distribution bar chart
- Risk score histogram showing where all alerts fall across the 0–10 range
- Top 10 highest-risk flows table with colour-coded rows

**Page 2 — Alert Table**
A full scrollable table of every alert in the database. The sidebar filters (severity and minimum risk score) apply here in real time. Includes a CSV download button so analysts can export the filtered results.

**Page 3 — Model Performance**
Displays the evaluation charts generated in Phase 3:
- Confusion matrix (correct vs incorrect predictions grid)
- Feature importance chart (top 20 features XGBoost used)
- Model architecture summary for both Isolation Forest and XGBoost
- The risk score formula written out clearly

**Page 4 — AI Explanations**
Shows the plain-English explanations from Phase 5, grouped by severity. Each alert is an expandable card showing the risk score, IF score, XGB score, and the full explanation text.

### Key Concepts

**Streamlit** — A Python library that turns a Python script into a web application with zero HTML, CSS, or JavaScript required. You write Python and Streamlit renders it as a web page with interactive widgets (sliders, dropdowns, buttons, charts).

**Plotly** — An interactive charting library used for the donut chart, bar chart, and histogram. Charts are interactive — you can hover to see values, click legend items to filter, and zoom in.

**`@st.cache_data`** — A Streamlit decorator that caches the result of a function. If the same database query is made again within 30 seconds, Streamlit returns the cached result instead of hitting the database again. This makes the dashboard feel fast and responsive.

**`@st.cache_resource`** — Like `@st.cache_data` but for objects that should only be created once per session, like a database connection. Creating a new database connection on every page interaction would be slow and wasteful.

**Sidebar** — The left panel in the Streamlit app containing filters. When the user changes a filter, Streamlit re-runs the script with the new values and updates all charts automatically. This is Streamlit's reactive model — no JavaScript event handlers needed.

**Colour coding** — Critical alerts are red, High are orange, Medium are yellow, Low are green. This is the standard traffic-light convention in security dashboards, making severity immediately visible without reading text.

### Why Streamlit for the Dashboard?
Streamlit is ideal for data science projects because it requires no web development knowledge. The entire dashboard is written in Python — the same language as the ML pipeline. Building an equivalent dashboard with HTML, JavaScript, and a web framework would take ten times as long and require skills outside the scope of this project.

### Viva Q&A

**Q: What is Streamlit and why did you choose it for the dashboard?**
A: Streamlit is a Python library that converts Python scripts into interactive web applications without requiring HTML, CSS, or JavaScript. I chose it because the entire project is written in Python, and Streamlit lets me build a professional-looking dashboard in the same language. It handles all the web rendering, widget interactivity, and layout automatically. For a data science project, it is significantly faster to develop with than a traditional web framework.

**Q: How does the dashboard connect to the rest of the pipeline?**
A: The dashboard reads from the SQLite database created in Phase 6, which was populated by loading the alerts CSV from Phase 5. The database functions — init_db, fetch_alerts, get_stats — are defined in src/database.py and imported into the dashboard. The Streamlit caching decorators ensure the database connection is created once and queries are not repeated unnecessarily. The model performance charts are loaded as static image files from the reports/ folder, generated during Phase 3 training.

**Q: What would you change if this was a real production system?**
A: Several things. First, replace the synthetic CICIDS2017 data with real network traffic captured from a live environment. Second, replace SQLite with PostgreSQL to support concurrent users and larger datasets. Third, add user authentication so only authorised analysts can view alerts. Fourth, add a real-time packet capture feed instead of replaying historical data. Fifth, add email or Slack notifications for Critical alerts so analysts are alerted immediately rather than having to check the dashboard manually. These are all acknowledged limitations of the current implementation.
