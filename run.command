#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
pip install -r requirements.txt -q
open -a "Google Chrome" http://localhost:8501 &
streamlit run app.py --server.headless true
