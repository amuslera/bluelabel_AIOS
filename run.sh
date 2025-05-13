#!/bin/bash

# Kill any existing Streamlit processes
pkill -f streamlit
sleep 1

# Set PYTHONPATH and run Streamlit
PYTHONPATH=$PWD streamlit run app/ui/streamlit_app.py --server.port=8502 --server.address=127.0.0.1 