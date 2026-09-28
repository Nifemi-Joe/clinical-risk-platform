import { useState } from 'react'
import { PredictionResponse } from '../lib/api'

const RISK_COPY: Record<PredictionResponse['risk_band'], { label: string; color: string }> = {
  low: { label: 'Low', color: '#1F6F5C' },
  'below-average': { label: 'Below average', color: '#1F6F5C' },
  elevated: { label: 'Elevated', color: '#A8462F' },
  high: { label: 'High', color: '#A8462F' },
}

export default function PredictionResult({ result }: { result: PredictionResponse }) {
  const [showMethodology, setShowMethodology] = useState(false)
  const pct = Math.round(result.probability * 100)
  const isElevated = result.probability >= 0.5
  const risk = RISK_COPY[result.risk_band] ?? RISK_COPY.low
  const contributions = result.feature_contributions?.length
    ? result.feature_contributions
    : null
  const maxAbs = contributions
    ? Math.max(...contributions.map((c) => Math.abs(c.contribution)), 0.0001)
    : 1

  return (
    <div className="card mt-6">
      {/* --- Headline number --- */}
      <div className="flex items-start justify-between gap-6 mb-2">
        <div>
          <div className="data-label mb-1">Estimated probability</div>
          <div className="text-4xl font-serif" style={{ color: isElevated ? '#A8462F' : '#1F6F5C' }}>
            {pct}%
          </div>
          <div className="flex items-center gap-2 mt-1">
            <span
              className="text-xs font-semibold uppercase tracking-wide px-2 py-0.5 rounded-full"
              style={{ color: risk.color, backgroundColor: `${risk.color}1A` }}
            >
              {risk.label} risk band
            </span>
          </div>
        </div>
        <div className="text-right">
          <div className="data-label mb-1">Model</div>
          <div className="font-mono text-sm">{result.model}</div>
        </div>
      </div>

      <p className="text-sm text-muted mt-2 mb-6">{result.calibration_context}</p>

      <div className="w-full h-2 bg-teal-light rounded-full overflow-hidden mb-8">
        <div
          className="h-full transition-all"
          style={{ width: `${pct}%`, backgroundColor: isElevated ? '#A8462F' : '#1F6F5C' }}
        />
      </div>

      {/* --- What drove this specific prediction --- */}
      <div className="mb-8">
        <div className="data-label mb-1">What influenced this estimate</div>
        <p className="text-xs text-muted mb-3">
          The clinical variables that moved this prediction the most, aggregated from the model's
          internal reasoning and matched back to what you entered.
        </p>
        <div className="space-y-3">
          {(contributions ?? []).map((c) => {
            const barPct = Math.min((Math.abs(c.contribution) / maxAbs) * 100, 100)
            const color = c.contribution > 0 ? '#A8462F' : '#1F6F5C'
            return (
              <div key={c.feature} className="text-sm">
                <div className="flex items-baseline justify-between gap-3">
                  <span>
                    <span className="font-medium">{c.label}</span>
                    <span className="text-muted"> — {c.patient_value}</span>
                  </span>
                  <span className="text-xs text-muted whitespace-nowrap">
                    {c.magnitude} · {c.direction} risk
                  </span>
                </div>
                <div className="h-1.5 bg-border rounded-full overflow-hidden mt-1">
                  <div
                    className="h-full"
                    style={{ width: `${barPct}%`, backgroundColor: color }}
                  />
                </div>
              </div>
            )
          })}
          {!contributions && (
            <p className="text-xs text-muted">No per-feature breakdown available for this model.</p>
          )}
        </div>
      </div>

      {/* --- How this number was produced --- */}
      <div className="border-t border-border pt-4 mb-4">
        <button
          type="button"
          onClick={() => setShowMethodology((v) => !v)}
          className="flex items-center justify-between w-full text-left"
          aria-expanded={showMethodology}
        >
          <span className="data-label">How this report was generated</span>
          <span className="text-xs text-muted">{showMethodology ? 'Hide' : 'Show'} details</span>
        </button>

        {showMethodology && (
          <div className="mt-4 space-y-4 text-sm">
            <div>
              <div className="text-xs font-semibold uppercase tracking-wide text-muted mb-1">Model</div>
              <p>{result.methodology.model_family}</p>
            </div>
            <div>
              <div className="text-xs font-semibold uppercase tracking-wide text-muted mb-1">
                Why this model was chosen
              </div>
              <p>{result.methodology.selection_rationale}</p>
            </div>
            <div>
              <div className="text-xs font-semibold uppercase tracking-wide text-muted mb-1">
                How the "what influenced this estimate" numbers were calculated
              </div>
              <p>{result.methodology.attribution_method}</p>
            </div>
            <div>
              <div className="text-xs font-semibold uppercase tracking-wide text-muted mb-1">
                Data preparation
              </div>
              <p>{result.methodology.preprocessing}</p>
            </div>
            <div>
              <div className="text-xs font-semibold uppercase tracking-wide text-muted mb-1">
                Trained on
              </div>
              <p>{result.methodology.trained_on}</p>
            </div>
            {result.methodology.performance_summary && (
              <div>
                <div className="text-xs font-semibold uppercase tracking-wide text-muted mb-1">
                  Measured performance
                </div>
                <p className="font-mono text-xs">{result.methodology.performance_summary}</p>
              </div>
            )}
            <div>
              <div className="text-xs font-semibold uppercase tracking-wide text-muted mb-1">
                Limitations of this specific report
              </div>
              <ul className="list-disc list-inside space-y-1 text-muted">
                {result.methodology.limitations.map((l) => (
                  <li key={l}>{l}</li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>

      <p className="text-xs text-muted border-t border-border pt-4">{result.disclaimer}</p>
    </div>
  )
}
