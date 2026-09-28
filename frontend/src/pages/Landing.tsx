import { Link } from 'react-router-dom'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import PublicNav from '../components/PublicNav'

// Real numbers from Phase 1 (reports/cardio_cross_site_results.csv + the
// within-site result) - not illustrative placeholders.
const GENERALIZATION_DATA = [
  { site: 'Cleveland\n(within-site)', logistic_regression: 0.961, random_forest: 0.952 },
  { site: 'Hungarian', logistic_regression: 0.887, random_forest: 0.900 },
  { site: 'Switzerland', logistic_regression: 0.737, random_forest: 0.779 },
  { site: 'VA Long Beach', logistic_regression: 0.680, random_forest: 0.723 },
]

const FINDINGS = [
  {
    n: '01',
    title: 'Cross-hospital validation drops ROC-AUC from 0.95 to 0.68',
    body: 'A model trained only on Cleveland Clinic data loses substantial discrimination when tested on three other hospitals\u2019 patients \u2014 calibration degrades even more sharply.',
  },
  {
    n: '02',
    title: 'The best within-site model was not the best cross-site model',
    body: 'Logistic regression ranked highest on its home hospital\u2019s held-out data. Random Forest \u2014 ranked lower at home \u2014 generalized better everywhere else.',
  },
  {
    n: '03',
    title: 'A model can look accurate while missing 99.5% of true cases',
    body: 'On an imbalanced diabetes screening target, a default Random Forest scored a respectable ROC-AUC of 0.81 while correctly flagging just 0.5% of actual diabetics.',
  },
]

export default function Landing() {
  return (
    <div className="min-h-screen">
      <PublicNav />

      <section className="max-w-6xl mx-auto px-6 pt-16 pb-20 grid md:grid-cols-2 gap-12 items-center">
        <div>
          <p className="data-label mb-4">Case file — cardiovascular, breast cancer, diabetes</p>
          <h1 className="text-4xl md:text-5xl leading-tight mb-6">
            Three diseases.
            <br />
            One pipeline.
            <br />
            Every result shown, including the ones that don't flatter it.
          </h1>
          <p className="text-muted max-w-prose mb-8">
            A clinical risk-prediction platform built to demonstrate rigorous
            ML engineering — leakage-safe by construction, calibrated,
            explained, and tested against a different hospital than the one
            it was trained on.
          </p>
          <div className="flex gap-3">
            <Link to="/register" className="btn-primary">Try a prediction</Link>
            <Link to="/data" className="btn-secondary">See where the data came from</Link>
          </div>
        </div>

        <div className="card animate-[fadeIn_0.6s_ease-out]">
          <p className="data-label mb-1">ROC-AUC by test site — cardiovascular model</p>
          <p className="text-sm text-muted mb-4">Same model, trained once on Cleveland. Real results.</p>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={GENERALIZATION_DATA} margin={{ left: -20 }}>
              <CartesianGrid stroke="#D8E0DA" vertical={false} />
              <XAxis dataKey="site" tick={{ fontSize: 11, fill: '#5B6B63' }} interval={0} />
              <YAxis domain={[0.6, 1]} tick={{ fontSize: 11, fill: '#5B6B63' }} />
              <Tooltip
                contentStyle={{ borderRadius: 2, borderColor: '#D8E0DA', fontSize: 13 }}
                formatter={(v: number) => v.toFixed(3)}
              />
              <Line type="monotone" dataKey="logistic_regression" name="Logistic Regression" stroke="#A8462F" strokeWidth={2} dot={{ r: 3 }} />
              <Line type="monotone" dataKey="random_forest" name="Random Forest" stroke="#1F6F5C" strokeWidth={2} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="border-t border-border">
        <div className="max-w-6xl mx-auto px-6 py-16">
          <h2 className="text-2xl mb-10">What we actually found</h2>
          <div className="space-y-10">
            {FINDINGS.map((f) => (
              <div key={f.n} className="flex gap-6">
                <span className="font-serif text-3xl text-teal/40 w-12 shrink-0">{f.n}</span>
                <div>
                  <h3 className="text-lg mb-1.5">{f.title}</h3>
                  <p className="text-muted max-w-prose">{f.body}</p>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-12">
            <Link to="/reports" className="text-teal-dark text-sm">Read the full results →</Link>
          </div>
        </div>
      </section>

      <footer className="border-t border-border py-8">
        <div className="max-w-6xl mx-auto px-6 text-xs text-muted">
          Research prototype. Not a diagnostic tool. Data sourced from the UCI
          Machine Learning Repository — full provenance on the{' '}
          <Link to="/data" className="text-teal-dark">data &amp; methodology</Link> page.
        </div>
      </footer>
    </div>
  )
}
