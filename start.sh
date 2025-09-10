#!/bin/bash
# start.sh - Production startup script

# Set environment variables
export STREAMLIT_SERVER_HEADLESS=true
export STREAMLIT_SERVER_PORT=${PORT:-8501}
export STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Start the Streamlit app
streamlit run app.py \
    --server.port=$STREAMLIT_SERVER_PORT \
    --server.address=$STREAMLIT_SERVER_ADDRESS \
    --server.headless=$STREAMLIT_SERVER_HEADLESS \
    --browser.gatherUsageStats=false
