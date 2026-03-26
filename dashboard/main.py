"""
dashboard/main.py
─────────────────
Streamlit dashboard consuming the FastAPI backend.
Real-time sports analytics with charts and match stats.
"""

import os
import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go


# ── Config ─────────────────────────────────────────────────────
API_URL = os.getenv("API_URL", "http://backend:8000")

st.set_page_config(
    page_title="Sports Realtime Dashboard",
    page_icon="⚽",
    layout="wide",
)

# ── Helpers ────────────────────────────────────────────────────
def fetch(path: str):
    try:
        r = requests.get(f"{API_URL}{path}", timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API error: {e}")
        return None


def status_badge(status: str) -> str:
    colors = {"LIVE": "🟢", "FINISHED": "⚫", "SCHEDULED": "🟡"}
    return f"{colors.get(status, '⚪')} {status}"


# ── Header ─────────────────────────────────────────────────────
st.title("⚽ Sports Realtime Dashboard")
st.caption("Real-time analytics powered by Kafka → PostgreSQL → FastAPI")

st.divider()

# ── Load matches ───────────────────────────────────────────────
data = fetch("/matches")
if not data or not data.get("matches"):
    st.warning("No matches found. Make sure the pipeline is running.")
    st.stop()

matches = data["matches"]

# ── Match selector ─────────────────────────────────────────────
def match_label(m):
    score = f"{m.get('home_score') or 0} - {m.get('away_score') or 0}"
    return f"{m['home_team']} vs {m['away_team']}  |  {score}  |  {m['competition']}"

labels = [match_label(m) for m in matches]
selected_idx = st.selectbox("Select a match", range(len(labels)), format_func=lambda i: labels[i])
match = matches[selected_idx]
match_id = match["id"]

st.divider()

# ── Match header ───────────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 2])

with col1:
    st.markdown(f"### 🏠 {match['home_team']}")
with col2:
    st.markdown(f"## {match.get('home_score') or 0}", unsafe_allow_html=True)
with col3:
    st.markdown("## —")
with col4:
    st.markdown(f"## {match.get('away_score') or 0}", unsafe_allow_html=True)
with col5:
    st.markdown(f"### 🛫 {match['away_team']}")

col_a, col_b, col_c = st.columns(3)
with col_a:
    st.markdown(f"**Status:** {status_badge(match.get('status', 'N/A'))}")
with col_b:
    st.markdown(f"**Minute:** ⏱️ {match.get('minute') or 0}'")
with col_c:
    st.markdown(f"**Competition:** 🏆 {match.get('competition', 'N/A')}")

st.divider()

# ── Load timeline ──────────────────────────────────────────────
timeline_data = fetch(f"/matches/{match_id}/timeline")
if not timeline_data or not timeline_data.get("timeline"):
    st.info("No timeline data available yet for this match.")
    st.stop()

df = pd.DataFrame(timeline_data["timeline"])

# ── Charts ─────────────────────────────────────────────────────
st.subheader("📈 Match Analytics")

tab1, tab2, tab3 = st.tabs(["⚽ Score Evolution", "🔵 Possession", "🎯 Shots"])

with tab1:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["minute"], y=df["home_score"],
        mode="lines+markers",
        name=match["home_team"],
        line=dict(color="#3b82f6", width=2),
        marker=dict(size=4),
    ))
    fig.add_trace(go.Scatter(
        x=df["minute"], y=df["away_score"],
        mode="lines+markers",
        name=match["away_team"],
        line=dict(color="#ef4444", width=2),
        marker=dict(size=4),
    ))
    fig.update_layout(
        xaxis_title="Minute",
        yaxis_title="Goals",
        yaxis=dict(tickformat="d", dtick=1),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        height=350,
        margin=dict(l=0, r=0, t=30, b=0),
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=df["minute"], y=df["home_possession"],
        mode="lines", fill="tozeroy",
        name=match["home_team"],
        line=dict(color="#3b82f6", width=2),
        fillcolor="rgba(59,130,246,0.2)",
    ))
    fig2.add_trace(go.Scatter(
        x=df["minute"], y=df["away_possession"],
        mode="lines", fill="tozeroy",
        name=match["away_team"],
        line=dict(color="#ef4444", width=2),
        fillcolor="rgba(239,68,68,0.2)",
    ))
    fig2.add_hline(y=50, line_dash="dash", line_color="gray", opacity=0.5)
    fig2.update_layout(
        xaxis_title="Minute",
        yaxis_title="Possession %",
        yaxis=dict(range=[0, 100]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        height=350,
        margin=dict(l=0, r=0, t=30, b=0),
    )
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=df["minute"], y=df["home_shots"],
        mode="lines+markers",
        name=f"{match['home_team']} shots",
        line=dict(color="#3b82f6", width=2),
    ))
    fig3.add_trace(go.Scatter(
        x=df["minute"], y=df["away_shots"],
        mode="lines+markers",
        name=f"{match['away_team']} shots",
        line=dict(color="#ef4444", width=2),
    ))
    fig3.update_layout(
        xaxis_title="Minute",
        yaxis_title="Shots",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        height=350,
        margin=dict(l=0, r=0, t=30, b=0),
    )
    st.plotly_chart(fig3, use_container_width=True)

st.divider()

# ── Final stats ────────────────────────────────────────────────
st.subheader("📊 Final Stats")

last = df.iloc[-1]

def stat_row(label, home_val, away_val):
    col1, col2, col3, col4, col5 = st.columns([2, 1, 0.5, 1, 2])
    with col1:
        st.markdown(f"<div style='text-align:right; font-size:1.1em'><b>{home_val}</b></div>", unsafe_allow_html=True)
    with col2:
        home_w = home_val >= away_val
        color = "#3b82f6" if home_w else "#6b7280"
        st.markdown(f"<div style='background:{color};height:8px;border-radius:4px'></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div style='text-align:center; color:#9ca3af; font-size:0.85em'>{label}</div>", unsafe_allow_html=True)
    with col4:
        away_w = away_val >= home_val
        color = "#ef4444" if away_w else "#6b7280"
        st.markdown(f"<div style='background:{color};height:8px;border-radius:4px'></div>", unsafe_allow_html=True)
    with col5:
        st.markdown(f"<div style='text-align:left; font-size:1.1em'><b>{away_val}</b></div>", unsafe_allow_html=True)

# Load last match_stats row for cards/fouls/corners
stats_data = fetch(f"/matches/{match_id}/stats")
if stats_data and stats_data.get("stats"):
    last_stats = stats_data["stats"][-1]

    st.markdown(f"<div style='display:flex;justify-content:space-between;padding:0 16px;color:#9ca3af'>"
                f"<span>{match['home_team']}</span><span>{match['away_team']}</span></div>",
                unsafe_allow_html=True)
    st.markdown("")

    stat_row("Shots", last_stats["home_shots"], last_stats["away_shots"])
    stat_row("Shots on Target", last_stats["home_shots_on_target"], last_stats["away_shots_on_target"])
    stat_row("Corners", last_stats["home_corners"], last_stats["away_corners"])
    stat_row("Fouls", last_stats["home_fouls"], last_stats["away_fouls"])
    stat_row("Yellow Cards", last_stats["home_yellow_cards"], last_stats["away_yellow_cards"])
    stat_row("Red Cards", last_stats["home_red_cards"], last_stats["away_red_cards"])
    stat_row("Possession %", last_stats["home_possession"], last_stats["away_possession"])

st.divider()
st.caption("Data pipeline: Kafka → PostgreSQL → FastAPI → Streamlit")