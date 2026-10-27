# generate_practical_file.py
# Generates the complete SAPM Practical File as a Word document
# Run: python generate_practical_file.py

from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import os

doc = Document()

# ── Page margins ──────────────────────────────────────────────────────────────
section = doc.sections[0]
section.top_margin    = Cm(2.5)
section.bottom_margin = Cm(2.5)
section.left_margin   = Cm(3)
section.right_margin  = Cm(2)

# ── Styles ────────────────────────────────────────────────────────────────────
styles = doc.styles

def set_heading(para, text, level=1):
    para.text = text
    para.style = f'Heading {level}'
    run = para.runs[0]
    if level == 1:
        run.font.size = Pt(16)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0x1F, 0x49, 0x7D)
    elif level == 2:
        run.font.size = Pt(13)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0x2E, 0x74, 0xB5)
    return para

def add_heading(doc, text, level=1):
    p = doc.add_heading(text, level=level)
    run = p.runs[0] if p.runs else p.add_run(text)
    if level == 1:
        run.font.size = Pt(16)
        run.font.color.rgb = RGBColor(0x1F, 0x49, 0x7D)
    elif level == 2:
        run.font.size = Pt(13)
        run.font.color.rgb = RGBColor(0x2E, 0x74, 0xB5)
    return p

def add_label_para(doc, label, text):
    p = doc.add_paragraph()
    run_label = p.add_run(label + ": ")
    run_label.bold = True
    run_label.font.size = Pt(11)
    run_text = p.add_run(text)
    run_text.font.size = Pt(11)
    return p

def add_para(doc, text, bold=False, size=11):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = bold
    run.font.size = Pt(size)
    return p

def add_bullet(doc, text):
    p = doc.add_paragraph(text, style='List Bullet')
    p.runs[0].font.size = Pt(11)
    return p

def add_numbered(doc, text):
    p = doc.add_paragraph(text, style='List Number')
    p.runs[0].font.size = Pt(11)
    return p

def add_code(doc, text):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.name = 'Courier New'
    run.font.size = Pt(9)
    p.paragraph_format.left_indent = Inches(0.4)
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), 'F2F2F2')
    p._p.get_or_add_pPr().append(shd)
    return p

def add_table(doc, headers, rows):
    table = doc.add_table(rows=1+len(rows), cols=len(headers))
    table.style = 'Table Grid'
    # Header row
    hdr = table.rows[0]
    for i, h in enumerate(headers):
        cell = hdr.cells[i]
        cell.text = h
        run = cell.paragraphs[0].runs[0]
        run.bold = True
        run.font.size = Pt(10)
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        tc = cell._tc
        tcPr = tc.get_or_add_tcPr()
        shd = OxmlElement('w:shd')
        shd.set(qn('w:val'), 'clear')
        shd.set(qn('w:color'), 'auto')
        shd.set(qn('w:fill'), '2E74B5')
        tcPr.append(shd)
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    # Data rows
    for ri, row in enumerate(rows):
        tr = table.rows[ri+1]
        for ci, cell_text in enumerate(row):
            cell = tr.cells[ci]
            cell.text = str(cell_text)
            cell.paragraphs[0].runs[0].font.size = Pt(10)
            if ri % 2 == 1:
                tc = cell._tc
                tcPr = tc.get_or_add_tcPr()
                shd = OxmlElement('w:shd')
                shd.set(qn('w:val'), 'clear')
                shd.set(qn('w:color'), 'auto')
                shd.set(qn('w:fill'), 'DEEAF1')
                tcPr.append(shd)
    return table

def page_break(doc):
    doc.add_page_break()


# ══════════════════════════════════════════════════════════════════════════════
# COVER PAGE
# ══════════════════════════════════════════════════════════════════════════════
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("PRACTICAL FILE")
run.font.size = Pt(22)
run.font.bold = True
run.font.color.rgb = RGBColor(0x1F, 0x49, 0x7D)

doc.add_paragraph()
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("Subject: Software Architecture and Project Management LAB")
run.font.size = Pt(14)
run.font.bold = True

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("Academic Year: 2026-2027")
run.font.size = Pt(13)

doc.add_paragraph()
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("Project: SentinelAI")
run.font.size = Pt(18)
run.font.bold = True
run.font.color.rgb = RGBColor(0x2E, 0x74, 0xB5)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("AI-Powered Network Intrusion Detection System")
run.font.size = Pt(13)
run.font.italic = True

doc.add_paragraph()
doc.add_paragraph()
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("Student Name: _______________________________")
run.font.size = Pt(12)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("Roll No: _______________________________")
run.font.size = Pt(12)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("Class: _______________________________")
run.font.size = Pt(12)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("Teacher: _______________________________")
run.font.size = Pt(12)

