# Technical Report — Cardiovascular Disease Risk Prediction (Primary Study)

Status: Phases 0–2 complete. Phase 3 (TabPFN/FT-Transformer) and the diabetes/
breast-cancer replications are next. All numbers below are from actual runs
against the real UCI Heart Disease data — none are illustrative or invented.

## Data

Official source: Janosi, Steinbrunn, Pfisterer & Detrano (1988), UCI Machine
Learning Repository, DOI 10.24432/C52P4X, CC BY 4.0. Four sites: Cleveland
(n=303, primary/training site — most complete), Hungarian (n=294), Switzerland
(n=123), VA Long Beach (n=200). Binary target: presence (num>0) vs. absence
(num==0) of heart disease.

### Missingness is structural, not random, across sites

| site | trestbps | chol | fbs | ca | thal |
|---|---|---|---|---|---|
| cleveland | 0.0% | 0.0% | 0.0% | 1.3% | 0.7% |
| hungarian | 0.3% | 7.8% | 2.7% | 99.0% | 90.5% |
| switzerland | 1.6% | 0.0% | 61.0% | 95.9% | 42.3% |
| va | 28.0% | 3.5% | 3.5% | 99.0% | 83.0% |

This confirms the Stage-2 dataset review: `ca` and `thal` — which turn out to
be the two most important SHAP features (below) — are almost entirely absent
outside Cleveland. Any pooled or cross-site model leans heavily on features
that don't exist in the other three sites' raw data, which is one likely
driver of the generalization gap reported next.

## Within-site results (Cleveland, held-out 20% test set, n=61)

Stratified train/test split, RandomizedSearchCV hyperparameter tuning on the
training split (5-fold stratified CV), evaluated once on the untouched test
split. 95% bootstrap CI on ROC-AUC (1,000 resamples).

| model | ROC-AUC | 95% CI | PR-AUC | Brier | Sensitivity | Specificity |
|---|---|---|---|---|---|---|
| logistic_regression | 0.961 | [0.898, 0.999] | 0.947 | 0.087 | 0.929 | 0.848 |
| svm_rbf | 0.955 | [0.884, 0.997] | 0.928 | 0.089 | 0.929 | 0.848 |
| logistic_regression_l1 | 0.953 | [0.889, 0.995] | 0.934 | 0.087 | 0.893 | 0.818 |
| random_forest | 0.952 | [0.895, 0.990] | 0.943 | 0.105 | 0.857 | 0.848 |
| lightgbm | 0.947 | [0.882, 0.988] | 0.945 | 0.109 | 0.893 | 0.879 |
| xgboost | 0.946 | [0.883, 0.989] | 0.943 | 0.113 | 0.893 | 0.879 |
| mlp | 0.922 | [0.841, 0.985] | 0.916 | 0.148 | 0.893 | 0.848 |
| decision_tree | 0.871 | [0.769, 0.954] | 0.809 | 0.133 | 0.857 | 0.879 |
| majority_baseline | 0.500 | [0.500, 0.500] | 0.459 | 0.459 | 0.000 | 1.000 |

**Reading this honestly:** every non-trivial model beats the majority
baseline by a wide margin (sanity check passes). The top five models' CIs
overlap heavily — logistic regression's point estimate is highest, but this
dataset (n=61 test rows) does not have the statistical power to declare a
single winner on discrimination alone. This is exactly why point-estimate
ranking was flagged as insufficient in the original project methodology.

## Cross-site generalization (train on Cleveland only, test on other sites, zero refitting)

| model | test site | n | ROC-AUC | PR-AUC | Brier |
|---|---|---|---|---|---|
| logistic_regression | hungarian | 294 | 0.887 | 0.854 | 0.129 |
| logistic_regression | switzerland | 123 | 0.737 | 0.968 | 0.406 |
| logistic_regression | va | 200 | 0.680 | 0.853 | 0.344 |
| random_forest | hungarian | 294 | 0.900 | 0.857 | 0.143 |
| random_forest | switzerland | 123 | 0.779 | 0.981 | 0.296 |
| random_forest | va | 200 | 0.723 | 0.869 | 0.288 |
| xgboost | hungarian | 294 | 0.845 | 0.778 | 0.156 |
| xgboost | switzerland | 123 | 0.751 | 0.975 | 0.376 |
| xgboost | va | 200 | 0.671 | 0.838 | 0.452 |

