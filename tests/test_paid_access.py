import unittest
import sys
import types

# The production dependency is declared in requirements.txt. Unit tests inject
# their own HTTP transport, so they do not require requests to be installed.
sys.modules.setdefault("requests", types.SimpleNamespace(request=None))

from core.auth import (
    AccessConfigurationError,
    AccessServiceError,
    AuthSession,
    Subscription,
    SupabaseAccessClient,
)


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self.payload = payload if payload is not None else {}

    def json(self):
        return self.payload


class FakeHttp:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return self.responses.pop(0)


class PaidAccessTests(unittest.TestCase):
    def test_missing_configuration_fails_closed(self):
        with self.assertRaises(AccessConfigurationError):
            SupabaseAccessClient("", "")

    def test_active_and_trialing_grant_access_only(self):
        self.assertTrue(Subscription(status="active").grants_access)
        self.assertTrue(Subscription(status="trialing").grants_access)
        for status in ("none", "incomplete", "past_due", "paused", "canceled", "unpaid"):
            self.assertFalse(Subscription(status=status).grants_access)

    def test_sign_in_builds_isolated_session(self):
        http = FakeHttp([FakeResponse(payload={
            "access_token": "access", "refresh_token": "refresh", "expires_at": 123,
            "user": {"id": "user-1", "email": "member@example.com"},
        })])
        client = SupabaseAccessClient("https://example.supabase.co", "public-key", http)
        session = client.sign_in("Member@Example.com", "password")
        self.assertEqual(session.user_id, "user-1")
        self.assertEqual(http.calls[0][2]["json"]["email"], "member@example.com")

    def test_subscription_request_uses_user_bearer_and_filter(self):
        http = FakeHttp([FakeResponse(payload=[{"status": "active", "price_id": "price_1"}])])
        client = SupabaseAccessClient("https://example.supabase.co", "public-key", http)
        session = AuthSession("private-user-token", "refresh", "user-7", "x@example.com")
        subscription = client.subscription(session)
        call = http.calls[0]
        self.assertTrue(subscription.grants_access)
        self.assertEqual(call[2]["headers"]["Authorization"], "Bearer private-user-token")
        self.assertEqual(call[2]["params"]["user_id"], "eq.user-7")

    def test_missing_subscription_is_locked(self):
        client = SupabaseAccessClient(
            "https://example.supabase.co", "public-key", FakeHttp([FakeResponse(payload=[])]))
        subscription = client.subscription(AuthSession("token", "refresh", "user", "x@example.com"))
        self.assertFalse(subscription.grants_access)

    def test_service_errors_do_not_grant_access(self):
        client = SupabaseAccessClient(
            "https://example.supabase.co", "public-key",
            FakeHttp([FakeResponse(status_code=401, payload={"message": "Invalid login"})]))
        with self.assertRaises(AccessServiceError):
            client.sign_in("x@example.com", "wrong")


if __name__ == "__main__":
    unittest.main()