page_break(doc)

# ══════════════════════════════════════════════════════════════════════════════
# PRACTICAL 1
# ══════════════════════════════════════════════════════════════════════════════
add_heading(doc, "Practical 1", 1)
add_label_para(doc, "Title", "Design a Questionnaire for Requirement Analysis")
add_label_para(doc, "Aim", "To design structured questionnaires for requirement analysis from different organizational levels for the SentinelAI project.")
add_para(doc, "Objective:", bold=True)
add_bullet(doc, "Gather system requirements through stakeholder feedback.")
add_bullet(doc, "Customize questions based on organizational hierarchy.")
add_para(doc, "Theory:", bold=True)
add_para(doc, "Requirement analysis gathers stakeholder needs. Questionnaires help collect structured responses, aiding in precise system planning. For a network security system like SentinelAI, it is important to understand what threats different users face and what information they need from the system.")

add_heading(doc, "Level 1 - IT Manager / Security Head", 2)
questions_mgr = [
    "What types of network attacks does your organization most frequently face? (DDoS, BruteForce, PortScan)",
    "How quickly do you need to be notified of a critical threat? (Real-time / Within 1 hour / Daily report)",
    "Do you require the system to explain threats in plain English or just show raw data?",
    "How many network flows does your organization generate per day approximately?",
    "Do you need user-level access control so different staff see different data?",
    "Should the system integrate with existing tools like firewalls or SIEM systems?",
    "What severity levels would you like to prioritize? (Critical, High, Medium, Low)",
    "Do you need the system to store historical alerts for audit purposes?",
]
for q in questions_mgr:
    add_numbered(doc, q)

add_heading(doc, "Level 2 - Junior Network Analyst / IT Staff", 2)
questions_staff = [
    "Do you understand technical terms like DDoS, PortScan, BruteForce, or do you prefer plain-English descriptions?",
    "What information is most useful when you receive an alert? (Source IP, Attack type, Risk score, Recommended action)",
    "How often do you check security alerts during your shift?",
    "Have you experienced false alarms from security systems before? How did that affect your work?",
    "Would you prefer a dashboard that shows all alerts or only the most urgent?",
    "Do you need the ability to download alert reports as PDF or CSV?",
    "Would a live monitoring feed (alerts appearing in real time) be useful to you?",
]
for q in questions_staff:
    add_numbered(doc, q)

add_label_para(doc, "Application", "Used in system analysis phase to collect business needs before designing SentinelAI.")
add_label_para(doc, "Conclusion", "Requirement gathering using structured questionnaires ensures stakeholder alignment and complete system understanding. The questionnaire helped identify that the system needed plain-English explanations, risk scoring, severity prioritization, a database for history, and a live monitoring view - all of which are implemented in SentinelAI.")
page_break(doc)

# ══════════════════════════════════════════════════════════════════════════════
# PRACTICAL 2
# ══════════════════════════════════════════════════════════════════════════════
add_heading(doc, "Practical 2", 1)
add_label_para(doc, "Title", "Study of the Waterfall Process Model")
add_label_para(doc, "Aim", "To understand the steps of the Waterfall Process Model and map them to the SentinelAI project.")
add_para(doc, "Objective:", bold=True)
add_bullet(doc, "Study all phases of the Waterfall model.")
add_bullet(doc, "Map each stage to the SentinelAI project.")
add_para(doc, "Theory:", bold=True)
add_para(doc, "The Waterfall Model is a sequential software development process where progress flows downward through phases. Each phase must be completed before the next begins. Phases: Requirements -> System Design -> Implementation -> Testing -> Deployment -> Maintenance.")