**This is the headline finding of the primary study.** Every model loses
substantial discrimination when moved to a genuinely independent site — ROC-AUC
drops from ~0.95 within-site to as low as 0.67–0.78 on VA and Switzerland.
Brier scores worsen even more sharply (e.g. logistic regression: 0.087 →
0.406 on Switzerland), meaning predicted probabilities become materially
unreliable off-site even where rank-ordering (AUC) partially holds up. Random
Forest generalizes best of the three tested here, but still degrades badly.
This is a real, non-trivial result: **a model validated only within one
hospital's data should not be assumed to transfer to another institution's
patients** — a directly job-relevant finding about deployment risk, not just
an academic footnote. Likely contributors: the missingness pattern above
(models leaning on `ca`/`thal`, which barely exist in the other sites) and
the large prevalence shift (Cleveland ~46% vs. Switzerland 93.5% vs. VA
74.5% disease prevalence).

## Calibration (Random Forest, Cleveland held-out test)

| variant | Brier score |
|---|---|
| uncalibrated | 0.102 |
| Platt (sigmoid) | 0.095 |
| isotonic | 0.092 |

Both calibration methods improve on the raw model, isotonic slightly more so
— consistent with general expectations for tree ensembles, which tend to
produce under-confident probabilities near the extremes. See
`reports/figures/calibration_comparison.png`.

## Explainability (SHAP, Random Forest)

Top features by mean |SHAP| on the held-out test set: `thal` (fixed defect
category), `ca`, `cp` (asymptomatic chest pain), `thal` (reversible defect
category), `oldpeak`, `thalach`. See `reports/figures/shap_summary_cardio_rf.png`
and `reports/cardio_shap_feature_importance.csv` for the full ranking.

**Caveat that must travel with this result:** `ca` and `thal` are themselves
outputs of the same diagnostic workup (fluoroscopy, thallium scan) that
produces the target label — flagged as a potential leakage-adjacent issue in
the Stage-2 dataset review, before any model was trained. The fact that they
now dominate feature importance is the model confirming that concern, not
new evidence against it. SHAP values describe association learned by this
fitted model; they are not a causal claim that abnormal thallium results
*cause* heart disease.

## Subgroup performance by sex (Cleveland held-out test, n=61: 20 female / 41 male)

Reported for logistic regression, random forest, and XGBoost — see
`reports/subgroup_*.json`. **Explicit limitation:** the female subgroup has
only 20 test observations, which is too small to draw a reliable fairness
conclusion either way. The numbers are reported for completeness, not as a
fairness claim — this is exactly the "don't claim fairness from one metric
on a retrospective public dataset" caution the project methodology called
for at the dataset-evaluation stage.

## Phase 3 — Modern tabular models

**TabPFN: blocked, not faked.** TabPFN's pretrained weights are served from
a gated Hugging Face repository (`Prior-Labs/tabpfn_3`) requiring license
acceptance and an authenticated download. `huggingface.co` is unreachable
from this build environment, and license acceptance is a per-user action
that can't be done on someone's behalf. No result is reported for TabPFN —
see `src/diseases/cardio/run_modern_tabular.py` for exact reproduction steps
on a machine with normal network access and a Hugging Face account.

**A real packaging mistake, caught by you running this on your own
machine:** `torch` was originally in the main `requirements.txt`, which
broke `pip install -r requirements.txt` entirely on your setup — an Intel
Mac on Python 3.13. This wasn't a temporary glitch: PyTorch stopped
publishing macOS x86_64 (Intel) wheels after version 2.2.2 (April 2024), and
even 2.2.2 only supports Python up to 3.12, so an Intel Mac on 3.13 cannot
get any working torch via pip, period. Fixed by moving `torch` into an
optional `requirements-modern-tabular.txt` (used only by this one Phase 3
script), adding an `ImportError` guard so the script and test suite degrade
gracefully instead of crashing, and verified for real: hid the installed
torch package, confirmed `pytest` reports "8 passed, 1 skipped" (not
failed) and the script prints a clear explanation and exits cleanly, then
restored it and confirmed everything still works normally. Nothing else in
this project (Phases 1/2/4, and the eventual API) ever needed torch — this
was a scoping mistake in how the dependency was declared, now fixed.

