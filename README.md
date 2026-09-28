# Clinical Risk Prediction Platform

A reusable, leakage-safe ML pipeline for tabular clinical risk prediction —
one shared codebase, config-driven across three disease domains (cardiovascular,
breast cancer, diabetes) — with calibration, explainability, and a deployed
FastAPI + React production system on top.

**Status:** Phases 0–8 complete. Full ML research pipeline, full production
system (auth, roles, messaging, password reset), full frontend (with code
splitting and a real test suite), and deployment-ready configs with a
step-by-step guide (`docs/DEPLOYMENT.md`) for Render, Fly.io, Vercel, or
local Docker Compose. **Not yet done:** an actual live URL — that step
needs your own hosting account, which I can't create on your behalf. See
`reports/technical-report.md` for full, real results (including two more
real bugs caught along the way: a passlib/bcrypt incompatibility and a
Vitest/Vite version conflict) and `reports/technical-report-simple.md` for
a plain-English walkthrough — nothing in either is illustrative.

## Get it running, end to end

```bash
# Backend
pip install -r requirements.txt
python -m src.registry.train_production_models
python -m scripts.seed_admin --email admin@example.com --name "Admin User"
uvicorn api.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
# open http://localhost:5173
```

Run the test suites any time with `pytest tests/ -q` (backend) and
`cd frontend && npm test` (frontend). See `docs/DEPLOYMENT.md` when you're
ready to put this on a real URL.

## Headline result so far

Trained only on Cleveland Clinic data, every model's discrimination degrades
substantially when evaluated on three other institutions' patients (ROC-AUC
0.95 within-site → 0.67–0.78 cross-site; calibration degrades even more
sharply). This isn't a footnote — it's the central, real finding of the
primary study, and it's the kind of "does this generalize past the hospital
it was trained on" question that matters in actual clinical ML deployment.

## Why this project is structured the way it is

- **One pipeline, three diseases** (`src/pipeline/` is disease-agnostic;
  `src/diseases/<name>/` holds only config and schema) — not three one-off
  scripts. This is a deliberate software-engineering decision, not just an
  ML one.
- **Leakage-safe by construction**: every statistical transform (imputation,
  scaling, encoding, calibration) lives inside an sklearn `Pipeline` fit only
  on training folds — verified by an explicit test in `tests/test_pipeline.py`,
  not just asserted in prose.
- **No accuracy-only evaluation**: ROC-AUC/PR-AUC + calibration (Brier score,
  Platt vs. isotonic) + bootstrap confidence intervals + SHAP explainability
  + subgroup reporting (with explicit small-sample caveats where relevant),
  on every model, every disease.

## Repo layout

```
src/pipeline/       shared preprocessing, models, evaluation, tuning
src/diseases/<x>/   per-disease schema + config only
tests/               pytest — leakage-safety and pipeline correctness checks
reports/             real experiment output: CSVs, figures, technical report
api/, frontend/      production system - both fully built
```

## Running it

```bash
pip install -r requirements.txt                       # core - works everywhere
python -m src.diseases.cardio.run_experiment           # Phase 1: model comparison + cross-site test
python -m src.diseases.cardio.run_explainability        # Phase 2: calibration + SHAP
python -m src.diseases.breast_cancer.run_experiment      # Phase 4: same pipeline, second disease
pytest tests/ -q                                         # verify leakage-safety + reusability properties hold

# Phase 3 (FT-Transformer) needs torch, kept OPTIONAL and separate on purpose:
pip install -r requirements-modern-tabular.txt
python -m src.diseases.cardio.run_modern_tabular
```

**Note for Intel Mac users:** PyTorch dropped Intel macOS support after
version 2.2.2, and 2.2.2 doesn't support Python 3.13+. If `pip install -r
requirements-modern-tabular.txt` fails for you, see the comments at the top
of that file — everything except Phase 3 works regardless, and `pytest`
will report the FT-Transformer test as *skipped*, not failed, when torch
isn't available.

Data provenance: `data/raw/SOURCE.md`.

## License

Code: MIT (add LICENSE file before publishing). Data: CC BY 4.0 per UCI
Heart Disease dataset terms — see `data/raw/SOURCE.md`.
