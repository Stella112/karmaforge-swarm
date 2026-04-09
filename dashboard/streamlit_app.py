import streamlit as st
import sqlite3
import pandas as pd
import json
import time
import re
import plotly.graph_objects as go
from datetime import datetime

# --- Setup & Styling ---
st.set_page_config(page_title="KarmaForge Swarm Dashboard", layout="wide", initial_sidebar_state="collapsed")

def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

load_css("/root/karmaforge-swarm/dashboard/ui_theme.css")

# --- Logic: Agent Brain (Log Parsing) ---
def get_agent_reasoning(limit=50):
    try:
        with open("/root/karmaforge-swarm/agent_output.log", "r") as f:
            lines = f.readlines()[-limit:]
        
        reasoning = []
        patterns = [
            (r"Karma:(\d+)/100 → Allowed: (\$\d+\.\d+) \| Drawdown cap: (\d+\.\d+%)", 
             lambda m: f"Risk Guardian: Karma {m.group(1)} validated. Scaling position limit to {m.group(2)} ({m.group(3)} drawdown cap)."),
            (r"RSI: (\d+\.\d+), Momentum: (-?\d+\.\d+)",
             lambda m: f"Strategy Engine: Analyzing market indicators (RSI: {m.group(1)} | Momentum: {m.group(2)})"),
            (r"Validator Agent creating on-chain checkpoint...",
             lambda m: "Validator: Emitting EIP-712 cryptographically signed decision to Sepolia."),
            (r"Signal Agent fetching Kraken data...",
             lambda m: "Signal Scanner: Ingesting high-fidelity market data from Kraken CEX."),
            (r"Mutation successful",
             lambda m: "Reflector: Self-evolution phase complete. Strategy parameters autonomously mutated."),
            (r"--- Starting KarmaForge Cycle (\d+) ---",
             lambda m: f"Swarm: Initializing complex execution cycle #{m.group(1)}.")
        ]
        
        for line in lines:
            timestamp = line[:19]
            for pattern, fmt in patterns:
                match = re.search(pattern, line)
                if match:
                    reasoning.append({"time": timestamp, "text": fmt(match)})
                    break
        return reasoning[::-1] # Newest first
    except:
        return []

# --- Component: Massive Premium Karma Gauge ---
def render_premium_gauge(score, label="VITAL"):
    primary_color = "#00FF9F"
    offset = 440 - (score / 100 * 440)
    
    gauge_html = f"""
    <div style="display: flex; justify-content: center; align-items: center; padding: 20px 0;">
        <div style="position: relative; width: 300px; height: 300px;">
          <svg width="300" height="300" viewBox="0 0 160 160">
            <circle cx="80" cy="80" r="75" fill="none" stroke="rgba(0, 255, 159, 0.05)" stroke-width="2" />
            <circle cx="80" cy="80" r="70" fill="none" stroke="rgba(255,255,255,0.03)" stroke-width="12" />
            <circle cx="80" cy="80" r="70" fill="none" stroke="{primary_color}" stroke-width="12" 
                    stroke-dasharray="440" stroke-dashoffset="{offset}" stroke-linecap="round" 
                    transform="rotate(-90 80 80)" style="transition: stroke-dashoffset 1.5s cubic-bezier(0.4, 0, 0.2, 1); filter: drop-shadow(0 0 8px {primary_color});" />
            <circle cx="80" cy="80" r="58" fill="none" stroke="rgba(0, 240, 255, 0.1)" stroke-width="1" stroke-dasharray="4,4" />
          </svg>
          <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center;">
            <div style="font-size: 0.6rem; color: #8b949e; letter-spacing: 4px; text-transform: uppercase;">Reputation</div>
            <div style="font-size: 5rem; font-weight: 800; color: white; line-height: 0.9; font-family: 'Outfit';">{score}</div>
            <div style="font-size: 0.8rem; color: {primary_color}; font-weight: 700; letter-spacing: 2px; margin-top: 5px;">{label}</div>
          </div>
        </div>
    </div>
    """
    st.markdown(gauge_html, unsafe_allow_html=True)

# --- Data Loading ---
def get_db_connection():
    return sqlite3.connect("/root/karmaforge-swarm/karmaforge.db")

