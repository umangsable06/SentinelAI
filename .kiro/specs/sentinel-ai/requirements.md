# Requirements Document

## Introduction

SentinelAI is an AI-powered network threat detection system built as an MCA college project.
It ingests network flow data (CICIDS2017 dataset), applies machine learning models to detect
and classify attacks, scores each event by risk severity, generates plain-English AI
explanations via Claude API, and presents everything in a Streamlit dashboard backed by SQLite.

The system is built phase-by-phase so that each component can be understood, explained during
a viva, and run locally on a standard laptop with no Docker or cloud dependencies.

---

## Glossary

- **System**: The SentinelAI application as a whole
- **Pipeline**: The data-processing chain from raw CSV to scored alert
- **Cleaner**: The module responsible for loading and cleaning raw network-flow CSV files
- **Feature_Engineer**: The module that selects, scales, and encodes features for model input
- **Isolation_Forest**: The unsupervised anomaly-detection model (Model A)
- **XGBoost_Classifier**: The supervised multi-class attack classification model (Model B)
- **Risk_Scorer**: The component that combines anomaly score and classifier confidence into a 0–10 risk score
- **AI_Explainer**: The component that calls the Claude API to generate plain-English threat summaries
- **Dashboard**: The Streamlit web application that displays alerts, charts, and model metrics
- **Database**: The SQLite database that stores all scored alert records and user feedback
- **Alert**: A single network-flow record that has been scored and stored in the Database
- **Severity**: A categorical label (Low / Medium / High / Critical) derived from risk score
- **CICIDS2017**: The Canadian Institute for Cybersecurity Intrusion Detection dataset 2017
- **MITRE_ATT&CK**: A publicly available knowledge base of adversary tactics and techniques
- **Scaler**: The StandardScaler instance persisted with joblib, used to normalise feature values
- **config.py**: A single Python file that holds all tunable constants (thresholds, paths, model names)
- **LEARNING_NOTES.md**: A running markdown file that accumulates per-phase explanations and viva Q&A
- **Admin**: A logged-in user with role "admin" who can submit feedback on alerts
- **Viewer**: A logged-in user with role "viewer" who has read-only access to the dashboard

---

## Requirements

### Requirement 1: Project Scaffolding and Configuration

**User Story:** As an MCA student, I want a clean project structure with all configuration centralised, so that I can navigate the code confidently and change settings without hunting through multiple files.

#### Acceptance Criteria

1. THE System SHALL create the following directories on first setup: `data/`, `models/`, `src/`, `dashboard/`, `scripts/`, `reports/`.
2. THE System SHALL provide a `config.py` file that contains all tunable constants including dataset sample size, file paths, model hyperparameters, risk-score thresholds, severity boundaries, and the Claude model name.
3. THE System SHALL provide a `requirements.txt` file listing all required Python packages with pinned versions.
4. THE System SHALL provide a `.env.example` file documenting every required environment variable without exposing real values.
5. THE System SHALL provide a `.gitignore` file that excludes `.env`, `data/`, `models/`, `__pycache__/`, and `*.pyc`.
6. THE System SHALL provide a `README.md` describing the project purpose, setup steps, and how to run each phase.
7. THE System SHALL provide an empty `LEARNING_NOTES.md` that is appended to at the end of every phase.
8. IF an environment variable required by the System is missing at runtime, THEN THE System SHALL print a clear error message naming the missing variable and exit gracefully.

---

### Requirement 2: Data Loading and Cleaning

**User Story:** As an MCA student, I want to load and clean a slice of the CICIDS2017 dataset, so that I can understand what raw network data looks like and how quality issues are handled.

#### Acceptance Criteria