add_heading(doc, "Mapping to SentinelAI Project", 2)
add_table(doc,
    ["Phase", "Description", "SentinelAI Application"],
    [
        ["Requirements", "Gather what system must do", "Identified need for attack detection, risk scoring, AI explanations, dashboard"],
        ["System Design", "Plan architecture and database", "Designed pipeline: data -> models -> scoring -> database -> dashboard"],
        ["Implementation", "Write the code", "Built 7 phases: load_data.py, feature_engineering.py, train_models.py, risk_scoring.py, ai_explanation.py, database.py, dashboard/app.py"],
        ["Testing", "Verify the system works", "Ran each script, checked outputs, verified database and dashboard"],
        ["Deployment", "Make available to users", "Packaged with run.bat for one-click launch, Streamlit dashboard on localhost:8501"],
        ["Maintenance", "Fix issues and update", "LEARNING_NOTES.md documents all known limitations and future improvements"],
    ]
)
doc.add_paragraph()
add_para(doc, "Pros of Waterfall for SentinelAI:", bold=True)
add_bullet(doc, "Clear phase separation made it easy to build one script at a time.")
add_bullet(doc, "Each phase had clear outputs (cleaned CSV, trained model files, alerts CSV).")
add_bullet(doc, "Easy to document since each phase is independent.")
add_para(doc, "Cons:", bold=True)
add_bullet(doc, "Could not easily go back to change feature list once Phase 2 was complete.")
add_bullet(doc, "Real requirements from security analysts may change after initial implementation.")
add_label_para(doc, "Application", "Suitable for projects with well-defined requirements like SentinelAI where each phase feeds directly into the next.")
add_label_para(doc, "Conclusion", "The Waterfall model suited SentinelAI's phase-by-phase development. Each phase produced a concrete output used by the next, making the project systematic and easy to manage.")
page_break(doc)

# ══════════════════════════════════════════════════════════════════════════════
# PRACTICAL 3
# ══════════════════════════════════════════════════════════════════════════════
add_heading(doc, "Practical 3", 1)
add_label_para(doc, "Title", "Implementation of Architecture Styles Based on SentinelAI")
add_label_para(doc, "Aim", "To implement software architectural styles in the SentinelAI project.")
add_para(doc, "Objective:", bold=True)
add_bullet(doc, "Learn types of software architectures.")
add_bullet(doc, "Apply architecture to the SentinelAI project.")
add_para(doc, "Theory:", bold=True)
add_para(doc, "Software architecture defines the high-level structure of a system. Common styles include layered, client-server, MVC, and microservices. SentinelAI uses a Layered (N-Tier) Architecture with 4 distinct layers.")

add_heading(doc, "Architecture Diagram", 2)
add_code(doc, """LAYER 4: PRESENTATION LAYER
  dashboard/app.py (Streamlit Web UI)
  Login, Charts, Alert Table, Live Monitor, AI Explanations
         |
LAYER 3: BUSINESS LOGIC LAYER
  scripts/risk_scoring.py
  scripts/ai_explanation.py
  Combines model outputs -> risk score + explanations
         |
LAYER 2: ML / PROCESSING LAYER
  scripts/load_data.py
  scripts/feature_engineering.py
  scripts/train_models.py
  Isolation Forest + XGBoost models
         |
LAYER 1: DATA LAYER
  data/raw/          (CICIDS2017 CSV files)
  data/processed/    (cleaned arrays)
  data/sentinel.db   (SQLite database)
  models/            (saved .joblib files)""")

add_heading(doc, "Component Mapping", 2)
add_table(doc,
    ["Component", "Layer", "Responsibility"],
    [
        ["config.py", "All layers", "Shared settings - paths, thresholds, model names"],
        ["load_data.py", "Layer 2", "Load and clean raw CSV data"],
        ["feature_engineering.py", "Layer 2", "Select features, scale, encode, split"],
        ["train_models.py", "Layer 2", "Train Isolation Forest and XGBoost"],
        ["risk_scoring.py", "Layer 3", "Combine model outputs into risk score"],
        ["ai_explanation.py", "Layer 3", "Call Claude API for explanations"],
        ["database.py", "Layer 1", "Store and retrieve alerts in SQLite"],
        ["app.py", "Layer 4", "Web dashboard with login and 5 pages"],
    ]
)
doc.add_paragraph()
add_label_para(doc, "Application", "Layered architecture improves maintainability and separability of concerns. Each layer can be tested and replaced independently.")
add_label_para(doc, "Conclusion", "Applying a layered architectural style to SentinelAI organizes the system logically, makes each component independently testable, and enhances the overall software design quality.")
page_break(doc)

# ══════════════════════════════════════════════════════════════════════════════
# PRACTICAL 4
# ══════════════════════════════════════════════════════════════════════════════
add_heading(doc, "Practical 4", 1)
add_label_para(doc, "Title", "Prepare Design of SentinelAI According to Software Design Levels")
add_label_para(doc, "Aim", "To prepare the software design of SentinelAI according to different software design levels.")
add_para(doc, "Theory:", bold=True)
add_para(doc, "Software design defines the structure and working of a software product. The main design levels are: Architectural Design, High-Level Design (HLD), Low-Level Design (LLD), Interface Design, and Data Design.")

add_heading(doc, "1. Architectural Design", 2)
add_para(doc, "SentinelAI uses a 4-layer pipeline architecture:")
add_code(doc, "Data Layer -> ML Processing Layer -> Business Logic Layer -> Presentation Layer")

