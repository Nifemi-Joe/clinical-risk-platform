import { useEffect, useState } from 'react'
import Layout from '../components/Layout'
import MessageThread from '../components/MessageThread'
import CardioForm from '../forms/CardioForm'
import BreastCancerForm from '../forms/BreastCancerForm'
import DiabetesForm from '../forms/DiabetesForm'
import { myPredictions, PredictionRecord } from '../lib/api'
import { useAuth } from '../lib/auth'

const TABS = [
  { key: 'cardio', label: 'Cardiovascular' },
  { key: 'breast_cancer', label: 'Breast cancer' },
  { key: 'diabetes', label: 'Diabetes' },
  { key: 'history', label: 'My history' },
  { key: 'messages', label: 'Message my doctor' },
] as const

export default function PatientDashboard() {
  const { user } = useAuth()
  const [tab, setTab] = useState<(typeof TABS)[number]['key']>('cardio')
  const [history, setHistory] = useState<PredictionRecord[]>([])

  useEffect(() => {
    if (tab === 'history') myPredictions().then(setHistory)
  }, [tab])

  return (
    <Layout title="Patient dashboard">
      <div className="flex gap-1 border-b border-border mb-8 overflow-x-auto">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2.5 text-sm whitespace-nowrap border-b-2 -mb-px transition-colors ${
              tab === t.key ? 'border-teal text-ink' : 'border-transparent text-muted hover:text-ink'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'cardio' && <CardioForm />}
      {tab === 'breast_cancer' && <BreastCancerForm />}
      {tab === 'diabetes' && <DiabetesForm />}

      {tab === 'history' && (
        <div className="card">
          {history.length === 0 ? (
            <p className="text-sm text-muted">No predictions yet — try one of the disease tabs above.</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-muted border-b border-border">
                  <th className="py-2 font-normal">Disease</th>
                  <th className="py-2 font-normal">Model</th>
                  <th className="py-2 font-normal">Probability</th>
                  <th className="py-2 font-normal">Date</th>
                </tr>
              </thead>
              <tbody>
                {history.map((r) => (
                  <tr key={r.id} className="border-b border-border last:border-0">
                    <td className="py-2 capitalize">{r.disease.replace('_', ' ')}</td>
                    <td className="py-2 font-mono text-xs">{r.model_used}</td>
                    <td className="py-2">{Math.round(r.probability * 100)}%</td>
                    <td className="py-2 text-muted">{new Date(r.created_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {tab === 'messages' && user?.doctor_id && (
        <MessageThread otherUserId={user.doctor_id} otherName="your doctor" />
      )}
    </Layout>
  )
}