**A second real cross-machine finding:** running this on a separate machine
(Python 3.13, sklearn 1.9.1, vs. this build's Python 3.12/sklearn 1.8)
reproduced every metric in the tables above almost to the decimal —
genuine, independently-verified reproducibility, not a one-off result. It
also surfaced a real forward-compatibility issue absent on the older
sklearn: `SVC(probability=True)` is deprecated as of sklearn 1.9 (removal
planned for 1.11), in favor of `CalibratedClassifierCV(SVC(), ensemble=False)`.
Fixed — same Platt-scaling mechanism either way, confirmed by rerunning
both the cardio and breast cancer experiments afterward with identical
ROC-AUC to before the change (0.955 and 0.9947 respectively) and zero
warnings.

## Phase 5 — Diabetes (imbalance/scale stress test, via the shared pipeline)

**Provenance, stated plainly (see `data/raw/SOURCE_diabetes.md` for full
detail):** this is a third-party-cleaned derivative of 2015 BRFSS survey
data (CDC → Kaggle cleaning by a third party → the file used here), not a
direct CDC release. Self-reported, not clinically measured. This is NOT
labeled "CDC BRFSS" anywhere in this project without that caveat attached.

Fetched the real file (253,680 rows, 13.9% diabetic, 0 missing values —
matches UCI's own listing for this same derivative). Ran the full model
comparison on a **documented, fixed, stratified 15,000-row subsample**
(not the full 253,680 — a scoping decision made for runtime, stated here
rather than hidden) via the exact same `src/pipeline/` code as cardio and
breast cancer.

| model | variant | ROC-AUC | PR-AUC | Sensitivity | Specificity |
|---|---|---|---|---|---|
| xgboost | default | 0.825 | 0.414 | 0.153 | 0.979 |
| lightgbm | default | 0.824 | 0.409 | 0.158 | 0.978 |
| mlp | default | 0.824 | 0.399 | 0.122 | 0.986 |
| logistic_regression | default | 0.820 | 0.403 | 0.141 | 0.980 |
| **logistic_regression_balanced** | balanced | 0.820 | 0.403 | **0.770** | 0.716 |
| **random_forest_balanced** | balanced | 0.810 | 0.386 | **0.758** | 0.699 |
| **random_forest** | **default** | 0.808 | 0.388 | **0.005** | 0.999 |
| decision_tree | default | 0.767 | 0.328 | 0.060 | 0.987 |
| svm_rbf | default | 0.738 | 0.360 | 0.089 | 0.987 |

**The single most important number in this table is Random Forest's default
sensitivity: 0.005.** At the standard 0.5 probability threshold, the default
Random Forest correctly identifies essentially **0.5% of actual diabetics**
in the test set — it almost never predicts "diabetic" at all — while still
posting a respectable-looking ROC-AUC of 0.808. This is not a bug; it's the
textbook failure mode of training on an imbalanced target (13.9% positive)
without addressing it: the model minimizes overall error by leaning heavily
toward the majority class, and ROC-AUC (which is threshold-independent)
completely hides this from view. Anyone judging this model by ROC-AUC alone
would ship something that, in practice, almost never flags a diabetic
patient. Adding `class_weight="balanced"` fixes this dramatically
(sensitivity 0.005 → 0.758) at the cost of specificity (0.999 → 0.699, i.e.
more false positives) — exactly the sensitivity/specificity trade-off a
screening tool should be tuned around deliberately, not left to a
default that happens to optimize a metric nobody should be optimizing blind.
This is the third distinct, real mechanism this project has now surfaced for
"don't trust a single headline metric," after the PR-AUC/prevalence trap
(Phase 1) and the within-site-vs-cross-site model ranking reversal (Phase 1).

**What's next for this disease:** SHAP/calibration pass (skipped in this
first cut, unlike cardio); a real attempt at pulling raw BRFSS microdata
directly from CDC instead of relying on the third-party cleaning chain;
running the full 253,680-row dataset rather than the 15k subsample, once
runtime budget allows.

## Phase 6 — Production API

A FastAPI service (`api/main.py`) serving all three trained models, built
on top of a small training script (`src/registry/train_production_models.py`)
that trains and persists exactly one production model per disease as a
`.joblib` artifact plus a `.json` metadata file — separating "research
pipeline" (Phases 1-5, many models compared) from "production system" (one
chosen model per disease, deployed), per the program plan.

