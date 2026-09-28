import { useState } from 'react'
import { predictDiabetes, PredictionResponse } from '../lib/api'
import PredictionResult from '../components/PredictionResult'

const DEFAULTS = {
  HighBP: 0, HighChol: 0, CholCheck: 1, BMI: 26, Smoker: 0, Stroke: 0,
  HeartDiseaseorAttack: 0, PhysActivity: 1, Fruits: 1, Veggies: 1,
  HvyAlcoholConsump: 0, AnyHealthcare: 1, NoDocbcCost: 0, GenHlth: 2,
  MentHlth: 0, PhysHlth: 0, DiffWalk: 0, Sex: 1, Age: 7, Education: 5, Income: 6,
}

const YES_NO = (key: string, label: string) => ({ key, label, type: 'select' as const, options: [[1, 'Yes'], [0, 'No']] as [number, string][] })

const FIELDS = [
  YES_NO('HighBP', 'High blood pressure'),
  YES_NO('HighChol', 'High cholesterol'),
  YES_NO('CholCheck', 'Cholesterol checked in last 5 years'),
  { key: 'BMI', label: 'BMI', type: 'number' as const },
  YES_NO('Smoker', 'Smoked 100+ cigarettes lifetime'),
  YES_NO('Stroke', 'History of stroke'),
  YES_NO('HeartDiseaseorAttack', 'History of heart disease/attack'),
  YES_NO('PhysActivity', 'Physical activity in last 30 days'),
  YES_NO('Fruits', 'Eats fruit daily'),
  YES_NO('Veggies', 'Eats vegetables daily'),
  YES_NO('HvyAlcoholConsump', 'Heavy alcohol consumption'),
  YES_NO('AnyHealthcare', 'Has healthcare coverage'),
  YES_NO('NoDocbcCost', 'Skipped doctor due to cost'),
  { key: 'GenHlth', label: 'General health (1=excellent … 5=poor)', type: 'number' as const },
  { key: 'MentHlth', label: 'Poor mental health days (last 30)', type: 'number' as const },
  { key: 'PhysHlth', label: 'Poor physical health days (last 30)', type: 'number' as const },
  YES_NO('DiffWalk', 'Difficulty walking/climbing stairs'),
  { key: 'Sex', label: 'Sex', type: 'select' as const, options: [[1, 'Male'], [0, 'Female']] as [number, string][] },
  { key: 'Age', label: 'BRFSS age bucket (1=18-24 … 13=80+)', type: 'number' as const },
  { key: 'Education', label: 'Education level (1-6)', type: 'number' as const },
  { key: 'Income', label: 'Income bracket (1-8)', type: 'number' as const },
]

export default function DiabetesForm() {
  const [values, setValues] = useState<Record<string, number>>(DEFAULTS)
  const [result, setResult] = useState<PredictionResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      setResult(await predictDiabetes(values))
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
