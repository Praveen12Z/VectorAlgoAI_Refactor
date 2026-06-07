VectorAlgoAI Phase 2 Refactor Pack

What changed:
1. mvp_dashboard.py is cleaned and now calls Streamlit UI components instead of holding all research UI code inline.
2. Added components/ folder:
   - research_panel.py
   - doctor_panel.py
   - root_cause_panel.py
   - gradecard_panel.py
3. Added core/gradecard.py for Institutional Readiness.
4. Updated core/strategy_doctor.py with stronger severity logic.
5. Updated requirements.txt to use yfinance and remove Polygon dependency.
6. Updated core/data_loader.py to Yahoo Finance version if available.

How to use:
- Upload/replace the files in your GitHub repository.
- Make sure components/ is at the same level as core/ and mvp_dashboard.py.
- Push to GitHub and reboot Streamlit Cloud.

Expected dashboard order:
Research Report -> Strategy Doctor -> Root Cause Analysis -> Institutional Gradecard -> Strategy Evidence -> Performance Analytics -> Trade Evidence.
