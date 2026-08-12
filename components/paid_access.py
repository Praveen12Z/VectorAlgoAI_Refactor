"""Streamlit UI for authenticated, webhook-verified paid access."""
from __future__ import annotations

import streamlit as st

from core.auth import AccessConfigurationError, AccessServiceError, AuthSession, SupabaseAccessClient

APP_URL = "https://vectoralgoai.streamlit.app"


def _client() -> SupabaseAccessClient:
    try:
        config = st.secrets["supabase"]
        return SupabaseAccessClient(config["url"], config["anon_key"])
    except (KeyError, TypeError, AttributeError) as exc:
        raise AccessConfigurationError("Paid access is not configured.") from exc


def _session() -> AuthSession | None:
    value = st.session_state.get("auth_session")
    return value if isinstance(value, AuthSession) else None


def _logout() -> None:
    st.session_state.pop("auth_session", None)
    st.rerun()


def _style() -> None:
    st.markdown("""
    <style>
    [data-testid="stAppViewContainer"]{background:linear-gradient(145deg,#f8faff 0%,#eef3fb 56%,#edf8f7 100%);color:#10233f}
    [data-testid="stHeader"]{background:rgba(248,250,255,.94);border-bottom:1px solid #e1e7f0}
    .block-container{max-width:520px;padding-top:3.8rem!important;padding-bottom:4rem!important}
    .vai-login-brand{display:flex!important;align-items:center!important;justify-content:center!important;gap:.8rem!important;margin:0 auto 1.35rem!important;min-height:66px!important;overflow:visible!important}
    .vai-login-symbol{width:62px!important;height:62px!important;color:#8295f5!important;flex:0 0 62px!important;overflow:visible!important}
    .vai-login-symbol svg{width:62px!important;height:62px!important;display:block!important;overflow:visible!important}
    .vai-login-brand-copy{display:block!important;min-width:170px!important;text-align:left!important;overflow:visible!important}
    .vai-login-brand-name{display:block!important;color:#0a2147!important;font-size:1.25rem!important;font-weight:800!important;line-height:1.15!important;letter-spacing:-.025em!important;white-space:nowrap!important;visibility:visible!important;opacity:1!important}
    .vai-login-tagline{display:block!important;color:#66758b!important;font-size:.68rem!important;font-style:italic!important;letter-spacing:.1em!important;margin-top:.28rem!important;white-space:nowrap!important}
    .vai-gate{position:relative;padding:1.45rem 1.5rem 1.25rem;border:1px solid #d9e1ee;border-radius:16px;background:#fff;box-shadow:0 20px 60px rgba(32,59,97,.11);text-align:center;overflow:hidden}
    .vai-gate::before{content:"";position:absolute;inset:0 0 auto;height:4px;background:linear-gradient(90deg,#8295f5,#43bdb6)}
    .vai-kicker{color:#5369d9;font-size:.68rem;font-weight:750;letter-spacing:.14em}
    .vai-gate h1{color:#0a2147;margin:.62rem 0 .38rem;font-size:1.82rem;line-height:1.15}
    .vai-gate p{color:#607086;line-height:1.55;margin:.2rem 0 .78rem}
    .vai-price{display:inline-flex;color:#233b78!important;background:#eef1ff;border:1px solid #d2d9ff;border-radius:999px;padding:.36rem .72rem;font-size:.76rem;font-weight:650}
    [data-baseweb="tab-list"]{gap:.25rem;border-bottom:1px solid #dfe6ef;margin-top:.9rem}
    [data-baseweb="tab-list"] button{color:#607086!important;font-weight:650}
    [data-baseweb="tab-list"] button[aria-selected="true"]{color:#4f64d8!important}
    [data-baseweb="tab-list"] [data-baseweb="tab-highlight"]{background:#4f64d8!important}
    [data-baseweb="tab-panel"]{padding-top:1rem}
    [data-testid="stForm"]{border:1px solid #d9e1ee!important;background:#fff!important;border-radius:14px!important;box-shadow:0 12px 34px rgba(32,59,97,.08)!important}
    [data-testid="stForm"] label p,[data-testid="stWidgetLabel"] p,.stCheckbox label p{color:#263b58!important}
    [data-testid="stTextInput"] input{background:#fff!important;color:#10233f!important;border:1px solid #cbd6e4!important;border-radius:8px!important}
    [data-testid="stTextInput"] input:focus{border-color:#8295f5!important;box-shadow:0 0 0 1px #8295f5!important}
    [data-testid="stTextInput"] input::placeholder{color:#7b899d!important}
    [data-testid="stTextInput"] svg{fill:#52657f!important}
    [data-testid="stFormSubmitButton"] button{background:#5268db!important;color:#fff!important;border-color:#5268db!important;font-weight:700;border-radius:8px!important}
    [data-testid="stFormSubmitButton"] button:hover{background:#4257c7!important;border-color:#4257c7!important}
    [data-testid="stAlert"]{color:#10233f!important}
    </style>
    <div class="vai-login-brand">
      <div class="vai-login-symbol">
        <svg viewBox="0 0 76 76" fill="none" aria-hidden="true">
          <circle cx="16" cy="17" r="7" fill="currentColor"/><circle cx="30" cy="61" r="5" fill="currentColor"/>
          <circle cx="48" cy="16" r="4" fill="currentColor"/><circle cx="11" cy="41" r="4" fill="currentColor"/>
          <path d="M24 35 40 13" stroke="currentColor" stroke-width="9" stroke-linecap="round"/>
          <path d="M37 44 50 26" stroke="currentColor" stroke-width="9" stroke-linecap="round"/>
          <path d="M42 60 58 38" stroke="currentColor" stroke-width="9" stroke-linecap="round"/>
          <path d="M57 31 68 16" stroke="currentColor" stroke-width="9" stroke-linecap="round"/>
        </svg>
      </div>
      <div class="vai-login-brand-copy">
        <div class="vai-login-brand-name">Vector AlgoAI</div>
        <div class="vai-login-tagline">“Edge Over Ego.”</div>
      </div>
    </div>
    <section class="vai-gate">
      <div class="vai-kicker">SECURE MEMBER ACCESS</div>
      <h1>Welcome to Strategy Lab</h1>
      <p>Sign in or create your account to build evidence before execution.</p>
      <span class="vai-price">Founding plan · €18.99/month</span>
    </section>
    """, unsafe_allow_html=True)