1. WHEN the Cleaner is invoked, THE Cleaner SHALL load CSV files from the path specified in `config.py`, limited to the sample size defined in `config.py`.
2. THE Cleaner SHALL strip leading and trailing whitespace from all column names after loading.
3. THE Cleaner SHALL replace all positive-infinity and negative-infinity values with NaN.
4. THE Cleaner SHALL drop all rows that contain at least one NaN value after infinity replacement.
5. THE Cleaner SHALL drop duplicate rows, keeping the first occurrence.
6. WHEN the Cleaner finds no IP-address columns in the loaded data, THE Cleaner SHALL assign clearly-labelled simulated source and destination IP addresses to every row and log a notice stating the IPs are simulated.
7. THE Cleaner SHALL downsample benign-labelled rows so that the ratio of benign to attack records does not exceed the ratio defined in `config.py`, and SHALL log the counts before and after downsampling.
8. IF the specified CICIDS2017 CSV files are not found at the configured path, THEN THE Cleaner SHALL generate a small synthetic fallback dataset, label it as synthetic in every output, and log a prominent warning.
9. THE Cleaner SHALL print the dataset shape, label distribution, and a short description of the key columns after cleaning.
10. THE Cleaner SHALL save at least one data-exploration chart (label distribution) to the `reports/` directory.

---

### Requirement 3: Feature Engineering

**User Story:** As an MCA student, I want to select, transform, and split features correctly, so that I can explain why each step matters and avoid data-leakage mistakes.

#### Acceptance Criteria

1. THE Feature_Engineer SHALL select a documented subset of features including flow duration, packets per second, bytes per second, packet-length statistics, flag counts, and destination port, with a comment in code explaining why each group is useful.
2. THE Feature_Engineer SHALL remove any feature whose variance is zero (constant feature) and log its name.
3. THE Feature_Engineer SHALL remove one feature from every pair whose Pearson correlation exceeds the threshold defined in `config.py`, and log the removed feature names.
4. THE Feature_Engineer SHALL split the dataset into training and test sets BEFORE fitting the Scaler, using the split ratio defined in `config.py`.
5. THE Feature_Engineer SHALL fit the Scaler on the training set only and transform both training and test sets using the fitted Scaler.
6. THE Feature_Engineer SHALL save the fitted Scaler to the `models/` directory using joblib.
7. THE Feature_Engineer SHALL encode the label column into the categories: BENIGN, DDoS, PortScan, BruteForce, and Other; any label not matching a known category SHALL be mapped to Other.
8. IF the Feature_Engineer is run after the Scaler file already exists, THEN THE Feature_Engineer SHALL load the existing Scaler rather than fitting a new one, and log that it is reusing a saved Scaler.

---

### Requirement 4: Model Training and Evaluation

**User Story:** As an MCA student, I want to train two different models and evaluate them honestly, so that I can explain their strengths, weaknesses, and appropriate use cases.

#### Acceptance Criteria

1. THE Isolation_Forest SHALL be trained exclusively on benign-labelled training rows so that it learns the baseline of normal traffic.
2. THE XGBoost_Classifier SHALL be trained on the full labelled training set for multi-class attack classification.
3. WHEN evaluation is run on the test set, THE System SHALL compute and display accuracy, precision, recall, and F1-score for both models.
4. THE System SHALL save a confusion-matrix image for each model to the `reports/` directory.
5. THE System SHALL save a feature-importance bar chart for the XGBoost_Classifier to the `reports/` directory.
6. THE System SHALL save each trained model to the `models/` directory using joblib.
7. THE System SHALL include a short plain-English comment next to each metric explaining what it measures.
8. IF a model file already exists in `models/`, THEN THE System SHALL load the saved model rather than retraining, and log that it is reusing a saved model.

---

### Requirement 5: Risk Scoring and Severity Mapping

**User Story:** As an MCA student, I want each network event scored on a 0–10 scale and mapped to a severity level, so that I can explain the threat priority to any audience without needing ML knowledge.

#### Acceptance Criteria