try:
    conn = get_db_connection()
    trades_df = pd.read_sql_query("SELECT * FROM trades ORDER BY timestamp ASC", conn)
    evolution_df = pd.read_sql_query("SELECT * FROM evolution_checkpoints ORDER BY timestamp DESC", conn)
    with open("/root/karmaforge-swarm/config.json", "r") as f:
        config_data = json.load(f)
    conn.close()
    
    # Process Reputation History from Artifacts
    def get_karma(art_json):
        try:
            return json.loads(art_json).get('karma_score', 0)
        except: return 0
    
    if not trades_df.empty:
        # Convert Unix Seconds to Datetime for Plotly
        trades_df['dt'] = pd.to_datetime(trades_df['timestamp'], unit='s')
        trades_df['karma_history'] = trades_df['artifact'].apply(get_karma)
        latest_karma = trades_df.iloc[-1]['karma_history']
    else:
        latest_karma = 13
    
    total_trades = len(trades_df)
    total_pnl = 0.00 
    win_rate = 0.0 
except Exception as e:
    st.error(f"Data Connection Error: {e}")
    trades_df, evolution_df, config_data = pd.DataFrame(), pd.DataFrame(), {}
    total_trades, total_pnl, win_rate, latest_karma = 0, 0.00, 0.0, 0

# --- UI LAYOUT ---

h1, h2 = st.columns([4, 1.2])
with h1:
    st.markdown("<h1 style='margin-bottom: 0;'>🚀 KarmaForge Swarm Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<div style='color: #8b949e; font-size: 0.9rem; margin-top: -5px;'>Autonomous Ethereum Agent Swarm • Production Instance v1.2</div>", unsafe_allow_html=True)