def _render_logged_out(client: SupabaseAccessClient) -> None:
    login_tab, signup_tab, reset_tab = st.tabs(["Sign in", "Create account", "Reset password"])
    with login_tab:
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Sign in", use_container_width=True)
        if submitted:
            try:
                st.session_state["auth_session"] = client.sign_in(email, password)
                st.rerun()
            except AccessServiceError as exc:
                st.error(str(exc))
    with signup_tab:
        with st.form("signup_form"):
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Password", type="password", key="signup_password")
            confirmed = st.text_input("Confirm password", type="password")
            accepted = st.checkbox("I agree to the Terms and Privacy Policy")
            submitted = st.form_submit_button("Create account", use_container_width=True)
        if submitted:
            if len(password) < 8:
                st.error("Use a password with at least 8 characters.")
            elif password != confirmed:
                st.error("Passwords do not match.")
            elif not accepted:
                st.error("Please accept the Terms and Privacy Policy.")
            else:
                try:
                    signed_in = client.sign_up(email, password)
                    st.success("Account created. Sign in to continue." if signed_in else
                               "Check your email to confirm your account, then sign in.")
                except AccessServiceError as exc:
                    st.error(str(exc))
    with reset_tab:
        with st.form("reset_form"):
            email = st.text_input("Account email", key="reset_email")
            submitted = st.form_submit_button("Send reset email", use_container_width=True)
        if submitted:
            try:
                client.send_password_reset(email, APP_URL)
                st.success("If the account exists, Supabase has sent a password-reset email.")
            except AccessServiceError as exc:
                st.error(str(exc))


def _render_subscription(client: SupabaseAccessClient, session: AuthSession) -> bool:
    try:
        subscription = client.subscription(session)
    except AccessServiceError:
        st.error("We could not verify your subscription. Strategy Lab remains locked.")
        if st.button("Sign out", use_container_width=True):
            _logout()
        return False
    if subscription.grants_access:
        with st.sidebar:
            st.caption(f"Signed in as {session.email}")
            if subscription.cancel_at_period_end:
                st.warning("Your subscription will end after the current billing period.")
            if st.button("Open billing portal", use_container_width=True):
                try:
                    st.session_state["portal_url"] = client.invoke("customer-portal", session)
                except AccessServiceError as exc:
                    st.error(str(exc))
            if st.session_state.get("portal_url"):
                st.link_button("Continue to secure billing", st.session_state["portal_url"], use_container_width=True)
            if st.button("Sign out", use_container_width=True):
                _logout()
        return True
    st.subheader("Activate Strategy Lab")
    st.write("Your account is confirmed, but it does not have an active subscription yet.")
    if "checkout_url" not in st.session_state:
        try:
            st.session_state["checkout_url"] = client.invoke("create-checkout", session)
        except AccessServiceError as exc:
            st.error(str(exc))
    if st.session_state.get("checkout_url"):
        st.link_button("Subscribe securely — €18.99/month", st.session_state["checkout_url"], use_container_width=True)
    if st.button("I paid — refresh access", use_container_width=True):
        st.rerun()
    if st.button("Sign out", use_container_width=True):
        _logout()
    st.caption("Access activates only after Stripe's signed webhook confirms the subscription.")
    return False


def require_paid_access() -> bool:
    _style()
    try:
        client = _client()
    except AccessConfigurationError:
        st.error("Strategy Lab access is temporarily unavailable.")
        return False
    session = _session()
    if session is None:
        _render_logged_out(client)
        return False
    return _render_subscription(client, session)