**Model choice per disease deliberately does NOT default to highest AUC —
each choice is a direct, traceable consequence of a Phase 1-5 finding:**

| disease | model served | AUC | why NOT the top-AUC model instead |
|---|---|---|---|
| cardiovascular | Random Forest | 0.952 | Logistic regression scored higher within-site (0.961), but Phase 1's cross-site test showed RF generalizes better to other hospitals (avg 0.801 vs 0.768) — the realistic deployment scenario |
| breast cancer | Logistic Regression (L1) | 0.996 | Actual top performer — no countervailing finding, simplest model wins outright |
| diabetes | Logistic Regression (balanced) | 0.820 | Default XGBoost scored higher AUC (0.825) but Phase 5 showed unweighted models have near-zero sensitivity (default Random Forest: 0.5%) — clinically useless for screening despite the AUC number |

**Endpoints implemented and tested with real HTTP requests** (via FastAPI's
TestClient, not just unit-testing the underlying functions): `POST
/predict/heart`, `/predict/breast-cancer`, `/predict/diabetes`, `GET
/models`, `/models/{disease}`, `/metrics`, `/health`. 7/7 API tests pass,
covering valid predictions for all three diseases, input validation
rejection (e.g. `age: -5` correctly returns HTTP 422), and the disclaimer
text being present on every response.

**Explanations are live, not precomputed**, and use the mathematically
correct method per model family rather than one generic approach: for the
two logistic regression models, the contribution of each feature to a given
prediction is `coefficient × transformed_feature_value` — an *exact*
decomposition of the model's logit output, not an approximation. For the
Random Forest (cardiovascular), a SHAP `TreeExplainer` runs per-request on
that single row — exact for tree ensembles, computed live since there's no
cached background dataset yet (noted below as a real limitation, not hidden).

**Example real response** (`POST /predict/heart`, a 63-year-old male with
typical angina, elevated cholesterol, and an abnormal ECG):
```json
{
  "probability": 0.2075,
  "calibration_context": "Model indicates below-average estimated risk...",
  "top_contributors": [
    {"feature": "cat__cp_4.0", "contribution": -0.0921},
    {"feature": "num__ca", "contribution": -0.0841},
    {"feature": "cat__thal_3.0", "contribution": 0.0488}
  ]
}
```
Note `ca` pulling the prediction *down* here (this patient has ca=0, the
lowest-risk category) — consistent with `ca` being the second-most
important global feature found in Phase 2's SHAP analysis, now visible at
the individual-prediction level too.

**Honest limitations of this phase, not glossed over:**
- `docker/Dockerfile.api` and `docker-compose.yml` are written but **the
  actual Docker build has not been run** — no Docker available in this
  build sandbox. This needs verifying on a machine with Docker before
  calling deployment "done."
- SHAP explanations for the Random Forest model are computed fresh on every
  request with no caching — fine for a portfolio demo's request volume, a
  real bottleneck under load.
- `calibration_context` is a plain-language probability-range description,
  not yet wired to the actual held-out calibration curve data from Phase 2
  — a reasonable placeholder, not a precise calibration lookup.
- Single-worker serving (see Dockerfile comment) — model artifacts are
  loaded once into memory; multiple workers would each load their own copy,
  fine for this scale, worth revisiting before any real traffic.

