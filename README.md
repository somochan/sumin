# NEXUS Research

A simple local research-paper explorer for Generative AI, Cloud Computing, and Cybersecurity. It uses the free OpenAlex API and does not need an API key.

## Setup

1. Install Python 3.10 or newer.
2. Open PowerShell in this folder and create a virtual environment:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. Start the backend in one terminal:

   ```powershell
   python backend.py
   ```

4. Start the frontend in a second terminal:

   ```powershell
   python -m streamlit run frontend.py
   ```

Streamlit will open the interface in your browser. The frontend calls the local backend, which fetches live paper metadata from OpenAlex.

## Enable sign-in with Supabase

1. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`.
2. In Supabase Dashboard → **Project Settings → API**, copy your project URL and **Publishable key** (or legacy `anon` key) into that file. Never use a `service_role` key.
3. In Supabase Dashboard → **Authentication → URL Configuration**, set the Site URL and add `http://localhost:8501` as a redirect URL.
4. Email/password auth is enabled by default. In **Authentication → Providers**, configure Google and GitHub with their OAuth client IDs and secrets, then enable both providers.

The app shows the authentication screen until the user signs in. The theme picker appears in the sidebar and includes dark, blue, and light modes.

## Current scope

- Live search in the three NEXUS domains
- Paper metadata, citation counts, source links, and CSV download
- Dark cyberpunk Streamlit UI

Next additions can include saved CSV datasets, cleaning, analysis charts, Ollama summaries, and Power BI-ready exports.
