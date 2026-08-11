# app.py
# Entry point for Streamlit Cloud

import streamlit as st
from mvp_dashboard import run_mvp_dashboard

st.set_page_config(
    page_title="VectorAlgoAI – Strategy Research",
    page_icon="📐",
    layout="wide",
)

run_mvp_dashboard()
