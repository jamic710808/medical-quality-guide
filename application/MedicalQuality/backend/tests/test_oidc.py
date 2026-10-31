from dataclasses import replace
from urllib.parse import parse_qs, urlparse
import time

import httpx2 as httpx
import pytest
from fastapi.testclient import TestClient
from authlib.integrations.starlette_client import OAuth
from authlib.jose import JsonWebKey, jwt

from medical_quality.db import transaction
from medical_quality.models import Actor


@pytest.mark.parametrize("invalid", [None, "nonce", "audience", "signature", "expired"])
def test_oidc_crypto_and_callback_binding(monkeypatch, invalid):
    import medical_quality.app as module

    config = replace(
        module.settings(),
        mode="production",
        oidc_issuer="https://identity.test",
        oidc_client_id="mq-test",
        oidc_client_secret="synthetic-client-secret",
    )
    monkeypatch.setattr(module, "settings", lambda: config)
    key = JsonWebKey.generate_key("RSA", 2048, options={"kid": "test-key"}, is_private=True)
    other = JsonWebKey.generate_key("RSA", 2048, options={"kid": "test-key"}, is_private=True)
    state = {}

    def transport(request):
        path = request.url.path
        if path.endswith("openid-configuration"):
            return httpx.Response(
                200,
                json={
                    "issuer": "https://identity.test",
                    "authorization_endpoint": "https://identity.test/authorize",
                    "token_endpoint": "https://identity.test/token",
                    "jwks_uri": "https://identity.test/jwks",
                    "id_token_signing_alg_values_supported": ["RS256"],
                    "token_endpoint_auth_methods_supported": ["client_secret_basic"],
                },
            )
        if path == "/jwks":
            return httpx.Response(200, json={"keys": [key.as_dict(is_private=False)]})
        if path == "/token":
            claims = {
                "iss": "https://identity.test",
                "sub": "verified-doctor-subject",
                "aud": "wrong" if invalid == "audience" else "mq-test",
                "nonce": "wrong" if invalid == "nonce" else state["nonce"],
                "iat": int(time.time()),
                "exp": int(time.time()) + (-500 if invalid == "expired" else 120),
            }
            token = jwt.encode(
                {"alg": "RS256", "kid": "test-key"}, claims, other if invalid == "signature" else key
            ).decode()
            return httpx.Response(
                200,
                json={
                    "access_token": "synthetic-token",
                    "token_type": "Bearer",
                    "expires_in": 120,
                    "id_token": token,
                },
            )
        raise AssertionError("Unexpected identity endpoint")

    registry = OAuth()
    registry.register(
        name="hospital",
        client_id="mq-test",
        client_secret="synthetic-client-secret",
        server_metadata_url="https://identity.test/.well-known/openid-configuration",
        client_kwargs={
            "scope": "openid profile",
            "code_challenge_method": "S256",
            "transport": httpx.MockTransport(transport),
        },
    )
    monkeypatch.setattr(module, "oauth", registry)
    with transaction() as db:
        db.get(Actor, "doctor1").oidc_subject = "verified-doctor-subject"
    with TestClient(module.app, base_url="https://testserver") as client:
        start = client.get("/api/v1/auth/login", follow_redirects=False)
        assert start.status_code in {302, 307}, start.text
        params = parse_qs(urlparse(start.headers["location"]).query)
        state["nonce"] = params["nonce"][0]
        assert params["code_challenge_method"] == ["S256"]
        callback = client.get(
            "/api/v1/auth/callback",
            params={"code": "synthetic-code", "state": params["state"][0]},
            follow_redirects=False,
        )
        if invalid:
            assert callback.status_code == 401 and not client.cookies.get("mq_session")
        else:
            assert callback.status_code in {302, 307}, callback.text
            session = client.get("/api/v1/session")
            assert session.status_code == 200
            assert session.json()["actor"]["id"] == "doctor1"
            assert client.get("/api/v1/cases/C004").status_code == 404