## Phase 7 — Full application: auth, roles, messaging, and a React frontend

This phase expanded scope substantially beyond the original "Phase 7:
React frontend" plan, at the user's request: real authentication, three
user roles (patient/doctor/admin), database-backed doctor-patient
messaging, and a full design system — not a wireframe.

**Backend additions, all real:**
- JWT authentication with bcrypt password hashing. **A real bug caught and
  fixed here too:** `passlib`'s `CryptContext` runs an internal self-test
  with a long dummy password that raises `ValueError` against `bcrypt>=4.1`
  (which correctly rejects >72-byte inputs instead of silently truncating,
  as older bcrypt did). Fixed by calling `bcrypt` directly instead of
  through passlib — simpler and avoids the incompatibility entirely.
- Role-based access control via FastAPI dependencies — verified with actual
  403 responses in tests, not just code that looks like it should 403.
- SQLite-backed users, prediction history, and doctor-patient messaging
  (Postgres-ready — one env var change per `api/db.py`).
- A real email integration point (`api/email.py`) — **honestly not sending
  real email** in this environment (no SMTP credentials exist to fabricate
  delivery with), but the interface is real: set four environment variables
  and it sends via any standard SMTP provider, no code changes needed. Dev
  mode logs what would have been sent instead of silently doing nothing.

**14 new HTTP-level tests** (23 total across the whole backend now),
covering: registration validation (duplicate email, patient without a
doctor), login failure, a patient's prediction being recorded and
retrievable, a doctor seeing their own patients' history, **a doctor being
correctly blocked (403) from an unrelated patient's data**, a full
message send-and-read cycle between a real doctor and real patient
account, and a non-admin being blocked from `/users`.

**Frontend: React + TypeScript + Tailwind**, built to a deliberate design
system (clinical teal + clay-red reserved only for genuine risk signals, on
a cool paper background, Newsreader + IBM Plex typography) rather than a
default template — see `frontend/README.md` for the full token system.
Pages: landing (real cross-site generalization chart as the hero, not stock
content), login/register (patients pick their doctor from a real list at
signup), a role-aware dashboard (prediction forms + history + messaging for
patients; patient list + history + messaging for doctors; user management
for admins), a reports page pulling live from `GET /reports/summary` (the
same CSVs behind every table in this document), a documentation page, and
a data-and-methodology page that surfaces the same honest provenance
caveats from this report in the actual product, not just in project docs.

**Verified, not assumed:** TypeScript compiles clean (`tsc -b`), the
production build succeeds (594 kB / 172 kB gzipped — noted as needing
code-splitting before real traffic, not hidden), and the full stack was
tested **end-to-end through the real dev-server proxy against the real
running backend** — register a doctor, register a patient against that
doctor, run a real prediction, send a real message, fetch real reports —
all via actual HTTP requests through the actual network path a browser
would use, not a mocked integration.

**Honest gaps, not glossed over:**
- No automated frontend test suite (Vitest/Playwright) yet — the
  end-to-end verification above was manual (via curl through the dev
  proxy), not codified as a repeatable test.
- Admin accounts aren't self-registrable (by design) and there's no seed
  script yet to create the first one — currently requires a direct DB
  insert or a temporary code change.
- No password reset flow, no email verification on registration — real
  gaps for anything beyond a portfolio/demo context.
- Bundle size needs code-splitting before this would hold up under real
  traffic.

## Phase 8 — Closing the gaps, and deployment readiness

**Admin seeding.** `scripts/seed_admin.py` — since admin accounts are
deliberately not self-registrable (a real security decision, not an
oversight), this is the actual provisioning path. Tested for real,
including idempotency: running it twice with the same email does nothing
the second time rather than erroring or duplicating.

