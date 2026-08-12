# Streamlit Cloud entry point
import streamlit as st

from components.paid_access import require_paid_access
from mvp_dashboard import run_mvp_dashboard

st.set_page_config(page_title="VectorAlgoAI – Strategy Research", page_icon="V", layout="wide")

if require_paid_access():
    run_mvp_dashboard()
