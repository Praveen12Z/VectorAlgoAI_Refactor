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
    [data-testid="stAppViewContainer"]{background:radial-gradient(circle at 18% 4%,#151a33 0,#080b18 42%,#050712 100%)}
    .block-container{max-width:500px;padding-top:4vh;padding-bottom:4rem}
    .vai-brand-lockup{display:flex;align-items:center;justify-content:center;gap:.75rem;margin:0 auto 1rem;color:#f7f9ff}
    .vai-logo-mark{width:54px;height:54px;color:#8ea0ff;flex:0 0 54px}
    .vai-logo-mark svg{width:100%;height:100%;display:block}
    .vai-wordmark{font-size:1.1rem;font-weight:750;line-height:1.15;letter-spacing:-.02em}
    .vai-tagline{color:#9ba9bd;font-size:.67rem;font-style:italic;letter-spacing:.1em;margin-top:.22rem}
    .vai-gate{padding:1.45rem 1.5rem 1.2rem;border:1px solid rgba(142,160,255,.24);border-top:3px solid #8ea0ff;border-radius:16px;background:rgba(10,14,31,.92);box-shadow:0 24px 80px rgba(0,0,0,.35);text-align:center}
    .vai-kicker{color:#8ea0ff;font-size:.69rem;font-weight:750;letter-spacing:.14em}
    .vai-gate h1{color:#f7f9ff;margin:.58rem 0 .35rem;font-size:1.85rem}
    .vai-gate p{color:#aab6c8;line-height:1.55;margin:.2rem 0 .75rem}
    .vai-price{display:inline-flex;color:#eef1ff!important;background:rgba(142,160,255,.1);border:1px solid rgba(142,160,255,.22);border-radius:999px;padding:.35rem .7rem;font-size:.76rem;font-weight:650}
    [data-baseweb="tab-list"]{gap:.25rem;border-bottom:1px solid rgba(148,163,184,.22);margin-top:.85rem}
    [data-baseweb="tab-list"] button{color:#a9bfd3!important;font-weight:650}
    [data-baseweb="tab-list"] button[aria-selected="true"]{color:#8ea0ff!important}
    [data-baseweb="tab-panel"]{padding-top:1rem}
    [data-testid="stForm"]{border:1px solid rgba(148,163,184,.18);background:rgba(6,10,24,.55);border-radius:14px}
    [data-testid="stForm"] label p,[data-testid="stWidgetLabel"] p,.stCheckbox label p{color:#dce8f3!important}
    [data-testid="stTextInput"] input{background:#f8fafc!important;color:#0f172a!important;border:1px solid #cbd5e1!important}
    [data-testid="stTextInput"] input::placeholder{color:#64748b!important}
    [data-testid="stFormSubmitButton"] button{background:#4f68db!important;color:#fff!important;border-color:#4f68db!important;font-weight:700;border-radius:8px!important}
    [data-testid="stFormSubmitButton"] button:hover{background:#4058c8!important;border-color:#4058c8!important}
    </style>
    <div class="vai-brand-lockup">
      <div class="vai-logo-mark">
        <svg viewBox="0 0 72 72" fill="none" aria-hidden="true">
          <circle cx="14" cy="15" r="7" fill="currentColor"/><circle cx="28" cy="59" r="5" fill="currentColor"/>
          <circle cx="46" cy="14" r="4" fill="currentColor"/><circle cx="9" cy="39" r="4" fill="currentColor"/>
          <path d="M22 33 38 11" stroke="currentColor" stroke-width="9" stroke-linecap="round"/>
          <path d="M35 42 48 24" stroke="currentColor" stroke-width="9" stroke-linecap="round"/>
          <path d="M40 58 56 36" stroke="currentColor" stroke-width="9" stroke-linecap="round"/>
          <path d="M55 29 66 14" stroke="currentColor" stroke-width="9" stroke-linecap="round"/>
        </svg>
      </div>
      <div><div class="vai-wordmark">Vector AlgoAI</div><div class="vai-tagline">“Edge Over Ego.”</div></div>
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
