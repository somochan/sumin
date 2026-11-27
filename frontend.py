"""NEXUS Research Streamlit interface. Run: python -m streamlit run frontend.py"""
from __future__ import annotations

import html
import os

import pandas as pd
import requests
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError
from supabase import Client, create_client

API_URL = os.getenv(
    "NEXUS_API_URL",
    "https://sumin1.vercel.app"
).rstrip("/")
THEMES = {
    "Nexus Dark": ("#050609", "#101722", "#eaf6ff", "#90a4b8", "#00f5ff", "#2563eb"),
    "Midnight Blue": ("#071426", "#0d243d", "#edf7ff", "#9bb6cc", "#38bdf8", "#3b82f6"),
    "Light Modern": ("#f5f7fb", "#ffffff", "#172033", "#5e6f82", "#007c91", "#2563eb"),
}
st.set_page_config(page_title="NEXUS Research", page_icon="◈", layout="wide", initial_sidebar_state="collapsed")


def setting(name: str) -> str:
    try:
        return str(st.secrets.get(name, os.getenv(name, "")))
    except StreamlitSecretNotFoundError:
        return os.getenv(name, "")


if "theme" not in st.session_state:
    st.session_state.theme = "Nexus Dark"
bg, surface, text, muted, cyan, blue = THEMES[st.session_state.theme]
st.markdown(f"""<style>
:root{{--bg:{bg};--surface:{surface};--text:{text};--muted:{muted};--cyan:{cyan};--blue:{blue}}}
.stApp{{background:radial-gradient(circle at 8% 8%,color-mix(in srgb,var(--blue) 17%,transparent),transparent 32%),radial-gradient(circle at 92% 85%,color-mix(in srgb,var(--cyan) 11%,transparent),transparent 28%),var(--bg);color:var(--text)}}
[data-testid="stHeader"]{{background:transparent}} #MainMenu,footer{{visibility:hidden}} .block-container{{max-width:1180px;padding-top:1.2rem}}
.nav{{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid color-mix(in srgb,var(--cyan) 20%,transparent);padding:.5rem 0 1.15rem}}.brand{{font-weight:800;letter-spacing:.16em;color:var(--text)}}.brand b,.eyebrow,.accent{{color:var(--cyan)}}.navsmall,.meta{{color:var(--muted);font-size:.88rem}}.eyebrow{{font-weight:700;letter-spacing:.14em;font-size:.76rem}}
.title{{font-size:clamp(3rem,7vw,5.7rem);line-height:1.02;letter-spacing:-.06em;font-weight:800;margin:.7rem 0 1rem;color:var(--text)}}.title span{{color:var(--cyan);text-shadow:0 0 27px color-mix(in srgb,var(--cyan) 60%,transparent)}}.copy{{color:var(--muted);font-size:1.08rem;line-height:1.7;max-width:32rem}}.chips{{display:flex;gap:.5rem;flex-wrap:wrap;margin-top:1.5rem}}.chip{{padding:.4rem .7rem;border-radius:999px;border:1px solid color-mix(in srgb,var(--cyan) 22%,transparent);color:var(--text);font-size:.8rem}}
.auth{{background:color-mix(in srgb,var(--surface) 94%,transparent);border:1px solid color-mix(in srgb,var(--cyan) 38%,transparent);box-shadow:0 0 38px color-mix(in srgb,var(--cyan) 12%,transparent);border-radius:20px;padding:1.45rem}}.auth h2,.card h3{{color:var(--text);margin:0}}.auth p{{color:var(--muted)}}
.paper{{background:var(--surface);border:1px solid color-mix(in srgb,var(--cyan) 20%,transparent);border-radius:14px;padding:1.1rem 1.25rem;margin:.7rem 0}}.paper h3{{color:var(--text);margin:0 0 .45rem}}.tag{{color:var(--cyan);font-weight:700}}
.stButton button,.stLinkButton a{{background:var(--blue)!important;color:white!important;border:1px solid color-mix(in srgb,var(--cyan) 45%,transparent)!important;border-radius:9px!important;font-weight:650!important}}button[data-baseweb="tab"]{{color:var(--muted)}}button[data-baseweb="tab"][aria-selected="true"]{{color:var(--cyan)}}
@media(max-width:700px){{.block-container{{padding-left:1rem;padding-right:1rem}}}}
</style>""", unsafe_allow_html=True)