**Password reset — a full, security-conscious flow, not a placeholder.**
`POST /auth/forgot-password` / `POST /auth/reset-password`, using
purpose-scoped JWTs (a `"purpose": "password_reset"` claim, checked on
every use) rather than reusing the general access-token mechanism — this
means a leaked reset link can't be replayed as a session token, and
conversely a valid session token can't be misused to reset a password.
Both properties were verified with actual failing/succeeding requests, not
assumed from the code shape: email enumeration returns an identical generic
response for known and unknown addresses; the old password stops working
immediately after reset; an access token submitted to `/auth/reset-password`
is correctly rejected (400). Frontend pages (`ForgotPassword.tsx`,
`ResetPassword.tsx`) wired in and linked from the login page.

**Code splitting — measured, not assumed.** Route-level `React.lazy()` plus
manual vendor chunking (`vite.config.ts`) dropped the initial JS payload
from one 594 kB bundle to a 7.8 kB entry point; the 384 kB `recharts`
dependency now only loads on the two pages that actually chart anything
(Landing, Reports). Confirmed by rebuilding and reading the real output
sizes, not by assumption that splitting "should" help.

**A real frontend test suite**, not just a backend one. Vitest +
React Testing Library — and setting it up surfaced a genuine dependency
conflict (latest Vitest requires Vite 6+, this project is on Vite 5;
resolved by pinning compatible versions rather than force-upgrading Vite
mid-project). 13 tests: the API client's auth-header injection and error
propagation, `PredictionResult`'s rendering logic (including that a
high-risk probability is visually distinguishable from a low-risk one, not
just numerically different), and the full `AuthProvider` lifecycle —
login populating state from a real round-trip, logout clearing both token
and state, and an invalid stored token being cleared rather than leaving
the UI stuck in a half-authenticated state.