with h2:
    last_run = time.strftime("%H:%M:%S")
    st.markdown(f'<div style="display: flex; justify-content: flex-end; align-items: center; gap: 15px; padding-top: 25px;"><div style="font-size: 0.7rem; color: #8b949e; font-family: \'JetBrains Mono\'">OS_TIME: {last_run}</div><div class="heartbeat">● SWARM ONLINE</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# 1. High-Impact Metrics
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(f'<div class="metric-card"><div class="metric-label">Total Realized PnL</div><div class="metric-value" style="color: #00FF9F;">+${total_pnl:,.2f}</div></div>', unsafe_allow_html=True)
with m2:
    st.markdown(f'<div class="metric-card"><div class="metric-label">Swarm Win Rate</div><div class="metric-value">{win_rate:.0f}%</div></div>', unsafe_allow_html=True)
with m3:
    st.markdown(f'<div class="metric-card"><div class="metric-label">Executed Trade Intents</div><div class="metric-value" style="color: #00F0FF;">{total_trades}</div></div>', unsafe_allow_html=True)
with m4:
    st.markdown(f'<div class="metric-card"><div class="metric-label">Karma Ranking</div><div class="metric-value">{latest_karma}/100</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# 2. Command Center (3-Column Architecture)
col_left, col_mid, col_right = st.columns([1.3, 3, 1.3])

with col_left:
    st.markdown("### 🛰️ AGENT SWARM")
    agents = [
        {"name": "Signal Scanner", "desc": "Monitoring Kraken CEX", "cycles": total_trades},
        {"name": "Risk Guardian", "desc": "Scaling per Karma", "cycles": total_trades},
        {"name": "Strategy Engine", "desc": "RSI/Momentum Logic", "cycles": total_trades},
        {"name": "Validator", "desc": "Signing EIP-712 Intents", "cycles": total_trades},
        {"name": "Reflector", "desc": "Ollama LLM Evolution", "cycles": len(evolution_df)}
    ]
    for agent in agents:
        st.markdown(f"""
        <div class="agent-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="font-weight: 800; font-size: 0.85rem; color: white;">{agent['name']}</div>
                <div class="status-active" style="font-size: 0.5rem; text-transform: uppercase; font-weight: 700; color: #00FF9F;">ACTIVE</div>
            </div>
            <div style="font-size: 0.7rem; color: #8b949e; margin-top: 4px;">{agent['desc']}</div>
            <div style="font-size: 0.6rem; color: #00F0FF; margin-top: 5px; font-family: 'JetBrains Mono';">SYNCCYCLES: {agent['cycles']}</div>
        </div>
        """, unsafe_allow_html=True)

with col_mid:
    # A. Karma Gauge (Top)
    render_premium_gauge(latest_karma, "VITAL" if latest_karma > 10 else "STABLE")
    
    # B. Reputation Timeline (Middle)
    st.markdown('<div class="glass-card" style="padding: 10px 20px;">', unsafe_allow_html=True)
    st.markdown("<h3 style='font-size: 1rem; margin-top: 10px;'>📊 REPUTATION EVOLUTION TIMELINE</h3>", unsafe_allow_html=True)
    if not trades_df.empty:
        fig = go.Figure()
        # Ensure 'dt' and 'karma_history' are used for plotting
        fig.add_trace(go.Scatter(
            x=trades_df['dt'], 
            y=trades_df['karma_history'], 
            mode='lines+markers',
            name='Karma',
            line=dict(color='#00FF9F', width=4, shape='spline'),
            fill='tozeroy',
            fillcolor='rgba(0, 255, 159, 0.05)'
        ))
        
        # Evolution Annotations
        if not evolution_df.empty:
            evolution_df['dt'] = pd.to_datetime(evolution_df['timestamp'], unit='s')
            for idx, row in evolution_df.iterrows():
                fig.add_annotation(
                    x=row['dt'], y=latest_karma,
                    text=f"MUTATION: {row['target_key']}",
                    showarrow=True, arrowhead=2, arrowcolor="#00F0FF",
                    font=dict(size=8, color="#00F0FF"),
                    bgcolor="#05070a", bordercolor="#00F0FF"
                )

        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=10, b=0), height=220, showlegend=False,
            xaxis=dict(showgrid=False, zeroline=False, color='#8b949e', tickfont=dict(size=8)),
            yaxis=dict(showgrid=False, zeroline=False, color='#8b949e', tickfont=dict(size=8), range=[0, 100])
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Gathering historical trust metrics...")
    st.markdown('</div>', unsafe_allow_html=True)

    # C. Agent Brain (Below Timeline)
    st.markdown("### 🧠 AGENT BRAIN (LIVE REASONING)")
    reasoning_feed = get_agent_reasoning()
    if reasoning_feed:
        feed_html = '<div class="reasoning-container">'
        for r in reasoning_feed:
            feed_html += f'<div class="reasoning-line"><span>[{r["time"][11:]}]</span> {r["text"]}</div>'
        feed_html += '</div>'
        st.markdown(feed_html, unsafe_allow_html=True)
    else:
        st.info("Connecting to agent cortex...")
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # D. Swarm Data Insights (Bottom)
    st.markdown("### 📊 SWARM DATA INSIGHTS")
    t1, t2, t3 = st.tabs(["Strategy Evolutions", "Real-Time Trade Log", "On-Chain Artifacts"])
    with t1:
        st.markdown('<div class="glass-card" style="padding: 15px;">', unsafe_allow_html=True)
        if not evolution_df.empty:
            st.dataframe(evolution_df[['timestamp', 'target_key', 'old_value', 'new_value', 'reason']], use_container_width=True)
        else: st.info("No evolution mutations recorded.")
        st.markdown('</div>', unsafe_allow_html=True)
    with t2:
        st.markdown('<div class="glass-card" style="padding: 15px;">', unsafe_allow_html=True)
        if not trades_df.empty:
            st.dataframe(trades_df[['timestamp', 'action', 'pair', 'amount']], use_container_width=True)
        else: st.info("Scanning logs...")
        st.markdown('</div>', unsafe_allow_html=True)
    with t3:
        st.markdown('<div class="glass-card" style="padding: 15px;">', unsafe_allow_html=True)
        if not trades_df.empty:
            latest_art = trades_df.iloc[-1]['artifact']
            try: st.json(json.loads(latest_art))
            except: st.code(latest_art)
        else: st.info("Waiting for artifacts...")
        st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    st.markdown("### ⚙️ LIVE CONFIG")
    st.markdown('<div class="glass-card" style="font-size: 0.75rem; padding: 15px;">', unsafe_allow_html=True)
    if 'strategy' in config_data:
        for k, v in config_data['strategy'].items():
            label = k.replace('_', ' ').upper()
            st.markdown(f"<div style='margin-bottom: 8px;'><span style='color: #8b949e;'>{label}:</span> <span style='color: #00FF9F; float: right;'>{v}</span></div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("### 🛡️ RISK METRICS")
    st.markdown('<div class="glass-card" style="font-size: 0.75rem; padding: 15px;">', unsafe_allow_html=True)
    if 'risk' in config_data:
        metrics = [
            ("MAX DRAWDOWN", f"{config_data['risk'].get('max_drawdown_limit_pct', 0)*100}%"),
            ("KELLY FRACTION", f"{config_data['risk'].get('kelly_fraction', 0)}"),
            ("BASE SIZE USD", f"${config_data['risk'].get('base_position_size_usd', 0)}")
        ]
        for label, val in metrics:
            st.markdown(f"<div style='margin-bottom: 8px;'><span style='color: #8b949e;'>{label}:</span> <span style='color: #00F0FF; float: right;'>{val}</span></div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
