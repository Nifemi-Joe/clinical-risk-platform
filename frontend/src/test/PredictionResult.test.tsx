import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import PredictionResult from '../components/PredictionResult'
import { PredictionResponse } from '../lib/api'

const baseResult: PredictionResponse = {
  disease: 'cardiovascular',
  model: 'random_forest',
  probability: 0.21,
  risk_band: 'below-average',
  calibration_context: 'Model indicates below-average estimated risk based on the provided variables.',
  feature_contributions: [
    {
      feature: 'ca',
      label: 'Major vessels seen on fluoroscopy',
      patient_value: '0 vessels',
      contribution: -0.08,
      direction: 'decreased',
      magnitude: 'strong',
    },
    {
      feature: 'thal',
      label: 'Thalassemia test result',
      patient_value: 'Normal',
      contribution: 0.05,
      direction: 'increased',
      magnitude: 'moderate',
    },
  ],
  top_contributors: [
    { feature: 'num__ca', contribution: -0.08 },
    { feature: 'cat__thal_3.0', contribution: 0.05 },
  ],
  methodology: {
    model_family: 'Random Forest (an ensemble of decision trees)',
    attribution_method: 'SHAP (SHapley Additive exPlanations), computed per-request with TreeExplainer.',
    preprocessing: 'Numeric fields were median-imputed and standardized; categorical fields one-hot encoded.',
    trained_on: 'UCI Heart Disease, Cleveland site, full 303 rows',
    performance_summary: 'within site test roc auc: 0.952',
    selection_rationale: 'Chosen for better cross-site generalization.',
    limitations: ['SHAP explains this model, not a general causal claim.'],
  },
  disclaimer: 'This is a research prototype. It is not a medical diagnosis.',
}

describe('PredictionResult', () => {
  it('renders the probability as a rounded percentage', () => {
    render(<PredictionResult result={baseResult} />)
    expect(screen.getByText('21%')).toBeInTheDocument()
  })

  it('always renders the non-diagnostic disclaimer', () => {
    render(<PredictionResult result={baseResult} />)
    expect(screen.getByText(/not a medical diagnosis/i)).toBeInTheDocument()
  })

  it('renders human-readable labels and the patient value, not raw encoded feature codes', () => {
    render(<PredictionResult result={baseResult} />)
    expect(screen.getByText('Major vessels seen on fluoroscopy')).toBeInTheDocument()
    expect(screen.getByText(/0 vessels/)).toBeInTheDocument()
    expect(screen.queryByText('num__ca')).not.toBeInTheDocument()
    expect(screen.queryByText('cat__thal_3.0')).not.toBeInTheDocument()
  })

  it('renders the model name', () => {
    render(<PredictionResult result={baseResult} />)
    expect(screen.getByText('random_forest')).toBeInTheDocument()
  })

  it('renders the risk band', () => {
    render(<PredictionResult result={baseResult} />)
    expect(screen.getByText(/below average risk band/i)).toBeInTheDocument()
  })

  it('reveals methodology details on demand', async () => {
    const { getByRole, findByText } = render(<PredictionResult result={baseResult} />)
    fireEvent.click(getByRole('button', { name: /how this report was generated/i }))
    expect(await findByText(/SHAP \(SHapley/i)).toBeInTheDocument()
  })

  it('renders a high-risk probability distinctly from a low-risk one', () => {
    const highRisk: PredictionResponse = { ...baseResult, probability: 0.85, risk_band: 'high' }
    const { container: lowContainer } = render(<PredictionResult result={baseResult} />)
    const { container: highContainer } = render(<PredictionResult result={highRisk} />)

    // Low risk uses the teal color, high risk uses the clay (risk) color -
    // a real, meaningful visual distinction, not just different text.
    const lowValue = lowContainer.querySelector('.text-4xl') as HTMLElement
    const highValue = highContainer.querySelector('.text-4xl') as HTMLElement
    expect(lowValue.style.color).not.toBe(highValue.style.color)
  })
})