**Lint cleanup.** Running `ruff check` for the first time against the
whole accumulated codebase surfaced 98 real issues (mostly unused imports
and variables from iterative development). Added `ruff.toml` with
deliberate, stated exceptions (test files may have unused fixture-style
imports; line length isn't enforced where comments need room) rather than
either ignoring everything or chasing every possible rule, auto-fixed the
rest, and reran the full test suite afterward to confirm nothing broke
(25/25 still passing).

**CI/CD, actually exercising what was previously unverifiable.** The
GitHub Actions workflow now has three jobs: `backend` (lint + pytest, as
before), `frontend` (type-check + vitest + production build, new), and
`docker-build` (builds both `Dockerfile.api` and `Dockerfile.frontend`).
That last job matters specifically because **this sandbox has no Docker
available** — every Docker file in this project was written but never
actually built here. GitHub's own runners do have Docker, so pushing to
`main` (or opening a PR) gives the first real build verification, not
just syntax review. This is stated plainly rather than claiming the Docker
setup was "tested."

**Deployment: prepared, not completed.** `docs/DEPLOYMENT.md` has exact,
platform-specific steps (Render, Fly.io, Vercel, and local Docker Compose)
including the real config each needs (`SECRET_KEY` generation,
`VITE_API_URL` as a Vite build-time variable, `FRONTEND_URL` for reset-email
links, optional `SMTP_*` variables for real email delivery) and a
pre-launch checklist. What this document does NOT claim: that anything is
actually live. Creating a cloud account, providing billing details, and
clicking deploy all require the project owner's own credentials — I can't
do those steps on someone's behalf, and pretending otherwise would be
exactly the kind of fabrication this whole report has tried not to do.

**Honest remaining gaps after this phase:**
- The `docker-build` CI job has been written but not yet observed to pass
  on an actual GitHub Actions run (needs a real push to verify) — the
  logical next step before trusting it.
- No live URL exists yet — that's the one item on the original wishlist
  that genuinely requires the project owner to act, not just more building.
- CORS is still wide open (`allow_origins=["*"]`) — fine for local/demo
  use, flagged in the deployment checklist as something to tighten before
  calling this production-grade.

**FT-Transformer: implemented from scratch in PyTorch** (feature tokenizer +
2-layer Transformer encoder + classification head — not a third-party
library), trained on the same 242-row training split, evaluated on the same
held-out test set as every other model above.

| model | ROC-AUC | 95% CI | PR-AUC | Brier |
|---|---|---|---|---|
| logistic_regression | 0.961 | [0.898, 0.999] | 0.947 | 0.087 |
| **ft_transformer** | **0.958** | **[0.895, 0.996]** | **0.937** | **0.086** |
| svm_rbf | 0.955 | [0.884, 0.997] | 0.928 | 0.089 |

**This contradicts the Stage-1 pre-registered hypothesis.** Before training
anything, the plan explicitly predicted FT-Transformer would underperform on
this small a dataset (242 training rows) — the standard expectation for
deep tabular architectures. Instead it landed in 2nd place out of 10 models,
essentially tied with logistic regression and ahead of every gradient-boosted
tree tested. Two honest caveats before reading too much into this: (1) the
95% CI is wide and overlaps with the entire top five — a single train/test
split on 61 test rows cannot distinguish "genuinely competitive" from "got a
lucky split," and this needs to be checked across multiple seeds/splits
before being trusted; (2) this is a small (d=32, 2-layer) transformer with
heavy regularization deliberately chosen for this data size — a
larger/default-sized FT-Transformer would likely have overfit and performed
worse, so this result is partly a demonstration that architecture sizing
matters more than architecture choice at this scale, not a clean "deep
learning wins" result. Flagging the hypothesis miss explicitly here rather
than quietly dropping it, per the project's "distinguish hypothesis from
established result" rule from the original brief.


## What's next

1. Seed/split sensitivity check on the FT-Transformer result above — the
   single biggest open question from Phase 3.
2. Extend Phases 1–2 to the breast cancer (negative control) and diabetes
   (imbalance/scale stress test) datasets via the shared `src/pipeline/`
   code, changing only `src/diseases/<name>/` config.
3. Full nested-CV hyperparameter sensitivity analysis on the primary result
   above (this pass used RandomizedSearchCV inside a single CV loop, not
   full nested CV — a reasonable first-pass simplification, but the
   difference should be checked before calling the model comparison final).
4. Sensitivity check flagged in Stage 2: rerun the primary comparison with
   `ca`/`thal` removed, to see how much of the ~0.95 within-site ROC-AUC
   depends on workup-derived features versus genuine pre-diagnostic risk
   factors.
5. TabPFN, once network/Hugging Face license access is available (see the
   Phase 3 note above for exact steps).

## Phase 4 — Breast cancer (negative control, via the shared pipeline)

Loaded via sklearn's bundled copy of the official UCI Wisconsin Diagnostic
dataset (verified: 569 rows, 212/357 class split, matches UCI documentation
exactly). **Zero pipeline code was written or duplicated for this disease** —
`src/pipeline/models.py`, `preprocessing.py`, `evaluation.py`, and `tuning.py`
are byte-for-byte the same files used for cardiovascular; only
`src/diseases/breast_cancer/schema.py` (feature list) and a thin orchestration
script differ. This is the actual proof of the "one pipeline, three diseases"
architecture, not a claim about it.

| model | ROC-AUC | 95% CI | Brier |
|---|---|---|---|
| logistic_regression_l1 | 0.996 | [0.988, 1.000] | 0.022 |
| lightgbm | 0.996 | [0.985, 1.000] | 0.022 |
| logistic_regression | 0.996 | [0.986, 1.000] | 0.021 |
| svm_rbf | 0.995 | [0.984, 1.000] | 0.022 |
| xgboost | 0.994 | [0.980, 1.000] | 0.023 |
| random_forest | 0.993 | [0.982, 1.000] | 0.032 |
| mlp | 0.985 | [0.969, 0.997] | 0.076 |
| **decision_tree** | **0.895** | [0.811, 0.967] | 0.078 |
| majority_baseline | 0.500 | — | 0.368 |

**Confirms the Stage-2 hypothesis exactly, with real data.** Every ensemble
or regularized model clears 0.99 ROC-AUC — there is essentially no
discrimination headroom left on this dataset, exactly as predicted when it
was scoped as a negative control rather than a primary study. The one
genuinely informative result is the gap between a **single** decision tree
(0.895) and every ensemble/regularized method (0.99+) — a clean, real
illustration of why a single tree overfits/high-variances on this kind of
data while bagging (Random Forest), boosting (XGBoost/LightGBM), and L1/L2
regularization (Logistic Regression) all close that gap. No fairness/subgroup
analysis was run here — this dataset has no demographic variables, so
forcing that analysis would mean fabricating a finding, not reporting one.

**A real bug caught in the process, worth documenting:** wiring this dataset
into the shared pipeline initially failed with a `KeyError: 'sex'` —
tracing it back, `build_preprocessor()` used `categorical_features or
CATEGORICAL_FEATURES`, and in Python an empty list is falsy, so passing
breast cancer's genuinely-empty categorical feature list silently fell back
to cardiovascular's `['sex', 'cp', ...]` defaults instead of respecting the
empty list. Fixed to explicit `is None` checks. This is exactly the kind of
bug that a "does it run on a second dataset" test catches and a "looks fine
on the first dataset" review doesn't — a concrete argument for why the
reusability test in Phase 4 was worth doing before writing any more
disease-specific code.

## Phase 9: Per-prediction explanation report (production API)

**Problem found via the deployed UI, not a test suite.** The `/predict/*`
endpoints' `top_contributors` field returned the model's raw, one-hot
encoded feature names verbatim (`cat__thal_3.0`, `cat__thal_7.0`,
`cat__cp_4.0`) with no indication of the value the patient had actually
entered. Two distinct defects, both real:

1. **Illegible to any non-engineer.** `cat__thal_7.0` means nothing without
   already knowing the encoding scheme.
2. **Misleading for SHAP on tree models specifically.** A one-hot encoded
   categorical feature like `thal` becomes several encoded columns. SHAP's
   `TreeExplainer` can assign a non-zero value to *every one* of those
   columns for a single row — it explains deviation from an expectation
   marginalized over the feature's distribution, not "is this dummy 1 or
   0." That is why the deployed screenshot that prompted this fix showed
   both `thal_3.0` (+0.049) and `thal_7.0` (-0.049) in the same top-5 list:
   two numbers that look contradictory unless you already know SHAP's
   one-hot semantics. (Note this doesn't apply the same way to the linear
   models used for breast cancer/diabetes, where a non-selected dummy's
   coefficient is multiplied by a literal 0 — the aggregation fix below is
   correct and necessary for both cases regardless.)

**Fix:** `api/reporting.py` aggregates the encoded contributions back to
their single parent clinical variable (`cat__thal_3.0` + `cat__thal_6.0` +
`cat__thal_7.0` → one `thal` row) before anything is shown, then pairs that
aggregated number with the patient's own submitted value translated into
plain language from a hand-written label registry sourced from each
dataset's real documented codebook (UCI Heart Disease attribute
information, the UCI Wisconsin Diagnostic feature names, the 2015 BRFSS
codebook). The API's `PredictionResponse` now also returns a `methodology`
object naming the exact model family, the exact attribution method used
(SHAP TreeExplainer for the Random Forest cardiovascular model; exact
linear coefficient × value for the two logistic-regression models), the
preprocessing applied, what the model was trained on, its measured
performance, why it was selected over alternatives (reusing the same
`selection_rationale` string written in Phase 6), and named limitations of
that specific attribution method (e.g. "a linear model cannot represent
feature interactions" for the two LR-based diseases). The old raw
`top_contributors` field is kept in the response, unchanged, for
debugging — the new `feature_contributions` field is what the frontend
renders.

Verified for real, not assumed: full backend test suite (24 passed / 1
skipped, the documented torch skip) after the change, plus a manual
end-to-end check against all three trained models confirming the
aggregation actually collapses the cardiovascular `thal` dummies into one
row and that breast cancer/diabetes produce sensible aggregated output too.
Frontend: `PredictionResult.tsx` reworked to show the aggregated
contributions with the patient's plain-language value and a collapsible
"how this report was generated" section; its test file was rewritten
(the old version literally asserted the raw `cat__thal_3.0` string
appeared, which is the exact defect being fixed) and now asserts those raw
codes do NOT appear. `tsc --noEmit`, `vitest run` (15/15), and `vite build`
all pass on the updated frontend.