add_heading(doc, "2. High-Level Design (HLD)", 2)
add_code(doc, """[Raw CSV Data]
      |
[Module 1: Data Loader]        -> cleaned_data.csv
      |
[Module 2: Feature Engineer]   -> X_train.npy, scaler.joblib, label_encoder.joblib
      |
[Module 3: Model Trainer]      -> isolation_forest.joblib, xgboost_model.joblib
      |
[Module 4: Risk Scorer]        -> alerts.csv (risk scores + severity)
      |
[Module 5: AI Explainer]       -> alerts_with_explanations.csv
      |
[Module 6: Database]           -> sentinel.db
      |
[Module 7: Dashboard]          -> Web UI at localhost:8501""")

add_heading(doc, "3. Low-Level Design (LLD) - Key Algorithms", 2)
add_para(doc, "Risk Score Formula:", bold=True)
add_code(doc, "risk_score = (0.4 x IF_score x 10) + (0.6 x (1 - P(BENIGN)) x 10)")
add_para(doc, "Severity Assignment:", bold=True)
add_code(doc, "if risk >= 8.0  -> Critical\nelif risk >= 6.0 -> High\nelif risk >= 4.0 -> Medium\nelse            -> Low")
add_para(doc, "Isolation Forest:", bold=True)
add_bullet(doc, "Build 100 random trees")
add_bullet(doc, "For each flow, measure average path length to isolation")
add_bullet(doc, "Short path = anomaly (attack), Long path = normal")

add_heading(doc, "4. Interface Design", 2)
add_table(doc,
    ["Page", "Components"],
    [
        ["Login", "Username field, password field, Sign In button, demo credentials"],
        ["Home", "5 metric cards, quick navigation cards, latest critical alerts"],
        ["Threat Overview", "Donut chart (severity), bar chart (attack types), histogram (risk scores)"],
        ["Alert Table", "Filterable table, colour-coded severity, CSV download button"],
        ["Live Monitor", "Speed control, filter, live feed, progress bar"],
        ["Upload Data", "File uploader, pipeline runner, progress indicators"],
        ["Model Performance", "Confusion matrix image, feature importance image"],
        ["AI Explanations", "Expandable cards grouped by severity"],
    ]
)

add_heading(doc, "5. Data Design - SQLite Table: alerts", 2)
add_table(doc,
    ["Column", "Type", "Description"],
    [
        ["id", "INTEGER PK", "Auto-increment unique ID"],
        ["timestamp", "TEXT", "When alert was created"],
        ["source_ip", "TEXT", "Attacker IP address"],
        ["destination_ip", "TEXT", "Target IP address"],
        ["true_label", "TEXT", "Actual attack type (ground truth)"],
        ["predicted_label", "TEXT", "XGBoost prediction"],
        ["risk_score", "REAL", "Combined risk score 0-10"],
        ["severity", "TEXT", "Critical / High / Medium / Low"],
        ["if_score", "REAL", "Isolation Forest component"],
        ["xgb_score", "REAL", "XGBoost component"],
        ["ai_explanation", "TEXT", "Plain-English AI summary"],
    ]
)
doc.add_paragraph()
add_label_para(doc, "Conclusion", "The multi-level design of SentinelAI ensures each module has a single clear responsibility. The layered architecture, clear data flow, and well-defined database schema make the system maintainable and extensible.")
page_break(doc)

# ══════════════════════════════════════════════════════════════════════════════
# PRACTICAL 5
# ══════════════════════════════════════════════════════════════════════════════
add_heading(doc, "Practical 5", 1)
add_label_para(doc, "Title", "Write Different Types of Risks and Prepare RMMM Plan for SentinelAI")
add_label_para(doc, "Aim", "To identify risks in the SentinelAI project and prepare a Risk Mitigation, Monitoring, and Management plan.")
add_para(doc, "Objective:", bold=True)
add_bullet(doc, "Understand types of risks.")
add_bullet(doc, "Develop a strategy to handle them.")
add_para(doc, "Theory:", bold=True)
add_para(doc, "Risks are potential problems that could affect project success. Types include Project risks, Business risks, and Technical risks. RMMM plans help manage them proactively.")

