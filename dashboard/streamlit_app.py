import streamlit as st
import sqlite3
import pandas as pd
import json

st.set_page_config(page_title="KarmaForge Dashboard", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS for dark theme and glassmorphism
st.markdown("""
<style>
    .reportview-container { background: #0e1117; color: #fff; }
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 10px;
        border: 1px solid rgba(0, 255, 0, 0.2);
        padding: 20px;
        margin-bottom: 20px;
    }
    .karma-circle {
        border-radius: 50%; width: 120px; height: 120px;
        border: 4px solid #00ff00;
        display: flex; align-items: center; justify-content: center;
        font-size: 32px; font-weight: bold; margin: 0 auto;
        color: #00ff00; box-shadow: 0 0 20px rgba(0, 255, 0, 0.5);
    }
</style>
""", unsafe_allow_html=True)

def load_data():
    try:
        conn = sqlite3.connect('../karmaforge.db')
        trades = pd.read_sql_query("SELECT * FROM trades ORDER BY timestamp DESC LIMIT 10", conn)
        checkpoints = pd.read_sql_query("SELECT * FROM evolution_checkpoints ORDER BY timestamp DESC", conn)
        conn.close()
        return trades, checkpoints
    except Exception:
        return pd.DataFrame(), pd.DataFrame()

def load_config():
    try:
        with open("../config.json", "r") as f:
            return json.load(f)
    except:
        return {}

st.title("🗡️ KarmaForge Swarm")
st.markdown("*Self-Evolving Verifiable AI Trading Agent*")

trades_df, checkpoints_df = load_data()
config = load_config()

col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center'>Live Karma Score</h3>", unsafe_allow_html=True)
    st.markdown('<div class="karma-circle">75/100</div>', unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; margin-top: 10px;'>Status: Sovereign. Evolving.</p>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("Evolution Timeline (Checkpoints)")
    if not checkpoints_df.empty:
        st.dataframe(checkpoints_df, use_container_width=True)
    else:
        st.info("No evolution checkpoints recorded yet. Reticulating splines...")
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("Live Config Parameters")
    st.json(config.get("strategy", {}))
    st.json(config.get("risk", {}))
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.subheader("Recent On-Chain Trade Artifacts (Validation Log)")
if not trades_df.empty:
    st.dataframe(trades_df[['action', 'amount', 'pair', 'timestamp']], use_container_width=True)
else:
    st.info("Waiting for first signal execution loop...")
st.markdown('</div>', unsafe_allow_html=True)
