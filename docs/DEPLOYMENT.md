# Deploying to a real URL

Everything below is honest about one constraint: I can prepare every
config file and give exact steps, but I cannot create a Render/Fly/Vercel
account, click "deploy," or hold credentials on your behalf. This is the
one part of the whole project that needs you to press the actual button.

The Docker build itself has never been run in the sandbox this project was
built in (no Docker available there) - the `docker-build` job added to
`.github/workflows/ci.yml` is the first real verification, since GitHub
Actions runners do have Docker. Push to `main` (or open a PR) and check
that job before trusting the images below.

## Recommended: Render (simplest two-service setup)

Render can build straight from your GitHub repo with no separate registry
step, and has a free tier for both a web service and a static site.

1. Push this repo to GitHub.
2. On [render.com](https://render.com), **New > Web Service**, connect the
   repo, and set:
   - **Root directory**: leave blank (repo root)
   - **Dockerfile path**: `docker/Dockerfile.api`
   - **Environment variables**: `SECRET_KEY` (generate a real random value —
     `python -c "import secrets; print(secrets.token_hex(32))"` — never
     reuse the dev default), `FRONTEND_URL` (fill in after step 3, or
     redeploy once you know it), and optionally the four `SMTP_*` /
     `FROM_EMAIL` variables from `api/email.py` if you want real password-
     reset and message-notification emails to actually send.
   - Render gives this service a URL like `https://clinical-risk-api.onrender.com`.
3. **New > Static Site** for the frontend:
   - **Root directory**: `frontend`
   - **Build command**: `npm install && npm run build`
   - **Publish directory**: `dist`
   - **Environment variable**: `VITE_API_URL` = the backend URL from step 2
     (e.g. `https://clinical-risk-api.onrender.com`) — this is a *build-time*
     variable per Vite convention, so set it before the first build.
4. Go back to the web service from step 2 and set `FRONTEND_URL` to the
   static site's URL, so password-reset emails link to the right place.
5. Free-tier Render web services sleep after inactivity and take ~30s to
   wake on the next request — fine for a portfolio demo, worth knowing
   before a live interview walkthrough.

## Alternative: Fly.io (if you want the Docker images running as-built)

```bash
fly launch --dockerfile docker/Dockerfile.api --name clinical-risk-api
fly secrets set SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
fly deploy

fly launch --dockerfile docker/Dockerfile.frontend --name clinical-risk-frontend \
  --build-arg VITE_API_URL=https://clinical-risk-api.fly.dev
fly deploy
```

## Alternative: Vercel (frontend only, pair with Render/Fly for the API)

```bash
cd frontend
vercel --build-env VITE_API_URL=https://your-backend-url
```

## Local, full-stack, via Docker Compose (once Docker is available to you)

```bash
cd docker
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))") \
  docker compose up --build
# API on :8000, frontend on :8080
```

## Before calling any of these "done"

- [ ] `SECRET_KEY` is a real random value, not the dev default
      (`api/auth.py` warns about this loudly on purpose)
- [ ] `docker-build` CI job is green on GitHub Actions (real verification,
      not assumed)
- [ ] An admin account exists — run `scripts/seed_admin.py` against
      whatever database URL the deployed backend is using, or add a
      one-off management endpoint/CLI hook for your platform of choice
- [ ] SMTP variables are set if you want real emails, otherwise password
      reset links will only ever appear in the backend's logs
- [ ] CORS in `api/main.py` is currently `allow_origins=["*"]` — fine for
      a portfolio demo, tighten to your actual frontend origin before
      calling this production-ready
