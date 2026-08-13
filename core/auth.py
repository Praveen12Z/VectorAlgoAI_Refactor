"""Supabase authentication and subscription access for VectorAlgoAI."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional
from urllib.parse import quote

import requests

ACTIVE_SUBSCRIPTION_STATUSES = frozenset({"active", "trialing"})
REQUEST_TIMEOUT_SECONDS = 15


class AccessConfigurationError(RuntimeError):
    pass


class AccessServiceError(RuntimeError):
    pass


@dataclass(frozen=True)
class AuthSession:
    access_token: str
    refresh_token: str
    user_id: str
    email: str
    expires_at: Optional[int] = None

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "AuthSession":
        user = payload.get("user") or {}
        return cls(str(payload["access_token"]), str(payload.get("refresh_token", "")),
                   str(user["id"]), str(user.get("email", "")), payload.get("expires_at"))


@dataclass(frozen=True)
class Subscription:
    status: str = "none"
    price_id: Optional[str] = None
    current_period_end: Optional[str] = None
    cancel_at_period_end: bool = False

    @property
    def grants_access(self) -> bool:
        return self.status in ACTIVE_SUBSCRIPTION_STATUSES


class SupabaseAccessClient:
    """Small REST client using only Supabase's public publishable key."""

    def __init__(self, url: str, anon_key: str, http: Any = requests):
        self.url = (url or "").strip().rstrip("/")
        self.anon_key = (anon_key or "").strip()
        self.http = http
        if not self.url or not self.anon_key:
            raise AccessConfigurationError("Supabase URL and publishable key must be configured.")

    @property
    def public_headers(self) -> dict[str, str]:
        return {"apikey": self.anon_key, "Content-Type": "application/json"}

    def _request(self, method: str, endpoint: str, **kwargs: Any) -> Any:
        kwargs.setdefault("timeout", REQUEST_TIMEOUT_SECONDS)
        response = self.http.request(method, endpoint, **kwargs)
        if response.status_code >= 400:
            try:
                body = response.json()
                detail = body.get("msg") or body.get("message") or body.get("error_description")
            except (ValueError, AttributeError):
                detail = None
            raise AccessServiceError(detail or "The access service is unavailable.")
        return response

    def sign_up(self, email: str, password: str) -> bool:
        response = self._request("POST", f"{self.url}/auth/v1/signup",
                                 headers=self.public_headers,
                                 json={"email": email.strip().lower(), "password": password})
        payload = response.json()
        return bool(payload.get("session") or payload.get("access_token"))

    def sign_in(self, email: str, password: str) -> AuthSession:
        response = self._request("POST", f"{self.url}/auth/v1/token?grant_type=password",
                                 headers=self.public_headers,
                                 json={"email": email.strip().lower(), "password": password})
        return AuthSession.from_payload(response.json())

    def refresh(self, refresh_token: str) -> AuthSession:
        response = self._request("POST", f"{self.url}/auth/v1/token?grant_type=refresh_token",
                                 headers=self.public_headers, json={"refresh_token": refresh_token})
        return AuthSession.from_payload(response.json())

    def send_password_reset(self, email: str, redirect_to: str) -> None:
        redirect = quote(redirect_to, safe=":/")
        self._request("POST", f"{self.url}/auth/v1/recover?redirect_to={redirect}",
                      headers=self.public_headers, json={"email": email.strip().lower()})

    def verify_recovery_token(self, token_hash: str) -> AuthSession:
        response = self._request(
            "POST", f"{self.url}/auth/v1/verify", headers=self.public_headers,
            json={"token_hash": token_hash, "type": "recovery"})
        return AuthSession.from_payload(response.json())

    def update_password(self, session: AuthSession, password: str) -> None:
        self._request(
            "PUT", f"{self.url}/auth/v1/user",
            headers={**self.public_headers, "Authorization": f"Bearer {session.access_token}"},
            json={"password": password})

    def subscription(self, session: AuthSession) -> Subscription:
        response = self._request(
            "GET", f"{self.url}/rest/v1/subscriptions",
            headers={**self.public_headers, "Authorization": f"Bearer {session.access_token}"},
            params={"select": "status,price_id,current_period_end,cancel_at_period_end",
                    "user_id": f"eq.{session.user_id}", "limit": "1"})
        rows = response.json()
        if not rows:
            return Subscription()
        row = rows[0]
        return Subscription(str(row.get("status") or "none").lower(), row.get("price_id"),
                            row.get("current_period_end"), bool(row.get("cancel_at_period_end", False)))

    def invoke(self, function_name: str, session: AuthSession) -> str:
        response = self._request(
            "POST", f"{self.url}/functions/v1/{function_name}",
            headers={**self.public_headers, "Authorization": f"Bearer {session.access_token}"}, json={})
        url = response.json().get("url")
        if not url:
            raise AccessServiceError("Billing did not return a secure redirect URL.")
        return str(url)

    def checkout_status(self, session_id: str) -> Mapping[str, Any]:
        response = self._request(
            "POST", f"{self.url}/functions/v1/checkout-status",
            headers=self.public_headers, json={"session_id": session_id})
        payload = response.json()
        if not isinstance(payload, Mapping):
            raise AccessServiceError("Payment confirmation is temporarily unavailable.")
        return payload
