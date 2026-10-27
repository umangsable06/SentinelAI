# dashboard/app.py — SentinelAI Web Dashboard
# RUN: streamlit run dashboard/app.py

import sys
from pathlib import Path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

from src.database import init_db, fetch_alerts, get_stats
import config

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SentinelAI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #0f0f1a; }
[data-testid="stSidebar"]          { background: #13131f; border-right: 1px solid #2a2a3d; }
.block-container { padding-top: 1.5rem; }

/* Cards */
.card {
    background: #1a1a2e;
    border: 1px solid #2a2a3d;
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 12px;
}
.card-title { font-size: 0.85rem; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }
.card-value { font-size: 2.2rem; font-weight: 700; color: #fff; }
.card-sub   { font-size: 0.8rem; color: #666; margin-top: 4px; }

/* Severity badges */
.badge-Critical { background:#3d0a14; color:#f38ba8; border:1px solid #f38ba8; border-radius:6px; padding:2px 10px; font-size:0.8rem; font-weight:600; }
.badge-High     { background:#3d1f0a; color:#fab387; border:1px solid #fab387; border-radius:6px; padding:2px 10px; font-size:0.8rem; font-weight:600; }
.badge-Medium   { background:#3d330a; color:#f9e2af; border:1px solid #f9e2af; border-radius:6px; padding:2px 10px; font-size:0.8rem; font-weight:600; }
.badge-Low      { background:#0a2e14; color:#a6e3a1; border:1px solid #a6e3a1; border-radius:6px; padding:2px 10px; font-size:0.8rem; font-weight:600; }

/* Nav buttons */
.nav-btn { width:100%; text-align:left; padding: 10px 16px; border-radius:8px; border:none;
           background:transparent; color:#888; cursor:pointer; font-size:0.95rem; }
.nav-btn:hover { background:#2a2a3d; color:#fff; }
.nav-btn.active { background:#2a2a3d; color:#fff; border-left: 3px solid #89b4fa; }
</style>
""", unsafe_allow_html=True)

SEV_COLOURS = {"Critical":"#f38ba8","High":"#fab387","Medium":"#f9e2af","Low":"#a6e3a1"}
ATTACK_COLOURS = {"DDoS":"#f38ba8","PortScan":"#fab387","BruteForce":"#cba6f7","Other":"#89dceb","BENIGN":"#a6e3a1"}

USERS = {"admin":"sentinel123", "analyst":"analyst456", "guest":"guest789"}

# ── Session state defaults ────────────────────────────────────────────────────
for key, val in [("logged_in", False), ("username", ""), ("page", "home")]:
    if key not in st.session_state:
        st.session_state[key] = val

# ══════════════════════════════════════════════════════════════════════════════
# LOGIN PAGE
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state.logged_in:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1.2, 1, 1.2])
    with col2:
        st.markdown("""
        <div style='text-align:center; padding: 40px 0 20px 0;'>
            <div style='font-size:3.5rem;'>🛡️</div>
            <div style='font-size:1.8rem; font-weight:700; color:#cdd6f4; margin-top:8px;'>SentinelAI</div>
            <div style='color:#888; margin-top:4px; font-size:0.95rem;'>AI-Powered Network Intrusion Detection</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        username = st.text_input("", placeholder="👤  Username", label_visibility="collapsed")
        password = st.text_input("", placeholder="🔒  Password", type="password", label_visibility="collapsed")
        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("Sign In →", use_container_width=True, type="primary"):
            if username in USERS and USERS[username] == password:
                st.session_state.logged_in = True
                st.session_state.username  = username
                st.session_state.page      = "home"
                st.rerun()
            else:
                st.error("❌  Incorrect username or password.")

        st.markdown("""
        <div style='text-align:center; margin-top:24px; padding:16px; background:#1a1a2e;
                    border-radius:10px; border:1px solid #2a2a3d;'>
            <div style='color:#888; font-size:0.8rem; margin-bottom:8px;'>DEMO ACCOUNTS</div>
            <div style='color:#cdd6f4; font-size:0.85rem;'>admin &nbsp;/&nbsp; sentinel123</div>
            <div style='color:#cdd6f4; font-size:0.85rem;'>analyst &nbsp;/&nbsp; analyst456</div>
            <div style='color:#cdd6f4; font-size:0.85rem;'>guest &nbsp;/&nbsp; guest789</div>
        </div>
        """, unsafe_allow_html=True)
    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# AUTHENTICATED — load data
# ══════════════════════════════════════════════════════════════════════════════
def get_conn():
    """Always create a fresh connection — SQLite connections are not thread-safe."""
    return init_db()

@st.cache_data(ttl=30)
def load_all():
    conn = get_conn()
    df = fetch_alerts(conn)
    conn.close()
    return df

@st.cache_data(ttl=30)
def load_stats():
    conn = get_conn()
    s = get_stats(conn)
    conn.close()
    return s

alerts = load_all()
stats  = load_stats()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style='padding:16px 0 8px 0;'>
        <div style='font-size:1.3rem; font-weight:700; color:#cdd6f4;'>🛡️ SentinelAI</div>
        <div style='font-size:0.8rem; color:#888; margin-top:2px;'>Logged in as <b style='color:#89b4fa;'>{st.session_state.username}</b></div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown("<div style='color:#888; font-size:0.75rem; letter-spacing:1px; margin-bottom:8px;'>NAVIGATION</div>", unsafe_allow_html=True)

    pages = [
        ("home",        "🏠",  "Home"),
        ("overview",    "📊",  "Threat Overview"),
        ("alerts",      "🚨",  "Alert Table"),
        ("live",        "📡",  "Live Monitor"),
        ("upload",      "📤",  "Upload Data"),
        ("performance", "📈",  "Model Performance"),
        ("explain",     "💬",  "AI Explanations"),
    ]

    for key, icon, label in pages:
        active = "color:#89b4fa; font-weight:600;" if st.session_state.page == key else "color:#aaa;"
        if st.button(f"{icon}  {label}", key=f"nav_{key}", use_container_width=True):
            st.session_state.page = key
            st.rerun()

    st.divider()
    st.markdown("<div style='color:#888; font-size:0.75rem; letter-spacing:1px; margin-bottom:8px;'>FILTERS</div>", unsafe_allow_html=True)

    st.markdown("""
    <div style='background:#1a1a2e; border:1px solid #2a2a3d; border-radius:8px; padding:12px; margin-bottom:12px;'>
        <div style='color:#89b4fa; font-size:0.8rem; font-weight:600; margin-bottom:6px;'>ℹ️ About the Filters</div>
        <div style='color:#888; font-size:0.78rem; line-height:1.5;'>
            <b style='color:#cdd6f4;'>Severity</b> is automatically assigned by the AI based on how dangerous the traffic is.<br><br>
            <b style='color:#cdd6f4;'>Min Risk Score</b> lets you hide low-priority alerts. Slide to 8.0 to see only Critical alerts.
        </div>
    </div>
    """, unsafe_allow_html=True)

    sev_filter  = st.selectbox("Severity", ["All","Critical","High","Medium","Low"])
    risk_filter = st.slider("Min Risk Score", 0.0, 10.0, 0.0, 0.5)

    st.divider()
    st.markdown("""
    <div style='background:#1a1a2e; border:1px solid #2a2a3d; border-radius:8px; padding:12px; margin-bottom:8px;'>
        <div style='color:#f9e2af; font-size:0.8rem; font-weight:600; margin-bottom:6px;'>📡 Data Source</div>
        <div style='color:#888; font-size:0.78rem; line-height:1.5;'>
            This system analyses the <b style='color:#cdd6f4;'>CICIDS2017</b> dataset — real network traffic
            captured in a cybersecurity research lab. It is replayed to demonstrate how the system
            would work on a live network.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    if st.button("🚪  Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username  = ""
        st.session_state.page      = "home"
        st.rerun()

# Apply filters
df = alerts.copy()
if sev_filter != "All":
    df = df[df["severity"] == sev_filter]
if risk_filter > 0:
    df = df[df["risk_score"] >= risk_filter]


# ══════════════════════════════════════════════════════════════════════════════
# HOME PAGE
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.page == "home":
    st.markdown(f"""
    <div style='padding: 10px 0 24px 0;'>
        <div style='font-size:1.8rem; font-weight:700; color:#cdd6f4;'>
            Welcome back, {st.session_state.username.capitalize()} 👋
        </div>
        <div style='color:#888; margin-top:4px;'>
            Here's what's happening on your network right now.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── What is this system banner ────────────────────────────────────────────
    st.markdown("""
    <div style='background:#1a1a2e; border:1px solid #2a2a3d; border-left:4px solid #89b4fa;
                border-radius:10px; padding:16px 20px; margin-bottom:24px;'>
        <div style='color:#89b4fa; font-weight:700; font-size:1rem; margin-bottom:8px;'>🛡️ What is SentinelAI?</div>
        <div style='color:#aaa; font-size:0.9rem; line-height:1.7;'>
            SentinelAI is an <b style='color:#cdd6f4;'>AI-powered network intrusion detection system</b>.
            It analyses network traffic flows and automatically detects attacks such as
            <b style='color:#f38ba8;'>DDoS</b>, <b style='color:#fab387;'>Port Scanning</b>,
            and <b style='color:#cba6f7;'>Brute Force</b> attempts.<br><br>
            It uses <b style='color:#cdd6f4;'>two AI models</b> working together:
            one that learns what normal traffic looks like and flags anything unusual,
            and one that identifies the specific attack type.
            Each alert gets a <b style='color:#cdd6f4;'>risk score from 0–10</b> and a
            plain-English explanation of what the threat is and what to do about it.<br><br>
            <span style='color:#f9e2af;'>📡 Currently replaying the CICIDS2017 research dataset
            — real network traffic captured in a cybersecurity lab.</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Top stats ─────────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"""<div class='card'><div class='card-title'>Total Alerts</div>
        <div class='card-value'>{stats.get('total',0):,}</div>
        <div class='card-sub'>All network flows</div></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class='card critical'><div class='card-title'>🔴 Critical</div>
        <div class='card-value' style='color:#f38ba8;'>{stats.get('critical',0):,}</div>
        <div class='card-sub'>Immediate action</div></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class='card'><div class='card-title'>🟠 High</div>
        <div class='card-value' style='color:#fab387;'>{stats.get('high',0):,}</div>
        <div class='card-sub'>Investigate soon</div></div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class='card'><div class='card-title'>🟡 Medium</div>
        <div class='card-value' style='color:#f9e2af;'>{stats.get('medium',0):,}</div>
        <div class='card-sub'>Daily review</div></div>""", unsafe_allow_html=True)
    with c5:
        st.markdown(f"""<div class='card'><div class='card-title'>🟢 Low</div>
        <div class='card-value' style='color:#a6e3a1;'>{stats.get('low',0):,}</div>
        <div class='card-sub'>Log and monitor</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Quick navigation cards ─────────────────────────────────────────────────
    st.markdown("<div style='color:#888; font-size:0.8rem; letter-spacing:1px; margin-bottom:12px;'>QUICK ACCESS</div>", unsafe_allow_html=True)

    q1, q2, q3, q4, q5 = st.columns(5)
    with q1:
        st.markdown("""<div class='card' style='text-align:center;'>
        <div style='font-size:2rem;'>📡</div>
        <div style='color:#f38ba8; font-weight:600; margin-top:8px;'>Live Monitor</div>
        <div style='color:#888; font-size:0.8rem; margin-top:4px;'>Watch alerts arrive in real time</div>
        </div>""", unsafe_allow_html=True)
        if st.button("Go to Live Monitor →", key="home_live", use_container_width=True):
            st.session_state.page = "live"; st.rerun()

    with q2:
        st.markdown("""<div class='card' style='text-align:center;'>
        <div style='font-size:2rem;'>📊</div>
        <div style='color:#cdd6f4; font-weight:600; margin-top:8px;'>Threat Overview</div>
        <div style='color:#888; font-size:0.8rem; margin-top:4px;'>Charts and attack breakdown</div>
        </div>""", unsafe_allow_html=True)
        if st.button("Go to Overview →", key="home_overview", use_container_width=True):
            st.session_state.page = "overview"; st.rerun()

    with q3:
        st.markdown("""<div class='card' style='text-align:center;'>
        <div style='font-size:2rem;'>🚨</div>
        <div style='color:#cdd6f4; font-weight:600; margin-top:8px;'>Alert Table</div>
        <div style='color:#888; font-size:0.8rem; margin-top:4px;'>All flagged network flows</div>
        </div>""", unsafe_allow_html=True)
        if st.button("Go to Alerts →", key="home_alerts", use_container_width=True):
            st.session_state.page = "alerts"; st.rerun()

    with q4:
        st.markdown("""<div class='card' style='text-align:center;'>
        <div style='font-size:2rem;'>📤</div>
        <div style='color:#cdd6f4; font-weight:600; margin-top:8px;'>Upload Data</div>
        <div style='color:#888; font-size:0.8rem; margin-top:4px;'>Analyse your own CSV file</div>
        </div>""", unsafe_allow_html=True)
        if st.button("Go to Upload →", key="home_upload", use_container_width=True):
            st.session_state.page = "upload"; st.rerun()

    with q5:
        st.markdown("""<div class='card' style='text-align:center;'>
        <div style='font-size:2rem;'>📈</div>
        <div style='color:#cdd6f4; font-weight:600; margin-top:8px;'>Model Performance</div>
        <div style='color:#888; font-size:0.8rem; margin-top:4px;'>Confusion matrix and accuracy</div>
        </div>""", unsafe_allow_html=True)
        if st.button("Go to Performance →", key="home_perf", use_container_width=True):
            st.session_state.page = "performance"; st.rerun()

    q6_col = st.columns([1,1,1,1,1])[2]
    with q6_col:
        st.markdown("""<div class='card' style='text-align:center;'>
        <div style='font-size:2rem;'>💬</div>
        <div style='color:#cdd6f4; font-weight:600; margin-top:8px;'>AI Explanations</div>
        <div style='color:#888; font-size:0.8rem; margin-top:4px;'>Plain-English alert summaries</div>
        </div>""", unsafe_allow_html=True)
        if st.button("Go to Explanations →", key="home_explain", use_container_width=True):
            st.session_state.page = "explain"; st.rerun()

    # ── Top 5 critical alerts preview ─────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🔴 Latest Critical Alerts")
    crit = alerts[alerts["severity"] == "Critical"].head(5)
    if len(crit) > 0:
        for _, row in crit.iterrows():
            st.markdown(f"""
            <div class='card' style='display:flex; justify-content:space-between; align-items:center; padding:14px 20px;'>
                <div>
                    <span class='badge-Critical'>Critical</span>
                    <span style='color:#cdd6f4; font-weight:600; margin-left:12px;'>{row['predicted_label']}</span>
                    <span style='color:#666; font-size:0.85rem; margin-left:8px;'>{row['source_ip']} → {row['destination_ip']}</span>
                </div>
                <div style='color:#f38ba8; font-weight:700; font-size:1.1rem;'>{row['risk_score']}/10</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("No Critical alerts with current filters.")


# ══════════════════════════════════════════════════════════════════════════════
# THREAT OVERVIEW PAGE
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "overview":
    st.markdown("## 📊 Threat Overview")
    st.markdown("<div style='color:#888; margin-bottom:20px;'>Visual breakdown of all detected threats</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Severity Distribution")
        sev_counts = df["severity"].value_counts().reset_index()
        sev_counts.columns = ["Severity","Count"]
        sev_counts["Severity"] = pd.Categorical(sev_counts["Severity"],
            categories=["Critical","High","Medium","Low"], ordered=True)
        sev_counts = sev_counts.sort_values("Severity")
        fig = px.pie(sev_counts, values="Count", names="Severity",
                     color="Severity", color_discrete_map=SEV_COLOURS, hole=0.55)
        fig.update_traces(textposition="outside", textinfo="percent+label")
        fig.update_layout(height=340, margin=dict(t=10,b=10,l=10,r=10),
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font_color="#cdd6f4", showlegend=True)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Attack Type Distribution")
        atk = df["predicted_label"].value_counts().reset_index()
        atk.columns = ["Attack","Count"]
        fig2 = px.bar(atk, x="Attack", y="Count", color="Attack",
                      color_discrete_map=ATTACK_COLOURS, text="Count")
        fig2.update_traces(textposition="outside")
        fig2.update_layout(height=340, margin=dict(t=10,b=10,l=10,r=10),
                           showlegend=False, paper_bgcolor="rgba(0,0,0,0)",
                           plot_bgcolor="rgba(0,0,0,0)", font_color="#cdd6f4",
                           xaxis=dict(gridcolor="#2a2a3d"), yaxis=dict(gridcolor="#2a2a3d"))
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("#### Risk Score Distribution")
    fig3 = px.histogram(df, x="risk_score", color="severity",
                        color_discrete_map=SEV_COLOURS, nbins=40,
                        barmode="overlay", opacity=0.8,
                        labels={"risk_score":"Risk Score (0–10)"})
    fig3.update_layout(height=280, margin=dict(t=10,b=10,l=10,r=10),
                       paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                       font_color="#cdd6f4", xaxis=dict(gridcolor="#2a2a3d"),
                       yaxis=dict(gridcolor="#2a2a3d"))
    st.plotly_chart(fig3, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# ALERT TABLE PAGE
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "alerts":
    st.markdown("## 🚨 Alert Table")
    st.markdown(f"<div style='color:#888; margin-bottom:20px;'>Showing <b style='color:#cdd6f4;'>{len(df):,}</b> alerts — sorted by risk score</div>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Alerts shown",    len(df))
    c2.metric("Avg risk score",  f"{df['risk_score'].mean():.2f}" if len(df) else "—")
    c3.metric("Highest risk",    f"{df['risk_score'].max():.2f}"  if len(df) else "—")

    st.markdown("<br>", unsafe_allow_html=True)

    if len(df) == 0:
        st.warning("No alerts match the current filters. Adjust the sidebar filters.")
    else:
        disp = df[["source_ip","destination_ip","predicted_label",
                   "risk_score","severity","if_score","xgb_score"]].rename(columns={
            "source_ip":"Source IP","destination_ip":"Dest IP",
            "predicted_label":"Attack Type","risk_score":"Risk Score",
            "severity":"Severity","if_score":"IF Score","xgb_score":"XGB Score"})

        def colour_sev(val):
            m = {"Critical":"background-color:#3d0a14;color:#f38ba8",
                 "High":    "background-color:#3d1f0a;color:#fab387",
                 "Medium":  "background-color:#3d330a;color:#f9e2af",
                 "Low":     "background-color:#0a2e14;color:#a6e3a1"}
            return m.get(val, "")

        st.dataframe(disp.style.map(colour_sev, subset=["Severity"]),
                     use_container_width=True, hide_index=True, height=550)

        csv = disp.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️  Download as CSV", csv,
                           "sentinel_alerts.csv", "text/csv", use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# MODEL PERFORMANCE PAGE
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "performance":
    st.markdown("## 📈 Model Performance")
    st.markdown("<div style='color:#888; margin-bottom:20px;'>How well the AI models performed on the test dataset</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Confusion Matrix")
        st.caption("Diagonal = correct predictions. Off-diagonal = mistakes.")
        cm = Path(config.REPORTS_DIR) / "confusion_matrix.png"
        if cm.exists():
            st.image(str(cm), use_container_width=True)
        else:
            st.info("Run Phase 3: python scripts/train_models.py")

    with col2:
        st.markdown("#### Top 20 Feature Importances")
        st.caption("Which columns XGBoost relied on most to detect attacks.")
        fi = Path(config.REPORTS_DIR) / "feature_importance.png"
        if fi.exists():
            st.image(str(fi), use_container_width=True)
        else:
            st.info("Run Phase 3: python scripts/train_models.py")

    st.divider()
    st.markdown("#### How the Two Models Work Together")
    col3, col4 = st.columns(2)
    with col3:
        st.markdown("""
        <div class='card'>
        <div class='card-title'>Model A — Isolation Forest</div>
        <br>
        <b style='color:#89b4fa;'>Type:</b> Unsupervised anomaly detection<br><br>
        <b style='color:#89b4fa;'>Trained on:</b> BENIGN (normal) traffic only<br><br>
        <b style='color:#89b4fa;'>How:</b> Builds 100 random trees. Anomalies are isolated faster
        because they are statistical outliers — fewer splits needed.<br><br>
        <b style='color:#89b4fa;'>Strength:</b> Detects zero-day attacks it has never seen before<br><br>
        <b style='color:#89b4fa;'>Weight in risk score:</b> 40%
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div class='card'>
        <div class='card-title'>Model B — XGBoost</div>
        <br>
        <b style='color:#a6e3a1;'>Type:</b> Supervised multi-class classifier<br><br>
        <b style='color:#a6e3a1;'>Trained on:</b> All 5 classes with labels<br><br>
        <b style='color:#a6e3a1;'>How:</b> Builds 100 boosted decision trees, each correcting
        the mistakes of the previous one.<br><br>
        <b style='color:#a6e3a1;'>Strength:</b> High accuracy on known attack types, outputs
        a specific attack name<br><br>
        <b style='color:#a6e3a1;'>Weight in risk score:</b> 60%
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.markdown("#### Risk Score Formula")
    st.code("""Risk Score  =  (0.4 × Isolation Forest Score)
            +  (0.6 × XGBoost Attack Confidence)

Both components are normalised to 0–10 before combining.

Severity:   Critical ≥ 8.0  |  High ≥ 6.0  |  Medium ≥ 4.0  |  Low < 4.0""")


# ══════════════════════════════════════════════════════════════════════════════
# AI EXPLANATIONS PAGE
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "explain":
    st.markdown("## 💬 AI Explanations")
    st.markdown("<div style='color:#888; margin-bottom:20px;'>Plain-English explanations for every flagged alert, generated by AI</div>", unsafe_allow_html=True)

    has_exp = df[df["ai_explanation"].notna() & (df["ai_explanation"] != "")]

    if len(has_exp) == 0:
        st.warning("No explanations found. Run: python scripts/ai_explanation.py")
        st.stop()

    st.info(f"Showing AI explanations for **{len(has_exp):,}** alerts.")

    for sev in ["Critical","High","Medium","Low"]:
        sev_df = has_exp[has_exp["severity"] == sev]
        if len(sev_df) == 0:
            continue

        colour = SEV_COLOURS[sev]
        st.markdown(f"<br><h4 style='color:{colour};'>{sev} Alerts &nbsp;({len(sev_df)})</h4>", unsafe_allow_html=True)

        for _, row in sev_df.head(5).iterrows():
            with st.expander(
                f"Risk {row['risk_score']}/10  |  {row['predicted_label']}  |  "
                f"{row['source_ip']} → {row['destination_ip']}"
            ):
                c1, c2, c3 = st.columns(3)
                c1.metric("Risk Score",  f"{row['risk_score']}/10")
                c2.metric("IF Score",    f"{row['if_score']}/10")
                c3.metric("XGB Score",   f"{row['xgb_score']}/10")
                st.markdown("---")
                st.markdown(f"**What the AI says:**")
                st.write(row["ai_explanation"])

        if len(sev_df) > 5:
            st.caption(f"Showing 5 of {len(sev_df)} {sev} alerts. Use sidebar filters to narrow down.")


# ══════════════════════════════════════════════════════════════════════════════
# LIVE MONITOR PAGE
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "live":
    import time

    st.markdown("## 📡 Live Network Monitor")
    st.markdown("""
    <div style='background:#1a1a2e; border:1px solid #2a2a3d; border-left: 4px solid #89b4fa;
                border-radius:8px; padding:14px 18px; margin-bottom:20px;'>
        <b style='color:#89b4fa;'>How this works:</b>
        <span style='color:#aaa;'> SentinelAI is replaying the CICIDS2017 network traffic dataset
        as if it were arriving live right now. Each row represents a real network flow that was
        captured in a lab environment. The AI analyses each flow and flags threats in real time.</span>
    </div>
    """, unsafe_allow_html=True)

    # Controls
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        speed = st.selectbox("Replay Speed", ["Slow (1s)", "Normal (0.5s)", "Fast (0.1s)"], index=1)
    with col2:
        show_only = st.selectbox("Show Only", ["All", "Critical & High", "Attacks Only"], index=0)
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        start_btn = st.button("▶  Start Live Monitor", type="primary", use_container_width=True)

    delay_map = {"Slow (1s)": 1.0, "Normal (0.5s)": 0.5, "Fast (0.1s)": 0.1}
    delay = delay_map[speed]

    st.divider()

    if start_btn:
        # Filter source data based on user choice
        source = alerts.copy()
        if show_only == "Critical & High":
            source = source[source["severity"].isin(["Critical", "High"])]
        elif show_only == "Attacks Only":
            source = source[source["predicted_label"] != "BENIGN"]

        source = source.reset_index(drop=True)
        total  = len(source)

        # Live stats counters
        live_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}

        # UI placeholders
        st.markdown("#### 📊 Live Statistics")
        stat_cols    = st.columns(4)
        stat_holders = [col.empty() for col in stat_cols]

        st.markdown("#### 🔴 Incoming Alerts Feed")
        feed_holder  = st.empty()
        prog_holder  = st.empty()

        feed_rows = []

        for i, row in source.iterrows():
            live_counts[row["severity"]] += 1

            # Update stat cards
            for j, (sev, col_h) in enumerate(zip(
                ["Critical","High","Medium","Low"], stat_holders
            )):
                colour = list(SEV_COLOURS.values())[j]
                col_h.markdown(f"""
                <div style='background:#1a1a2e; border:1px solid #2a2a3d; border-radius:10px;
                            padding:16px; text-align:center;'>
                    <div style='color:#888; font-size:0.75rem;'>{sev}</div>
                    <div style='color:{colour}; font-size:2rem; font-weight:700;'>{live_counts[sev]}</div>
                </div>""", unsafe_allow_html=True)

            # Build feed entry
            sev   = row["severity"]
            label = row["predicted_label"]
            src   = row["source_ip"]
            dst   = row["destination_ip"]
            score = row["risk_score"]
            expl  = str(row.get("ai_explanation", ""))[:120] + "..."

            badge_colour = SEV_COLOURS.get(sev, "#888")

            feed_rows.insert(0, f"""
            <div style='background:#1a1a2e; border:1px solid #2a2a3d; border-left:4px solid {badge_colour};
                        border-radius:8px; padding:12px 16px; margin-bottom:8px;
                        animation: fadeIn 0.3s ease;'>
                <div style='display:flex; justify-content:space-between; align-items:center;'>
                    <div>
                        <span style='background:{badge_colour}22; color:{badge_colour};
                                     border:1px solid {badge_colour}; border-radius:4px;
                                     padding:2px 8px; font-size:0.75rem; font-weight:600;'>{sev}</span>
                        <span style='color:#cdd6f4; font-weight:600; margin-left:10px;'>{label}</span>
                        <span style='color:#666; font-size:0.85rem; margin-left:8px;'>{src} &rarr; {dst}</span>
                    </div>
                    <div style='color:{badge_colour}; font-weight:700; font-size:1.1rem;'>{score}/10</div>
                </div>
                <div style='color:#888; font-size:0.8rem; margin-top:6px;'>{expl}</div>
            </div>
            """)

            # Show last 12 alerts in feed
            feed_html = (
                "<style>@keyframes fadeIn{from{opacity:0}to{opacity:1}}</style>"
                + "".join(feed_rows[:12])
            )
            feed_holder.markdown(feed_html, unsafe_allow_html=True)

            # Progress bar
            prog_holder.progress(
                (i + 1) / total,
                text=f"Analysing flow {i+1} of {total} — {row['predicted_label']} detected"
            )

            time.sleep(delay)

        st.success(f"✅ Replay complete. Analysed {total:,} network flows.")

    else:
        # Instructions when not started yet
        st.markdown("""
        <div style='text-align:center; padding:60px 20px; color:#666;'>
            <div style='font-size:3rem;'>📡</div>
            <div style='font-size:1.1rem; margin-top:12px; color:#888;'>
                Press <b style='color:#cdd6f4;'>Start Live Monitor</b> above to begin replaying network traffic.
            </div>
            <div style='font-size:0.85rem; margin-top:8px;'>
                The system will analyse each network flow one by one and display alerts as they are detected.
            </div>
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# UPLOAD DATA PAGE
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "upload":
    import subprocess

    st.markdown("## 📤 Upload New Data")
    st.markdown("""
    <div style='background:#1a1a2e; border:1px solid #2a2a3d; border-left:4px solid #a6e3a1;
                border-radius:10px; padding:16px 20px; margin-bottom:24px;'>
        <div style='color:#a6e3a1; font-weight:700; font-size:1rem; margin-bottom:8px;'>How this works</div>
        <div style='color:#aaa; font-size:0.9rem; line-height:1.8;'>
            1. Upload a CSV file containing network traffic data<br>
            2. The system saves it to <code>data/raw/</code><br>
            3. It automatically runs the full pipeline (clean → train → score → explain → store)<br>
            4. All dashboard pages update with the new results
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### Supported File Format")
    st.markdown("""
    <div style='background:#1a1a2e; border:1px solid #2a2a3d; border-radius:8px; padding:14px 18px; margin-bottom:20px;'>
        <div style='color:#aaa; font-size:0.88rem; line-height:1.8;'>
            <b style='color:#cdd6f4;'>Expected format:</b> CICIDS2017-style CSV with network flow columns<br>
            <b style='color:#cdd6f4;'>Required column:</b> <code>Label</code> (attack type) or <code> Label</code> (with space)<br>
            <b style='color:#cdd6f4;'>Example labels:</b> BENIGN, DDoS, PortScan, FTP-Patator, SSH-Patator, Bot<br>
            <b style='color:#cdd6f4;'>No CSV?</b> Leave blank — the system will use its built-in synthetic demo data
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])

    with col1:
        uploaded_file = st.file_uploader(
            "Drop your CSV here or click to browse",
            type=["csv"],
            help="Upload a CICIDS2017-format CSV file. Max recommended size: 100MB"
        )

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        use_demo = st.checkbox("Use demo data instead", value=False)
        st.caption("Tick this to run with the built-in synthetic dataset")

    st.markdown("<br>", unsafe_allow_html=True)

    run_btn = st.button("🚀  Run Full Analysis Pipeline", type="primary", use_container_width=True)

    if run_btn:
        raw_dir = Path(config.RAW_DATA_DIR)
        raw_dir.mkdir(parents=True, exist_ok=True)

        if uploaded_file is not None and not use_demo:
            # Save uploaded file to data/raw/
            save_path = raw_dir / uploaded_file.name
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"File saved: {uploaded_file.name} ({uploaded_file.size / 1024:.1f} KB)")
        elif use_demo:
            # Remove any existing CSVs so synthetic fallback triggers
            for f in raw_dir.glob("*.csv"):
                f.unlink()
            st.info("Using built-in synthetic demo data.")
        else:
            st.warning("No file uploaded. Using existing data in data/raw/ (or synthetic fallback).")

        st.markdown("---")
        st.markdown("#### Running Pipeline...")

        steps = [
            ("Phase 1 — Loading & Cleaning",      ["venv\\Scripts\\python.exe", "scripts\\load_data.py"]),
            ("Phase 2 — Feature Engineering",      ["venv\\Scripts\\python.exe", "scripts\\feature_engineering.py"]),
            ("Phase 3 — Training Models",          ["venv\\Scripts\\python.exe", "scripts\\train_models.py"]),
            ("Phase 4 — Risk Scoring",             ["venv\\Scripts\\python.exe", "scripts\\risk_scoring.py"]),
            ("Phase 5 — AI Explanations",          ["venv\\Scripts\\python.exe", "scripts\\ai_explanation.py"]),
            ("Phase 6 — Saving to Database",       ["venv\\Scripts\\python.exe", "src\\database.py"]),
        ]

        progress_bar = st.progress(0)
        all_ok = True

        for idx, (label, cmd) in enumerate(steps):
            with st.spinner(f"{label}..."):
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=str(ROOT)
                )
                progress_bar.progress((idx + 1) / len(steps))

                if result.returncode == 0:
                    st.success(f"✅ {label}")
                else:
                    st.error(f"❌ {label} failed")
                    st.code(result.stderr[-500:] if result.stderr else "No error output")
                    all_ok = False
                    break

        if all_ok:
            # Clear caches so dashboard reloads fresh data
            st.cache_data.clear()
            st.markdown("---")
            st.success("🎉 Pipeline complete! All pages have been updated with the new data.")
            st.balloons()
            if st.button("Go to Home →", use_container_width=True, type="primary"):
                st.session_state.page = "home"
                st.rerun()
