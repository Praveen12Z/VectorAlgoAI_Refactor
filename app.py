# app.py
# Entry point for Streamlit Cloud

import hmac

import streamlit as st

from mvp_dashboard import run_mvp_dashboard


st.set_page_config(
    page_title="VectorAlgoAI – Strategy Research",
    page_icon="V",
    layout="wide",
)


def _configured_access_code() -> str:
    """Read the temporary private-beta code without exposing it to the client."""
    try:
        return str(st.secrets["access_gate"]["code"]).strip()
    except (KeyError, TypeError, AttributeError):
        return ""


def _unlock_strategy_lab() -> None:
    submitted_code = st.session_state.get("access_code", "")
    configured_code = _configured_access_code()

    if configured_code and hmac.compare_digest(submitted_code, configured_code):
        st.session_state["strategy_lab_unlocked"] = True
        st.session_state.pop("access_code", None)
        return

    st.session_state["strategy_lab_unlocked"] = False
    st.session_state["access_code_error"] = True


def _render_access_gate() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"] {
            background: radial-gradient(circle at 15% 5%, #102a43 0, #07131f 42%, #050b12 100%);
        }
        .block-container { max-width: 760px; padding-top: 10vh; }
        .vai-gate {
            padding: 2.4rem 2.5rem 1.4rem;
            border: 1px solid rgba(45, 212, 191, .22);
            border-top: 3px solid #2dd4bf;
            border-radius: 20px;
            background: rgba(9, 25, 40, .92);
            box-shadow: 0 24px 80px rgba(0, 0, 0, .35);
        }
        .vai-kicker { color: #2dd4bf; font-size: .78rem; font-weight: 750; letter-spacing: .14em; }
        .vai-gate h1 { color: #f4f8fb; margin: .7rem 0 .75rem; font-size: 2.25rem; }
        .vai-gate p { color: #a9bac9; font-size: 1.02rem; line-height: 1.65; }
        .vai-price { color: #eafcff !important; font-weight: 650; }
        div[data-testid="stForm"] {
            margin-top: 1rem; padding: 1.4rem 1.5rem;
            border: 1px solid rgba(83, 155, 191, .24); border-radius: 16px;
            background: rgba(7, 19, 31, .92);
        }
        </style>
        <section class="vai-gate">
          <div class="vai-kicker">VECTORALGOAI · PRIVATE FOUNDING BETA</div>
          <h1>Strategy Lab access</h1>
          <p>The working research platform is available only to approved founding members while secure subscriptions are being introduced.</p>
          <p class="vai-price">Founding Beta: €18.99/month · Price locked while continuously subscribed.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    if not _configured_access_code():
        st.warning("Strategy Lab access is temporarily unavailable. Please contact the VectorAlgoAI team.")
        st.link_button("Return to VectorAlgoAI", "https://www.vectoralgoai.com/", use_container_width=True)
        return

    with st.form("private_access", clear_on_submit=False):
        st.text_input(
            "Private access code",
            type="password",
            key="access_code",
            placeholder="Enter your founding access code",
        )
        st.form_submit_button("Unlock Strategy Lab", on_click=_unlock_strategy_lab, use_container_width=True)

    if st.session_state.pop("access_code_error", False):
        st.error("That access code is not valid.")

    st.caption("Paid account login and Stripe billing are coming next. Access codes are temporary and must not be shared.")


if st.session_state.get("strategy_lab_unlocked", False):
    with st.sidebar:
        if st.button("Lock Strategy Lab", use_container_width=True):
            st.session_state["strategy_lab_unlocked"] = False
            st.rerun()
    run_mvp_dashboard()
else:
    _render_access_gate()
