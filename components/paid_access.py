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


def _style(authenticated: bool = False) -> None:
    if authenticated:
        st.markdown("""
        <style>
        [data-testid="stAppViewContainer"]{background:#f4f7fb;color:#10233f}
        [data-testid="stHeader"]{background:transparent}
        </style>
        """, unsafe_allow_html=True)
        return
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
    .stButton button[kind="secondary"]{color:#5268db!important;border:0!important;background:transparent!important;box-shadow:none!important;font-weight:650!important;padding:.25rem .1rem!important}
    .stButton button[kind="secondary"]:hover{color:#4257c7!important;text-decoration:underline!important}
    [data-testid="stAlert"]{color:#10233f!important}
    .vai-payment-success{margin:1rem 0;padding:1.25rem 1.3rem;border:1px solid #b9dfd9;border-radius:14px;background:#f1fbf8;box-shadow:0 12px 34px rgba(32,110,97,.08);text-align:center}
    .vai-payment-check{display:grid;place-items:center;width:44px;height:44px;margin:0 auto .65rem;border-radius:50%;background:#149e8f;color:#fff;font-size:1.45rem;font-weight:800}
    .vai-payment-success h2{margin:.15rem 0 .35rem;color:#0a514a;font-size:1.35rem}.vai-payment-success p{margin:0;color:#426b67;line-height:1.5}
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


def _clear_recovery_state() -> None:
    st.session_state.pop("recovery_session", None)
    st.session_state.pop("show_password_reset", None)
    for key in ("token_hash", "type"):
        if key in st.query_params:
            del st.query_params[key]


def _render_new_password(client: SupabaseAccessClient) -> bool:
    token_hash = st.query_params.get("token_hash")
    recovery_type = st.query_params.get("type")
    if recovery_type != "recovery" and "recovery_session" not in st.session_state:
        return False

    if "recovery_session" not in st.session_state:
        if not token_hash:
            st.error("This password-reset link is incomplete. Please request a new link.")
            return True
        try:
            st.session_state["recovery_session"] = client.verify_recovery_token(token_hash)
            for key in ("token_hash", "type"):
                if key in st.query_params:
                    del st.query_params[key]
        except AccessServiceError:
            st.error("This password-reset link is invalid or has expired. Request a new link.")
            return True

    st.subheader("Set a new password")
    with st.form("new_password_form", enter_to_submit=False):
        password = st.text_input("New password", type="password", key="new_password")
        confirmed = st.text_input("Confirm new password", type="password", key="confirm_new_password")
        submitted = st.form_submit_button("Update password", use_container_width=True)
    if submitted:
        if len(password) < 8:
            st.error("Use a password with at least 8 characters.")
        elif password != confirmed:
            st.error("Passwords do not match.")
        else:
            try:
                client.update_password(st.session_state["recovery_session"], password)
                _clear_recovery_state()
                st.session_state["password_updated"] = True
                st.rerun()
            except AccessServiceError as exc:
                st.error(str(exc))
    return True


def _friendly_reset_error(exc: AccessServiceError) -> str:
    detail = str(exc)
    if "rate limit" in detail.lower():
        return "Too many authentication emails were requested. Please wait before trying again."
    return detail


def _render_checkout_return(client: SupabaseAccessClient) -> bool:
    checkout_result = st.query_params.get("checkout")
    if checkout_result == "cancelled":
        st.info("Checkout was cancelled. You have not been charged.")
        return False
    if checkout_result != "success":
        return False

    session_id = st.query_params.get("session_id")
    if not session_id:
        st.warning("We could not verify the checkout return. Sign in to check your subscription.")
        return False

    try:
        checkout = client.checkout_status(session_id)
    except AccessServiceError:
        st.warning("Payment is being verified. Sign in and refresh your subscription status.")
        return False

    confirmed = (checkout.get("status") == "complete" and
                 checkout.get("payment_status") in {"paid", "no_payment_required"})
    if confirmed:
        st.session_state["checkout_confirmed"] = True
        st.markdown("""
        <section class="vai-payment-success">
          <div class="vai-payment-check">✓</div>
          <h2>Payment successful</h2>
          <p>Your Founding Plan payment is confirmed. Welcome to Vector AlgoAI.</p>
        </section>
        """, unsafe_allow_html=True)
        return True

    st.warning("Stripe is still processing the payment. Please wait a moment and refresh this page.")
    return False


def _render_logged_out(client: SupabaseAccessClient) -> None:
    if _render_new_password(client):
        return

    if st.session_state.pop("password_updated", False):
        st.success("Your password has been updated. You can now sign in.")

    login_tab, signup_tab = st.tabs(["Sign in", "Create account"])
    with login_tab:
        if not st.session_state.get("show_password_reset"):
            with st.form("login_form"):
                email = st.text_input("Email", key="login_email")
                password = st.text_input("Password", type="password", key="login_password")
                submitted = st.form_submit_button("Sign in", use_container_width=True)
            if st.button("Forgot password?", key="show_reset"):
                st.session_state["show_password_reset"] = True
                st.rerun()
            if submitted:
                try:
                    st.session_state["auth_session"] = client.sign_in(email, password)
                    st.rerun()
                except AccessServiceError as exc:
                    st.error(str(exc))
        else:
            st.markdown("#### Reset your password")
            st.caption("Enter the email address used for your Vector AlgoAI account.")
            with st.form("reset_form"):
                email = st.text_input("Account email", key="reset_email")
                submitted = st.form_submit_button("Send reset email", use_container_width=True)
            if st.button("Back to sign in", key="hide_reset"):
                st.session_state["show_password_reset"] = False
                st.rerun()
            if submitted:
                try:
                    client.send_password_reset(email, APP_URL)
                    st.success("If the account exists, a password-reset email has been sent.")
                except AccessServiceError as exc:
                    st.error(_friendly_reset_error(exc))
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


def _render_subscription(client: SupabaseAccessClient, session: AuthSession) -> bool:
    try:
        subscription = client.subscription(session)
    except AccessServiceError:
        st.error("We could not verify your subscription. Strategy Lab remains locked.")
        if st.button("Sign out", use_container_width=True):
            _logout()
        return False
    if subscription.grants_access:
        st.session_state.pop("checkout_url", None)
        st.session_state.pop("checkout_confirmed", None)
        for key in ("checkout", "session_id"):
            if key in st.query_params:
                del st.query_params[key]
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
    if st.session_state.get("checkout_confirmed"):
        st.subheader("Finalizing your Strategy Lab access")
        st.write("Your payment is confirmed. We are waiting for the signed Stripe notification to activate access.")
        if st.button("Continue to Strategy Lab", type="primary", use_container_width=True):
            st.rerun()
        st.caption("This normally takes only a few seconds. You will not be charged again.")
        return False

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
    session = _session()
    _style(authenticated=session is not None)
    try:
        client = _client()
    except AccessConfigurationError:
        st.error("Strategy Lab access is temporarily unavailable.")
        return False
    checkout_confirmed = _render_checkout_return(client)
    if session is None:
        if checkout_confirmed:
            st.info("For security, sign in once to continue to Strategy Lab. Your payment is already confirmed.")
        _render_logged_out(client)
        return False
    return _render_subscription(client, session)
