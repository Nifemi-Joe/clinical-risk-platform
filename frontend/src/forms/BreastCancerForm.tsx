import { useState } from 'react'
import { predictBreastCancer, PredictionResponse } from '../lib/api'
import PredictionResult from '../components/PredictionResult'

const MEASURES = [
  'radius', 'texture', 'perimeter', 'area', 'smoothness',
  'compactness', 'concavity', 'concave_points', 'symmetry', 'fractal_dimension',
]
const GROUPS: { prefix: 'mean' | 'worst' | 'error'; label: string }[] = [
  { prefix: 'mean', label: 'Mean values' },
  { prefix: 'error', label: 'Standard error' },
  { prefix: 'worst', label: 'Worst (largest) values' },
]

// A real, representative benign-leaning example to start from, so the form
// isn't full of zeros - drawn from the same public dataset used for training.
const DEFAULTS: Record<string, number> = {
  mean_radius: 12.3, mean_texture: 18.1, mean_perimeter: 78.5, mean_area: 470,
  mean_smoothness: 0.09, mean_compactness: 0.08, mean_concavity: 0.05,
  mean_concave_points: 0.03, mean_symmetry: 0.17, mean_fractal_dimension: 0.06,
  radius_error: 0.3, texture_error: 1.0, perimeter_error: 2.0, area_error: 20,
  smoothness_error: 0.006, compactness_error: 0.02, concavity_error: 0.02,
  concave_points_error: 0.01, symmetry_error: 0.02, fractal_dimension_error: 0.003,
  worst_radius: 13.5, worst_texture: 23, worst_perimeter: 88, worst_area: 560,
  worst_smoothness: 0.13, worst_compactness: 0.2, worst_concavity: 0.15,
  worst_concave_points: 0.08, worst_symmetry: 0.28, worst_fractal_dimension: 0.08,
}

function label(measure: string) {
  return measure.replace('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

export default function BreastCancerForm() {
  const [values, setValues] = useState<Record<string, number>>(DEFAULTS)
  const [result, setResult] = useState<PredictionResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      setResult(await predictBreastCancer(values))
    } catch (err: any) {
      setError(err.message || 'Prediction failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <p className="text-sm text-muted mb-6 max-w-prose">
        These 30 values come from a digitized image of a fine needle aspirate
        of a breast mass - a lab or clinician would supply them, not a
        patient directly. Defaults below are a real representative example
        from the training dataset.
      </p>
      <form onSubmit={handleSubmit}>
        {GROUPS.map((g) => (
          <div key={g.prefix} className="mb-6">
            <div className="data-label mb-2">{g.label}</div>
            <div className="grid grid-cols-5 gap-3">
              {MEASURES.map((m) => {
                const key = `${g.prefix}_${m}`
                return (
                  <div key={key}>
                    <label className="field-label">{label(m)}</label>
                    <input
                      type="number"
                      step="any"
                      className="field-input"
                      value={values[key]}
                      onChange={(e) => setValues({ ...values, [key]: Number(e.target.value) })}
                    />
                  </div>
                )
              })}
            </div>
          </div>
        ))}
        <button type="submit" disabled={loading} className="btn-primary">
          {loading ? 'Estimating…' : 'Estimate risk'}
        </button>
      </form>
      {error && <p className="text-sm text-clay mt-4">{error}</p>}
      {result && <PredictionResult result={result} />}
    </div>
  )
}