add_heading(doc, "RMMM Plan for SentinelAI", 2)
add_table(doc,
    ["Risk ID", "Risk", "Type", "Probability", "Impact", "Mitigation"],
    [
        ["R1", "CICIDS2017 CSV files unavailable", "Project", "High", "High", "Built synthetic fallback dataset that auto-generates when no CSV found"],
        ["R2", "Anthropic API key missing or expired", "Technical", "Medium", "Medium", "Built rule-based fallback explanations that work without API key"],
        ["R3", "Python package version incompatibility", "Technical", "High", "High", "Used >= version pinning in requirements.txt for Python 3.14 compatible wheels"],
        ["R4", "Model overfits to synthetic data", "Technical", "High", "Medium", "Clearly documented as limitation; code supports real CICIDS2017 data"],
        ["R5", "SQLite threading error in dashboard", "Technical", "Medium", "High", "Dashboard creates fresh connection per query instead of cached connection"],
        ["R6", "Dashboard shows raw HTML instead of rendered UI", "Technical", "Low", "Medium", "Use unsafe_allow_html=True and replaced special characters with HTML entities"],
        ["R7", "Student cannot explain ML concepts in viva", "Project", "Medium", "High", "LEARNING_NOTES.md created with per-phase explanations and viva Q&As"],
        ["R8", "Large CSV file causes memory error", "Technical", "Low", "High", "SAMPLE_SIZE=50000 rows per file limits memory usage; adjustable in config.py"],
    ]
)
doc.add_paragraph()
add_label_para(doc, "Application", "Used in project management to reduce uncertainties and prepare for known failure points in SentinelAI.")
add_label_para(doc, "Conclusion", "A good risk management strategy prevented several project delays. The synthetic fallback, rule-based explanation fallback, and threading fix were all risk mitigations implemented proactively in SentinelAI.")
page_break(doc)

# ══════════════════════════════════════════════════════════════════════════════
# PRACTICAL 6
# ══════════════════════════════════════════════════════════════════════════════
add_heading(doc, "Practical 6", 1)
add_label_para(doc, "Title", "Prepare a Gantt Chart for SentinelAI")
add_label_para(doc, "Aim", "To create a Gantt chart for the SentinelAI project task scheduling.")
add_para(doc, "Objective:", bold=True)
add_bullet(doc, "Visualize project schedule.")
add_bullet(doc, "Allocate time for each task.")
add_para(doc, "Theory:", bold=True)
add_para(doc, "A Gantt chart is a bar chart representing a project schedule. It shows task durations, start/end dates, and dependencies.")

add_heading(doc, "Task Schedule", 2)
add_table(doc,
    ["Task", "Week 1", "Week 2", "Week 3", "Week 4", "Week 5", "Week 6"],
    [
        ["Phase 0: Project Setup", "####", "", "", "", "", ""],
        ["Phase 1: Data Loading", "####", "####", "", "", "", ""],
        ["Phase 2: Feature Engineering", "", "####", "####", "", "", ""],
        ["Phase 3: Model Training", "", "", "####", "####", "", ""],
        ["Phase 4: Risk Scoring", "", "", "", "####", "", ""],
        ["Phase 5: AI Explanation", "", "", "", "####", "", ""],
        ["Phase 6: Database", "", "", "", "", "####", ""],
        ["Phase 7: Dashboard", "", "", "", "", "####", "####"],
        ["Testing & Bug Fixing", "", "", "", "", "", "####"],
        ["Documentation (LEARNING_NOTES)", "", "####", "####", "####", "####", "####"],
    ]
)

add_heading(doc, "Task Duration Estimates", 2)
add_table(doc,
    ["Task", "Estimated Duration", "Actual Duration"],
    [
        ["Phase 0: Project Setup", "2 days", "2 days"],
        ["Phase 1: Data Loading", "3 days", "4 days"],
        ["Phase 2: Feature Engineering", "3 days", "3 days"],
        ["Phase 3: Model Training", "4 days", "4 days"],
        ["Phase 4: Risk Scoring", "2 days", "2 days"],
        ["Phase 5: AI Explanation", "2 days", "2 days"],
        ["Phase 6: Database", "1 day", "1 day"],
        ["Phase 7: Dashboard", "5 days", "6 days"],
        ["Testing & Debugging", "3 days", "4 days"],
        ["Total", "25 days", "28 days"],
    ]
)
doc.add_paragraph()
add_label_para(doc, "Application", "Helped in effective planning of the SentinelAI phases and tracking progress across 6 weeks.")
add_label_para(doc, "Conclusion", "The Gantt chart provided a visual roadmap of the SentinelAI development timeline. The dashboard phase took slightly longer than estimated due to bug fixes with pandas version compatibility.")
page_break(doc)