def get_auth() -> tuple[Client | None, str]:
    url, key = setting("SUPABASE_URL"), setting("SUPABASE_KEY")
    if not url or not key:
        return None, ""
    if "supabase_client" not in st.session_state:
        st.session_state.supabase_client = create_client(url, key)
    return st.session_state.supabase_client, setting("AUTH_REDIRECT_URL") or "http://localhost:8501"


def save_session(auth_response: object) -> None:
    """Store only this visitor's short-lived session data."""
    session = getattr(auth_response, "session", None)
    user = getattr(auth_response, "user", None)
    if not session or not user:
        raise ValueError("Supabase did not return a valid sign-in session.")
    st.session_state.user_email = user.email
    st.session_state.access_token = session.access_token


def nav(signed_in: bool = False) -> None:
    a, b = st.columns([5, 1])
    with a:
        st.markdown("<div class='nav'><div class='brand'><b>◈</b> NEXUS RESEARCH</div><div class='navsmall'>Research intelligence, simplified.</div></div>", unsafe_allow_html=True)
    with b:
        with st.popover("◐ Theme"):
            choice = st.radio("Interface theme", list(THEMES), index=list(THEMES).index(st.session_state.theme))
            if choice != st.session_state.theme:
                st.session_state.theme = choice
                st.rerun()
        if signed_in and st.button("Sign out", use_container_width=True):
            client, _ = get_auth()
            if client:
                client.auth.sign_out()
            st.session_state.pop("user_email", None)
            st.session_state.pop("access_token", None)
            st.session_state.pop("demo_mode", None)
            st.rerun()


def social(client: Client | None, provider: str, label: str, redirect: str) -> None:
    if client is None:
        if st.button(label, use_container_width=True, key=f"demo_{provider}"):
            st.info("Connect Supabase in `.streamlit/secrets.toml` to use real Google or GitHub sign-in.")
        return
    try:
        result = client.auth.sign_in_with_oauth({"provider": provider, "options": {"redirect_to": redirect}})
        st.link_button(label, result.url, use_container_width=True)
    except Exception:
        st.button(label, disabled=True, use_container_width=True)


def landing(client: Client | None, redirect: str) -> None:
    nav()
    left, right = st.columns([1.2, .8], gap="large")
    with left:
        st.markdown("<div style='padding:4rem 0 2rem'><div class='eyebrow'>RESEARCH, CONNECTED</div><div class='title'>Find the signal.<br/><span>Build the future.</span></div><p class='copy'>NEXUS brings Generative AI, Cloud Computing, and Cybersecurity research into one focused workspace.</p><div class='chips'><span class='chip'>◈ Live research data</span><span class='chip'>⌁ AI-ready workflows</span><span class='chip'>◌ Private workspace</span></div></div>", unsafe_allow_html=True)
    with right:
        st.markdown("<div style='height:2rem'></div><div class='auth'><h2>◈ Welcome to NEXUS</h2><p>Securely access your research workspace.</p><p class='meta'>✦ Analyze real papers &nbsp; · &nbsp; ⌁ Keep your work organized</p></div>", unsafe_allow_html=True)
        signin, signup = st.tabs(["Sign in", "Create account"])
        with signin:
            with st.form("login"):
                email = st.text_input("Email", placeholder="you@example.com")
                password = st.text_input("Password", type="password")
                sent = st.form_submit_button("Sign in to NEXUS", use_container_width=True)
            if sent:
                if client is None:
                    st.warning("Real sign-in needs your Supabase publishable key. Use **Explore demo workspace** below to test the app now.")
                    return
                try:
                    session = client.auth.sign_in_with_password({"email": email, "password": password})
                    save_session(session)
                    st.rerun()
                except Exception as exc:
                    st.error(f"Sign-in failed: {exc}")
        with signup:
            with st.form("signup"):
                email = st.text_input("Email", placeholder="you@example.com", key="new_email")
                password = st.text_input("Create password", type="password", key="new_password")
                sent = st.form_submit_button("Create free account", use_container_width=True)
            if sent:
                if client is None:
                    st.warning("Account creation will activate as soon as Supabase is configured. Use the demo workspace while you set it up.")
                    return
                try:
                    client.auth.sign_up({"email": email, "password": password, "options": {"email_redirect_to": redirect}})
                    st.success("Account created. Check your email to confirm it.")
                except Exception as exc:
                    st.error(f"Account creation failed: {exc}")
        st.markdown("<p class='meta' style='text-align:center'>or continue with</p>", unsafe_allow_html=True)
        g, h = st.columns(2)
        with g: social(client, "google", "G  Google", redirect)
        with h: social(client, "github", "◉  GitHub", redirect)
        st.divider()
        if st.button("Explore demo workspace", use_container_width=True):
            st.session_state.user_email = "demo@nexus.local"
            st.session_state.demo_mode = True
            st.rerun()
        if client is None:
            st.caption("Demo mode lets you test the complete interface. It does not create a real account.")