1. THE Risk_Scorer SHALL combine the Isolation_Forest anomaly score and the XGBoost_Classifier confidence score using a weighted formula defined entirely in `config.py`.
2. THE Risk_Scorer SHALL produce a final risk score in the range 0.0 to 10.0 for every event.
3. THE Risk_Scorer SHALL map risk scores to severity levels according to boundaries defined in `config.py`: a score below the Low threshold maps to Low, between Low and Medium to Medium, between Medium and High to High, and at or above the High threshold to Critical.
4. THE Risk_Scorer SHALL map each known attack type to its MITRE ATT&CK technique ID: PortScan to T1046, BruteForce to T1110, DDoS to T1498; BENIGN and Other SHALL map to N/A.
5. WHEN the risk score formula or severity boundaries are changed in `config.py`, THE Risk_Scorer SHALL use the updated values without requiring code changes outside `config.py`.

---

### Requirement 6: AI Explanation Layer

**User Story:** As an MCA student, I want high-risk events to be explained in plain English by an AI, so that I can demonstrate the practical value of LLMs in a security context and handle API failures gracefully.

#### Acceptance Criteria

1. WHEN an event's risk score meets or exceeds the explanation threshold defined in `config.py`, THE AI_Explainer SHALL send a prompt to the Claude API requesting a JSON response containing the fields: `plain_english_summary`, `why_flagged`, and `recommended_actions`.
2. THE AI_Explainer SHALL use the Claude model name specified in `config.py` and the API key from the `.env` file.
3. THE AI_Explainer SHALL cache explanations keyed by attack type so that repeated calls for the same attack type reuse the cached response within a single session.
4. IF the Claude API call fails for any reason, or IF no API key is configured, THEN THE AI_Explainer SHALL return a pre-written template explanation and label the output with a visible "template mode" indicator.
5. THE AI_Explainer SHALL include a comment in code explaining why JSON is requested in the prompt rather than free-form text.

---

### Requirement 7: Database Storage

**User Story:** As an MCA student, I want all alerts persisted in a local SQLite database, so that the dashboard can query historical data and I can explain relational database concepts during my viva.

#### Acceptance Criteria

1. THE Database SHALL contain an `alerts` table with columns: `id` (auto-increment primary key), `timestamp`, `source_ip`, `dest_ip`, `attack_type`, `risk_score`, `severity`, `explanation`, `user_feedback`.
2. THE Database SHALL contain a `users` table with columns: `id`, `username`, `password_hash`, `role`, `failed_attempts`, `locked`.
3. WHEN an alert is inserted, THE Database SHALL set `user_feedback` to NULL by default.
4. THE Database SHALL enforce that `role` in the `users` table is one of: `admin`, `viewer`.
5. THE System SHALL create both tables automatically on first run if they do not already exist.

---

### Requirement 8: Streamlit Dashboard

**User Story:** As an MCA student, I want a web dashboard that displays alerts, charts, and model performance, so that I can demonstrate the end-to-end system visually during my project presentation.

#### Acceptance Criteria

1. THE Dashboard SHALL display a live alerts table colour-coded by severity: Low as green, Medium as yellow, High as orange, and Critical as red.
2. THE Dashboard SHALL display summary cards showing total alerts, critical alerts, high alerts, and unique attack types detected.
3. THE Dashboard SHALL display a chart of attacks over time and a chart of attack-type distribution.
4. THE Dashboard SHALL include a Model Performance page showing the saved confusion matrix images, evaluation metrics, and feature-importance chart.
5. THE Dashboard SHALL include an About page describing the project, dataset, and tech stack.
6. WHEN a user is not logged in, THE Dashboard SHALL display only the login page and SHALL NOT render any other page or data.
7. WHILE a user is logged in with the Admin role, THE Dashboard SHALL display feedback buttons ("Mark as false alarm" / "Confirm as real threat") on each alert row.
8. WHILE a user is logged in with the Viewer role, THE Dashboard SHALL display the alerts table without feedback buttons.
9. THE Dashboard SHALL display the logged-in username and role in the sidebar.
10. THE Dashboard SHALL provide a logout button in the sidebar that clears the session and returns the user to the login page.

---

### Requirement 9: User Feedback on Alerts

**User Story:** As an MCA student, I want analysts to be able to mark alerts as false alarms or confirmed threats, so that I can demonstrate a feedback loop concept and discuss how real SOC workflows improve detection over time.