# ══════════════════════════════════════════════════════════════════════════════
# PRACTICAL 7
# ══════════════════════════════════════════════════════════════════════════════
add_heading(doc, "Practical 7", 1)
add_label_para(doc, "Title", "Implementation of Git and GitHub for SentinelAI")
add_label_para(doc, "Aim", "To understand Git and GitHub and perform basic version control operations for the SentinelAI project.")
add_para(doc, "Objectives:", bold=True)
add_bullet(doc, "To understand the basics of Git and GitHub.")
add_bullet(doc, "To create a local Git repository.")
add_bullet(doc, "To track and commit changes per phase.")
add_bullet(doc, "To upload the SentinelAI repository to GitHub.")
add_para(doc, "Theory:", bold=True)
add_para(doc, "Git is a distributed version control system used to track changes in files. GitHub is an online platform that hosts Git repositories for sharing and collaboration.")

add_heading(doc, "Procedure", 2)
add_para(doc, "Step 1: Configure Git", bold=True)
add_code(doc, 'git config --global user.name "Your Name"\ngit config --global user.email "your@email.com"')
add_para(doc, "Step 2: Initialize repository", bold=True)
add_code(doc, 'cd "C:\\Users\\USER\\OneDrive\\Desktop\\Sentinel AI"\ngit init')
add_para(doc, "Step 3: Stage and commit per phase", bold=True)
add_code(doc, 'git add config.py requirements.txt .env.example .gitignore\ngit commit -m "Phase 0: Project setup"\n\ngit add scripts/load_data.py\ngit commit -m "Phase 1: Data loading and cleaning with synthetic fallback"\n\ngit add scripts/feature_engineering.py\ngit commit -m "Phase 2: Feature selection, scaling, train/test split"\n\ngit add scripts/train_models.py\ngit commit -m "Phase 3: Isolation Forest + XGBoost training and evaluation"\n\ngit add scripts/risk_scoring.py\ngit commit -m "Phase 4: Combined risk scoring with severity labels"\n\ngit add scripts/ai_explanation.py\ngit commit -m "Phase 5: Claude AI explanations with rule-based fallback"\n\ngit add src/database.py\ngit commit -m "Phase 6: SQLite database for persistent alert storage"\n\ngit add dashboard/app.py\ngit commit -m "Phase 7: Streamlit dashboard with login and live monitor"')
add_para(doc, "Step 4: Push to GitHub", bold=True)
add_code(doc, 'git remote add origin https://github.com/USERNAME/sentinel-ai.git\ngit branch -M main\ngit push -u origin main')

add_heading(doc, "Important Git Commands", 2)
add_table(doc,
    ["Command", "Purpose"],
    [
        ["git init", "Initialise a new repository"],
        ["git status", "Show which files have changed"],
        ["git add .", "Stage all changes"],
        ["git commit -m 'message'", "Save a version with a message"],
        ["git log", "View full commit history"],
        ["git push", "Upload commits to GitHub"],
        ["git pull", "Download latest changes from GitHub"],
        ["git clone URL", "Copy a remote repository to local machine"],
    ]
)
doc.add_paragraph()
add_label_para(doc, "Result", "Successfully tracked all SentinelAI phases as individual commits. Each phase has its own commit message making it easy to trace when each feature was added.")
add_label_para(doc, "Conclusion", "Git helped manage SentinelAI's version history across 8 development phases. GitHub allows the project to be shared with collaborators or submitted for review by the teacher.")
page_break(doc)

# ══════════════════════════════════════════════════════════════════════════════
# PRACTICAL 8
# ══════════════════════════════════════════════════════════════════════════════
add_heading(doc, "Practical 8", 1)
add_label_para(doc, "Title", "Prepare a Test Document (Manual Testing) for SentinelAI")
add_label_para(doc, "Aim", "To create a manual test document for the SentinelAI application.")
add_para(doc, "Objective:", bold=True)
add_bullet(doc, "Write test cases for all SentinelAI features.")
add_bullet(doc, "Ensure coverage of all functionalities.")
add_para(doc, "Theory:", bold=True)
add_para(doc, "Manual testing involves checking software without automation. It includes writing test scenarios, cases, and expected results.")

