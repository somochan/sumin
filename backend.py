"""Small Flask API for NEXUS Research.

Run with: python backend.py
"""

from __future__ import annotations

import os
import tomllib
from pathlib import Path

from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

OPENALEX_URL = "https://api.openalex.org/works"
ALLOWED_DOMAINS = {
    "Generative AI": "generative artificial intelligence",
    "Cloud Computing": "cloud computing",
    "Cybersecurity": "cybersecurity",
}


def load_supabase_settings() -> tuple[str, str]:
    """Load local settings without exposing a key in API responses."""
    url, key = os.getenv("SUPABASE_URL", ""), os.getenv("SUPABASE_KEY", "")
    secrets_file = Path(__file__).parent / ".streamlit" / "secrets.toml"
    if secrets_file.exists() and (not url or not key):
        settings = tomllib.loads(secrets_file.read_text(encoding="utf-8"))
        url, key = url or settings.get("SUPABASE_URL", ""), key or settings.get("SUPABASE_KEY", "")
    return url, key


def authenticated_user() -> dict | None:
    """Let Supabase Auth validate the caller's access token server-side."""
    url, key = load_supabase_settings()
    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    if not url or not key or not token:
        return None
    try:
        response = requests.get(f"{url}/auth/v1/user", headers={"apikey": key, "Authorization": f"Bearer {token}"}, timeout=10)
        return response.json() if response.ok else None
    except requests.RequestException:
        return None


def is_local_demo_request() -> bool:
    """Allow read-only demo searches only from the local Streamlit process."""
    return (
        request.headers.get("X-NEXUS-DEMO") == "local"
        and request.remote_addr in {"127.0.0.1", "::1"}
    )


def format_work(work: dict) -> dict:
    """Keep only the fields the frontend needs from an OpenAlex work."""
    authors = [
        author.get("author", {}).get("display_name", "Unknown author")
        for author in work.get("authorships", [])[:3]
    ]
    return {
        "id": work.get("id"),
        "title": work.get("title") or "Untitled paper",
        "year": work.get("publication_year"),
        "citations": work.get("cited_by_count", 0),
        "authors": ", ".join(authors) or "Authors unavailable",
        "source": (((work.get("primary_location") or {}).get("source") or {}).get("display_name"))
        or "Source unavailable",
        "url": work.get("doi") or work.get("id"),
        "abstract_available": bool(work.get("abstract_inverted_index")),
    }


@app.get("/api/health")
def health() -> tuple:
    return jsonify({"status": "ok", "service": "NEXUS Research API"}), 200


@app.get("/api/papers")
def get_papers() -> tuple:
    if not authenticated_user() and not is_local_demo_request():
        return jsonify({"error": "Sign in is required to access research data."}), 401
    domain = request.args.get("domain", "Generative AI")
    search = request.args.get("search", "").strip()
    try:
        limit = min(max(int(request.args.get("limit", 10)), 1), 25)
    except ValueError:
        return jsonify({"error": "limit must be a number"}), 400

    if domain not in ALLOWED_DOMAINS:
        return jsonify({"error": f"domain must be one of: {', '.join(ALLOWED_DOMAINS)}"}), 400

    query = search or ALLOWED_DOMAINS[domain]
    try:
        response = requests.get(
            OPENALEX_URL,
            params={"search": query, "per-page": limit, "sort": "cited_by_count:desc"},
            timeout=15,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        return jsonify({"error": "Could not reach OpenAlex", "detail": str(exc)}), 502

    works = response.json().get("results", [])
    return jsonify({"domain": domain, "query": query, "papers": [format_work(work) for work in works]}), 200


if __name__ == "__main__":
    app.run(debug=True, port=5000)
