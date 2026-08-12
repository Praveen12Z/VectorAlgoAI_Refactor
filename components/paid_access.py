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
    [data-testid="stAppViewContainer"]{background:radial-gradient(circle at 15% 5%,#102a43 0,#07131f 42%,#050b12 100%)}
    .block-container{max-width:780px;padding-top:7vh}.vai-gate{padding:2.2rem 2.4rem 1.3rem;border:1px solid rgba(45,212,191,.22);border-top:3px solid #2dd4bf;border-radius:20px;background:rgba(9,25,40,.94);box-shadow:0 24px 80px rgba(0,0,0,.35)}
    .vai-kicker{color:#2dd4bf;font-size:.78rem;font-weight:750;letter-spacing:.14em}.vai-gate h1{color:#f4f8fb;margin:.7rem 0 .75rem}.vai-gate p{color:#a9bac9;line-height:1.65}.vai-price{color:#eafcff!important;font-weight:650}
    </style><section class="vai-gate"><div class="vai-kicker">VECTORALGOAI · FOUNDING BETA</div><h1>Build evidence. Trade with conviction.</h1><p>Create your account and activate a verified subscription to enter Strategy Lab.</p><p class="vai-price">€18.99/month · Founding price retained while continuously subscribed.</p></section>
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