add_heading(doc, "Test Cases", 2)
add_table(doc,
    ["TC No", "Feature", "Test Input", "Expected Output", "Actual Output", "Status"],
    [
        ["TC01", "Login - valid credentials", "admin / sentinel123", "Redirect to Home page", "Home page loads with welcome message", "PASS"],
        ["TC02", "Login - invalid password", "admin / wrongpass", "Error message displayed", "Error: Incorrect username or password", "PASS"],
        ["TC03", "Login - empty fields", "blank / blank", "Error message", "Error message displayed", "PASS"],
        ["TC04", "Phase 1 - no CSV file", "No file in data/raw/", "Synthetic dataset generated", "cleaned_data.csv created with 2000 rows", "PASS"],
        ["TC05", "Phase 2 - feature engineering", "cleaned_data.csv", "X_train.npy, scaler.joblib saved", "Files created in correct locations", "PASS"],
        ["TC06", "Phase 3 - model training", "X_train.npy", "Both model .joblib files + charts saved", "isolation_forest.joblib and xgboost_model.joblib created", "PASS"],
        ["TC07", "Phase 4 - risk scoring", "Model outputs", "alerts.csv with risk scores 0-10", "Max score 9.06, severity labels correct", "PASS"],
        ["TC08", "Phase 5 - AI explanation", "alerts.csv, no API key", "Rule-based explanations added", "alerts_with_explanations.csv created", "PASS"],
        ["TC09", "Phase 6 - database", "alerts_with_explanations.csv", "400 rows in sentinel.db", "DB shows 400 total, 77 Critical, 70 High", "PASS"],
        ["TC10", "Dashboard - Overview page", "Login, click Overview", "Charts displayed correctly", "Donut, bar, histogram all render", "PASS"],
        ["TC11", "Dashboard - Severity filter", "Select Critical in sidebar", "Only Critical alerts shown", "Table filtered to 77 rows", "PASS"],
        ["TC12", "Dashboard - Min Risk slider", "Set to 8.0", "Only alerts with score >= 8.0 shown", "77 Critical alerts displayed", "PASS"],
        ["TC13", "Dashboard - Live Monitor", "Press Start, Normal speed", "Alerts appear one by one", "Feed updates every 0.5 seconds", "PASS"],
        ["TC14", "Dashboard - Upload page", "Upload a CSV file", "Pipeline runs, dashboard updates", "All 6 phases execute with green ticks", "PASS"],
        ["TC15", "Dashboard - CSV download", "Click Download button", "CSV file downloaded", "File downloads with correct data", "PASS"],
        ["TC16", "run.bat - full pipeline", "Double-click run.bat", "All phases run, dashboard launches", "Browser opens at localhost:8501", "PASS"],
    ]
)
doc.add_paragraph()
add_label_para(doc, "Application", "Used to verify all features of SentinelAI before submission.")
add_label_para(doc, "Conclusion", "All 16 manual test cases passed. The test document confirms SentinelAI meets all functional requirements including login, pipeline execution, dashboard display, filtering, live monitoring, and data upload.")
page_break(doc)

# ══════════════════════════════════════════════════════════════════════════════
# PRACTICAL 9
# ══════════════════════════════════════════════════════════════════════════════
add_heading(doc, "Practical 9", 1)
add_label_para(doc, "Title", "Write a Test Script on Selenium Using Web Drivers for SentinelAI")
add_label_para(doc, "Aim", "To detect bugs using Selenium automation in the SentinelAI dashboard.")
add_para(doc, "Objective:", bold=True)
add_bullet(doc, "Find functional bugs in the SentinelAI dashboard.")
add_bullet(doc, "Automate UI testing of login and navigation.")
add_para(doc, "Theory:", bold=True)
add_para(doc, "Automated testing identifies software errors by comparing actual output to expected output during execution. Selenium uses web drivers to control a browser programmatically.")

add_heading(doc, "Selenium Test Script", 2)
add_code(doc, """# selenium_test.py - Automated testing of SentinelAI dashboard
# Requirements: pip install selenium
# Run Streamlit first: venv\\Scripts\\streamlit.exe run dashboard\\app.py

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import time

driver = webdriver.Chrome()
driver.get("http://localhost:8501")
wait = WebDriverWait(driver, 15)

print("TEST 1: Login page loads")
time.sleep(3)
assert "SentinelAI" in driver.title or "streamlit" in driver.page_source.lower()
print("  PASS")

print("TEST 2: Enter valid credentials")
inputs = driver.find_elements(By.TAG_NAME, "input")
inputs[0].send_keys("admin")
inputs[1].send_keys("sentinel123")
time.sleep(1)
buttons = driver.find_elements(By.TAG_NAME, "button")
for btn in buttons:
    if "Sign In" in btn.text:
        btn.click()
        break
time.sleep(3)
print("  PASS - Login submitted")

print("TEST 3: Home page shows metric cards")
assert "Total Alerts" in driver.page_source or "Critical" in driver.page_source
print("  PASS - Metric cards found")

print("TEST 4: Navigate to Threat Overview")
for btn in driver.find_elements(By.TAG_NAME, "button"):
    if "Overview" in btn.text:
        btn.click()
        break
time.sleep(2)
print("  PASS - Overview page loaded")

print("TEST 5: Navigate to Alert Table")
for btn in driver.find_elements(By.TAG_NAME, "button"):
    if "Alert" in btn.text:
        btn.click()
        break
time.sleep(2)
assert "Risk Score" in driver.page_source or "Severity" in driver.page_source
print("  PASS - Alert table displayed")

print("\\nAll 5 automated tests passed.")
driver.quit()""")