#### Acceptance Criteria

1. WHEN an Admin clicks "Mark as false alarm" on an alert, THE Database SHALL update that alert's `user_feedback` column to `false_alarm`.
2. WHEN an Admin clicks "Confirm as real threat" on an alert, THE Database SHALL update that alert's `user_feedback` column to `confirmed_threat`.
3. THE Dashboard SHALL display a Feedback Summary section showing: total alerts reviewed, count of false alarms, count of confirmed threats, false alarm rate as a percentage, and a bar chart of feedback counts by attack type.
4. THE System SHALL include a visible note in both the code and the dashboard stating that feedback is recorded only and does NOT trigger model retraining.

---

### Requirement 10: Authentication and Role-Based Access

**User Story:** As an MCA student, I want secure login with hashed passwords and role-based access control, so that I can explain basic authentication security principles during my viva.

#### Acceptance Criteria

1. THE System SHALL hash all passwords using bcrypt before storing them in the `users` table and SHALL never store or log plain-text passwords.
2. THE System SHALL provide a `scripts/create_user.py` script that prompts for a username, password, and role interactively in the terminal, with no hardcoded default credentials.
3. WHEN login is attempted with incorrect credentials, THE Dashboard SHALL increment the `failed_attempts` counter for that username.
4. WHEN a user's `failed_attempts` reaches 3, THE Database SHALL set the `locked` column to true for that user and THE Dashboard SHALL reject all subsequent login attempts for that user regardless of password correctness.
5. THE Dashboard SHALL display a generic error message on any failed login attempt without revealing whether the username or password was incorrect.
6. THE System SHALL provide a `scripts/unlock_user.py` script that an admin can run from the terminal to reset `failed_attempts` to 0 and set `locked` to false for a specified user.
7. THE Dashboard SHALL use `st.session_state` to maintain login state across page interactions.

---

### Requirement 11: Traffic Simulation and Testing

**User Story:** As an MCA student, I want scripts to simulate live traffic and automated tests for key logic, so that I can demonstrate the system running end-to-end and explain how testing catches bugs.

#### Acceptance Criteria

1. THE System SHALL provide a simulation script that replays test-set rows one by one with a configurable delay, writing each scored alert to the Database.
2. THE System SHALL provide a demo script that feeds a mix of normal and attack traffic rows through the Pipeline and writes results to the Database, suitable for a live presentation.
3. THE System SHALL provide automated tests for the Cleaner's column-name stripping and infinity-replacement logic.
4. THE System SHALL provide automated tests for the Risk_Scorer's output-range constraint (result must be between 0.0 and 10.0 inclusive) and severity-mapping correctness.
5. THE System SHALL provide a `run.py` entry-point script that checks for saved model files, trains models if they are missing, and then launches the Streamlit dashboard.

---

### Requirement 12: Documentation and Viva Preparation

**User Story:** As an MCA student, I want complete documentation and a dedicated viva Q&A file, so that I can prepare thoroughly for my examination and explain every design decision.

#### Acceptance Criteria

1. THE System SHALL include a finalised `README.md` with: project overview, prerequisites, installation steps, how to run each phase, and a description of each directory.
2. THE System SHALL include a `REPORT_OUTLINE.md` covering: abstract, problem statement, objectives, related work, methodology, system architecture, results, limitations, and future scope.
3. THE Limitations section of `REPORT_OUTLINE.md` SHALL explicitly state: use of a lab dataset rather than live traffic, simulated IP addresses, class imbalance in the dataset, and that the system detects and advises but does not automatically remediate threats.
4. THE System SHALL include a `VIVA_QA.md` file containing at least 25 questions likely to be asked during a viva examination, each with a concise plain-English answer.
5. THE System SHALL include a system architecture diagram (text-based or Mermaid format) showing the data flow from raw CSV through the Pipeline, models, Database, and Dashboard.
6. WHEN a phase is completed, THE System SHALL append to `LEARNING_NOTES.md`: a plain-English description of what the phase built, key concepts introduced, and at least 3 viva questions with short answers for that phase.
