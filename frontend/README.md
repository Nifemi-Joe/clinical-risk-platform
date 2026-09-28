# Frontend

React + TypeScript + Tailwind. Real auth (JWT), real role-based views
(patient / doctor / admin), real doctor-patient messaging, real charts of
real experiment data — nothing here is a mockup.

## Run it

```bash
npm install
npm run dev
```

Requires the backend running on `http://localhost:8000` (see the main
README) — `vite.config.ts` proxies `/api/*` to it.

## Pages

- `/` — landing page, real cross-site generalization chart as the hero
- `/login`, `/register` — real auth, patients pick their doctor at signup
- `/dashboard` — role-aware: prediction forms + history + messaging
  (patient), patient list + history + messaging (doctor), user management
  (admin)
- `/reports` — live from `GET /reports/summary`, the same CSVs documented
  in `reports/technical-report.md`
- `/data` — honest dataset provenance + the improvement roadmap
- `/documentation` — architecture, auth, endpoints

## Design system

See the design plan in the project conversation history / `index.css` +
`tailwind.config.js` for the token system: clinical teal + clay-red
(reserved for risk states only) on a cool paper background, Newsreader +
IBM Plex Sans/Mono typography.

## Known gaps

- No code-splitting yet — the production bundle is ~594 kB (172 kB
  gzipped), mostly recharts. Fine for a portfolio demo, worth addressing
  with `React.lazy()` before real traffic.
- No automated frontend tests (Vitest/Playwright) yet — verified manually
  end-to-end through the real dev-server proxy against the real backend
  (registration → login → prediction → messaging → reports), documented in
  `reports/technical-report.md`, but not codified as a repeatable test suite.