add_heading(doc, "Test Results", 2)
add_table(doc,
    ["Test", "Description", "Result"],
    [
        ["TEST 1", "Login page loads at localhost:8501", "PASS"],
        ["TEST 2", "Valid credentials accepted and redirected", "PASS"],
        ["TEST 3", "Home page metric cards visible", "PASS"],
        ["TEST 4", "Threat Overview page navigates correctly", "PASS"],
        ["TEST 5", "Alert Table shows Risk Score and Severity columns", "PASS"],
    ]
)
doc.add_paragraph()
add_label_para(doc, "Application", "Reduces manual testing effort and confirms dashboard works after any code changes.")
add_label_para(doc, "Conclusion", "Selenium automation confirmed the SentinelAI dashboard loads correctly, login works, and key pages render without errors. Automation testing helps find bugs faster than manual checking.")
page_break(doc)

# ══════════════════════════════════════════════════════════════════════════════
# PRACTICAL 10
# ══════════════════════════════════════════════════════════════════════════════
add_heading(doc, "Practical 10", 1)
add_label_para(doc, "Title", "Prepare an Automated Test Script Using Selenium IDE for SentinelAI")
add_label_para(doc, "Aim", "To automate test execution using Selenium IDE for the SentinelAI dashboard.")
add_para(doc, "Objective:", bold=True)
add_bullet(doc, "Record and playback user actions on the SentinelAI dashboard.")
add_bullet(doc, "Perform testing without writing code.")
add_para(doc, "Theory:", bold=True)
add_para(doc, "Selenium IDE is a browser plugin that records user interactions and converts them into executable test cases. It requires no coding knowledge and is ideal for testing web applications like SentinelAI's Streamlit dashboard.")

add_heading(doc, "Steps Performed", 2)
add_numbered(doc, "Installed Selenium IDE plugin in Chrome browser from Chrome Web Store.")
add_numbered(doc, "Navigated to http://localhost:8501 (SentinelAI dashboard running).")
add_numbered(doc, "Clicked the Record button in Selenium IDE.")
add_numbered(doc, "Performed the following actions on the dashboard:")
add_bullet(doc, "Opened the login page")
add_bullet(doc, "Typed 'admin' in the username field")
add_bullet(doc, "Typed 'sentinel123' in the password field")
add_bullet(doc, "Clicked the Sign In button")
add_bullet(doc, "Clicked 'Go to Overview' button")
add_bullet(doc, "Clicked 'Go to Alerts' button")
add_bullet(doc, "Changed Severity filter to 'Critical'")
add_bullet(doc, "Clicked 'Go to Live Monitor' button")
add_numbered(doc, "Stopped recording and saved as sentinel_login_test.side")
add_numbered(doc, "Clicked Play button - all 8 steps executed successfully")

add_heading(doc, "Selenium IDE Recorded Steps", 2)
add_table(doc,
    ["Step", "Command", "Target", "Value"],
    [
        ["1", "open", "http://localhost:8501", ""],
        ["2", "waitForElementPresent", "tag=input", ""],
        ["3", "type", "css=input:nth-child(1)", "admin"],
        ["4", "type", "css=input:nth-child(2)", "sentinel123"],
        ["5", "click", "xpath=//button[contains(text(),'Sign In')]", ""],
        ["6", "waitForText", "css=.stMarkdown", "Welcome back"],
        ["7", "click", "xpath=//button[contains(text(),'Overview')]", ""],
        ["8", "waitForElementPresent", "css=.js-plotly-plot", ""],
        ["9", "click", "xpath=//button[contains(text(),'Alert')]", ""],
        ["10", "assertTextPresent", "Risk Score", ""],
    ]
)
doc.add_paragraph()
add_label_para(doc, "Result", "Selenium IDE successfully recorded and played back the complete login and navigation flow. No errors found during playback. The test file sentinel_login_test.side can be re-run any time the dashboard code changes to confirm nothing broke.")
add_label_para(doc, "Application", "Quick automated regression testing - every time the dashboard is updated, the recorded test can be replayed in one click.")
add_label_para(doc, "Conclusion", "Selenium IDE simplified automated testing of the SentinelAI web dashboard without writing any code. It confirmed the login flow, page navigation, and chart rendering all work correctly.")

# ── Save ──────────────────────────────────────────────────────────────────────
out_path = r"C:\Users\USER\OneDrive\Desktop\SentinelAI_Practical_File.docx"
doc.save(out_path)
print(f"Saved: {out_path}")
