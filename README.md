# Lab Olympics 2026

A Streamlit app for scoring the lab olympics — referee panel for entering results
per group, leaderboard for live standings, records, and best individual results.

## Run locally

```bash
pip install -r requirements.txt
streamlit run olympics_app.py
```

With no secrets configured, scores persist to a local `scores.json` next to the app.

## Deploy to Streamlit Community Cloud

The Community Cloud filesystem is ephemeral — anything written to disk is lost on
restart or redeploy. The app uses a GitHub Gist as a persistent JSON blob instead.

### 1. Create a secret gist for scores

1. Go to <https://gist.github.com>.
2. Filename: `scores.json`. Content: `{}` (an empty JSON object is enough).
3. Click **Create secret gist**.
4. From the URL `https://gist.github.com/<user>/<gist_id>`, copy the `<gist_id>`.

Secret gists are not listed publicly, but anyone with the URL can read them — that's
fine for scores, but don't reuse the gist for anything sensitive.

### 2. Create a GitHub personal access token

Either form works:

- **Classic PAT** (simpler): <https://github.com/settings/tokens> → *Generate new
  token (classic)* → scope: `gist` only. No other scopes.
- **Fine-grained PAT** (scoped to the one gist): <https://github.com/settings/personal-access-tokens>
  → grant *Gists: Read and write*.

Copy the token — you won't see it again.

### 3. Deploy on Streamlit Community Cloud

1. Push this repo to GitHub.
2. Go to <https://share.streamlit.io>, sign in, **New app** → pick the repo /
   branch, main file `olympics_app.py`.
3. Before the first deploy, open **Advanced settings → Secrets** and paste:

   ```toml
   [github]
   token = "ghp_yourTokenHere"
   gist_id = "yourGistIdHere"
   filename = "scores.json"
   ```

4. Deploy. After it boots, save a score from the Referee tab and confirm the
   gist updates.

### Updating secrets later

App page → **Manage app** (bottom right) → **Settings** → **Secrets**. Edits
trigger a restart automatically.

## Local development with the gist backend

Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and fill in the
same values. `secrets.toml` is gitignored. Omit the `[github]` block to fall back to
the local `scores.json` file.
