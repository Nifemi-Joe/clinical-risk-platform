import { useState } from 'react'
import { predictHeart, PredictionResponse } from '../lib/api'
import PredictionResult from '../components/PredictionResult'

const DEFAULTS = {
  age: 55, sex: 1, cp: 1, trestbps: 130, chol: 220, fbs: 0, restecg: 0,
  thalach: 150, exang: 0, oldpeak: 1.0, slope: 2, ca: 0, thal: 3,
}

const FIELDS: { key: keyof typeof DEFAULTS; label: string; type: 'number' | 'select'; options?: [number, string][] }[] = [
  { key: 'age', label: 'Age (years)', type: 'number' },
  { key: 'sex', label: 'Sex', type: 'select', options: [[1, 'Male'], [0, 'Female']] },
  { key: 'cp', label: 'Chest pain type', type: 'select', options: [[1, 'Typical angina'], [2, 'Atypical angina'], [3, 'Non-anginal'], [4, 'Asymptomatic']] },
  { key: 'trestbps', label: 'Resting blood pressure (mm Hg)', type: 'number' },
  { key: 'chol', label: 'Serum cholesterol (mg/dl)', type: 'number' },
  { key: 'fbs', label: 'Fasting blood sugar > 120 mg/dl', type: 'select', options: [[1, 'Yes'], [0, 'No']] },
  { key: 'restecg', label: 'Resting ECG result', type: 'select', options: [[0, 'Normal'], [1, 'ST-T abnormality'], [2, 'LV hypertrophy']] },
  { key: 'thalach', label: 'Max heart rate achieved', type: 'number' },
  { key: 'exang', label: 'Exercise-induced angina', type: 'select', options: [[1, 'Yes'], [0, 'No']] },
  { key: 'oldpeak', label: 'ST depression vs. rest', type: 'number' },
  { key: 'slope', label: 'Slope of peak exercise ST', type: 'select', options: [[1, 'Upsloping'], [2, 'Flat'], [3, 'Downsloping']] },
  { key: 'ca', label: 'Major vessels colored by fluoroscopy', type: 'select', options: [[0, '0'], [1, '1'], [2, '2'], [3, '3']] },
  { key: 'thal', label: 'Thalassemia result', type: 'select', options: [[3, 'Normal'], [6, 'Fixed defect'], [7, 'Reversible defect']] },
]

export default function CardioForm() {
  const [values, setValues] = useState<Record<string, number>>(DEFAULTS)
  const [result, setResult] = useState<PredictionResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const res = await predictHeart(values)
      setResult(res)
    } catch (err: any) {
      setError(err.message || 'Prediction failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <form onSubmit={handleSubmit} className="grid grid-cols-2 gap-4">
        {FIELDS.map((f) => (
          <div key={f.key}>
            <label className="field-label">{f.label}</label>
            {f.type === 'select' ? (
              <select
                className="field-input"
                value={values[f.key]}
                onChange={(e) => setValues({ ...values, [f.key]: Number(e.target.value) })}
              >
                {f.options!.map(([v, l]) => (
                  <option key={v} value={v}>{l}</option>
                ))}
              </select>
            ) : (
              <input
                type="number"
                step="any"
                className="field-input"
                value={values[f.key]}
                onChange={(e) => setValues({ ...values, [f.key]: Number(e.target.value) })}
              />
            )}
          </div>
        ))}
        <div className="col-span-2 mt-2">
          <button type="submit" disabled={loading} className="btn-primary">
            {loading ? 'Estimating…' : 'Estimate risk'}
          </button>
        </div>
      </form>
      {error && <p className="text-sm text-clay mt-4">{error}</p>}
      {result && <PredictionResult result={result} />}
    </div>
  )
}
