import PublicNav from '../components/PublicNav'

const ENDPOINTS = [
  { method: 'POST', path: '/auth/register', desc: 'Create a patient or doctor account, returns a bearer token.' },
  { method: 'POST', path: '/auth/login', desc: 'Exchange email + password for a bearer token.' },
  { method: 'GET', path: '/auth/me', desc: 'Current authenticated user.' },
  { method: 'POST', path: '/predict/heart', desc: 'Cardiovascular risk prediction. Auth required.' },
  { method: 'POST', path: '/predict/breast-cancer', desc: 'Breast cancer risk prediction. Auth required.' },
  { method: 'POST', path: '/predict/diabetes', desc: 'Diabetes risk prediction. Auth required.' },
  { method: 'GET', path: '/predictions/mine', desc: 'The authenticated patient\u2019s own prediction history.' },
  { method: 'GET', path: '/predictions/patient/{id}', desc: 'A specific patient\u2019s history — doctor (own patients only) or admin.' },
  { method: 'GET', path: '/users/my-patients', desc: 'A doctor\u2019s assigned patients.' },
  { method: 'GET', path: '/users', desc: 'All users — admin only.' },
  { method: 'POST', path: '/messages', desc: 'Send a message within an existing doctor–patient relationship.' },
  { method: 'GET', path: '/messages/thread/{other_user_id}', desc: 'Full message thread with one other user.' },
  { method: 'GET', path: '/reports/summary', desc: 'Real experiment results as JSON — no auth required.' },
  { method: 'GET', path: '/models', desc: 'Which model is deployed per disease, and why it was chosen.' },
  { method: 'GET', path: '/health', desc: 'Liveness check.' },
]

export default function Documentation() {
  return (
    <div className="min-h-screen">
      <PublicNav />
      <div className="max-w-3xl mx-auto px-6 py-16">
        <p className="data-label mb-2">For developers</p>
        <h1 className="text-3xl mb-4">Documentation</h1>
        <p className="text-muted max-w-prose mb-12">
          This page covers how the system fits together. Interactive,
          auto-generated API docs (Swagger) are available at{' '}
          <code className="font-mono text-sm bg-teal-light px-1 rounded-sm">/docs</code> on the backend directly.
        </p>

        <section className="mb-12">
          <h2 className="text-xl mb-4">Architecture</h2>
          <pre className="card font-mono text-xs leading-relaxed overflow-x-auto">
{`src/pipeline/       shared ML pipeline: preprocessing, models, evaluation, tuning
src/diseases/<x>/    per-disease config only (schema, data loading)
src/registry/        trains + persists the ONE production model per disease
api/                 FastAPI service: auth, roles, messaging, prediction serving
frontend/            this React app
reports/              real experiment output — CSVs, figures, technical report
models/               persisted .joblib artifacts + .json metadata`}
          </pre>
          <p className="text-sm text-muted mt-3">
            The same <code className="font-mono">src/pipeline/</code> code trains all
            three diseases — proven, not just claimed, in Phase 4 (see the
            data &amp; methodology page for what that caught).
          </p>
        </section>

        <section className="mb-12">
          <h2 className="text-xl mb-4">Running it locally</h2>
          <pre className="card font-mono text-xs leading-relaxed overflow-x-auto">
{`# Backend
pip install -r requirements.txt
python -m src.registry.train_production_models
uvicorn api.main:app --reload

# Frontend
cd frontend
npm install
npm run dev`}
          </pre>
        </section>

        <section className="mb-12">
          <h2 className="text-xl mb-4">Authentication</h2>
          <p className="text-sm text-muted max-w-prose mb-3">
            JWT bearer tokens, 8-hour expiry. Passwords hashed with bcrypt
            directly (not via passlib — a real compatibility issue with
            newer bcrypt versions was hit and fixed during development, see
            the technical report). Three roles: <code className="font-mono">patient</code>,{' '}
            <code className="font-mono">doctor</code>, <code className="font-mono">admin</code> — admin
            accounts are provisioned directly, not self-registered.
          </p>
        </section>

        <section className="mb-12">
          <h2 className="text-xl mb-4">Email</h2>
          <p className="text-sm text-muted max-w-prose">
            The messaging system's email notification integration point is
            real and functional, but in this environment there are no SMTP
            credentials configured — it logs what would have been sent
            instead of fabricating delivery. Set <code className="font-mono">SMTP_HOST</code>,{' '}
            <code className="font-mono">SMTP_USER</code>, <code className="font-mono">SMTP_PASSWORD</code>,{' '}
            and <code className="font-mono">FROM_EMAIL</code> to enable real delivery — no code changes needed.
          </p>
        </section>

        <section>
          <h2 className="text-xl mb-4">Endpoints</h2>
          <div className="card divide-y divide-border">
            {ENDPOINTS.map((e) => (
              <div key={e.path} className="py-3 flex items-start gap-4">
                <span className="font-mono text-xs w-14 shrink-0 pt-0.5 text-teal-dark">{e.method}</span>
                <div>
                  <div className="font-mono text-sm">{e.path}</div>
                  <div className="text-sm text-muted">{e.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}
