#!/bin/bash
cd /root/karmaforge-swarm
export STREAMLIT_SERVER_HEADLESS=true
export STREAMLIT_SERVER_GATHER_USAGE_STATS=false
/root/karmaforge-swarm/venv/bin/python -m streamlit run /root/karmaforge-swarm/dashboard/streamlit_app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true