def callback(client: Client | None) -> None:
    if client and (code := st.query_params.get("code")):
        try:
            session = client.auth.exchange_code_for_session({"auth_code": code})
            save_session(session)
            st.query_params.clear(); st.rerun()
        except Exception as exc:
            st.error(f"Social sign-in could not finish: {exc}")


def save_current_papers(client: Client | None, papers: list[dict], domain: str) -> None:
    """Save this user's current research results through Supabase RLS."""
    if client is None or st.session_state.get("demo_mode"):
        st.warning("Sign in with a real Supabase account before saving papers.")
        return
    try:
        user = client.auth.get_user().user
        records = [
            {
                "user_id": user.id,
                "openalex_id": paper["id"],
                "title": paper["title"],
                "authors": paper["authors"],
                "publication_year": paper["year"],
                "citations": paper["citations"],
                "source": paper["source"],
                "paper_url": paper["url"],
                "domain": domain,
            }
            for paper in papers
        ]
        client.table("saved_papers").upsert(records, on_conflict="user_id,openalex_id").execute()
        st.success(f"Saved {len(records)} papers to your private NEXUS library.")
    except Exception as exc:
        st.error(f"Could not save papers. Run database/saved_papers.sql in Supabase first. Details: {exc}")


def dashboard() -> None:
    nav(True)
    with st.sidebar:
        st.markdown("### Research controls")
        domain = st.selectbox("Research domain", ["Generative AI", "Cloud Computing", "Cybersecurity"])
        search = st.text_input("Focus topic", placeholder="e.g. large language models")
        limit = st.slider("Results", 5, 25, 10, 5)
        load = st.button("Scan research", use_container_width=True)
    demo_note = " <span class='accent'>DEMO MODE</span>" if st.session_state.get("demo_mode") else ""
    st.markdown(f"<div style='padding:2.2rem 0 1rem'><div class='eyebrow'>● WORKSPACE ACTIVE{demo_note}</div><h1>Welcome back, {html.escape(st.session_state.user_email)}</h1><p class='copy'>Explore live research across the domains shaping modern technology.</p></div>", unsafe_allow_html=True)
    if "papers" not in st.session_state: st.session_state.papers = []
    if load:
        try:
            headers = {"Authorization": f"Bearer {st.session_state.get('access_token', '')}"}
            if st.session_state.get("demo_mode"):
                headers["X-NEXUS-DEMO"] = "local"
            response = requests.get(f"{API_URL}/api/papers", params={"domain": domain, "search": search, "limit": limit}, headers=headers, timeout=20)
            response.raise_for_status()
            data = response.json()
            st.session_state.papers, st.session_state.query = data["papers"], data["query"]
        except (requests.RequestException, KeyError) as exc: st.error(f"The research API is unavailable: {exc}")
    papers = st.session_state.papers
    if not papers:
        st.info("Open the sidebar and select **Scan research** to load live OpenAlex papers."); return
    a, b, c = st.columns(3); a.metric("Papers loaded", len(papers)); b.metric("Combined citations", f"{sum(p['citations'] for p in papers):,}"); c.metric("Domain", domain)
    if st.button("✦ Save these results to my library", use_container_width=True):
        save_current_papers(client, papers, domain)
    for p in papers:
        st.markdown(f"<div class='paper'><h3>{html.escape(p['title'])}</h3><div class='meta'>{html.escape(p['authors'])} · {p['year'] or 'Year unknown'} · {html.escape(p['source'])}</div><p><span class='tag'>{p['citations']:,} citations</span> · Abstract {'available' if p['abstract_available'] else 'not indexed'}</p><a href='{html.escape(p['url'], quote=True)}' target='_blank'>Open paper ↗</a></div>", unsafe_allow_html=True)
    st.download_button("Download current results as CSV", pd.DataFrame(papers).to_csv(index=False), "nexus_papers.csv", "text/csv")


client, redirect_url = get_auth(); callback(client)
if "user_email" not in st.session_state:
    landing(client, redirect_url); st.stop()
dashboard()
