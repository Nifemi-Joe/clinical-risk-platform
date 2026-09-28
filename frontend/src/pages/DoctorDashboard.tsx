import { useEffect, useState } from 'react'
import Layout from '../components/Layout'
import MessageThread from '../components/MessageThread'
import { myPatients, patientPredictions, PredictionRecord, UserOut } from '../lib/api'

export default function DoctorDashboard() {
  const [patients, setPatients] = useState<UserOut[]>([])
  const [selected, setSelected] = useState<UserOut | null>(null)
  const [predictions, setPredictions] = useState<PredictionRecord[]>([])
  const [view, setView] = useState<'history' | 'messages'>('history')

  useEffect(() => {
    myPatients().then((p) => {
      setPatients(p)
      if (p.length > 0) setSelected(p[0])
    })
  }, [])

  useEffect(() => {
    if (selected) patientPredictions(selected.id).then(setPredictions)
  }, [selected])

  return (
    <Layout title="Doctor dashboard">
      {patients.length === 0 ? (
        <p className="text-sm text-muted">
          No patients assigned to you yet. Patients choose their doctor at registration.
        </p>
      ) : (
        <div className="grid grid-cols-[220px_1fr] gap-8">
          <div>
            <div className="data-label mb-2">Your patients</div>
            <div className="space-y-1">
              {patients.map((p) => (
                <button
                  key={p.id}
                  onClick={() => setSelected(p)}
                  className={`w-full text-left px-3 py-2 rounded-sm text-sm ${
                    selected?.id === p.id ? 'bg-teal-light text-teal-dark font-medium' : 'text-muted hover:bg-teal-light/50'
                  }`}
                >
                  {p.full_name}
                </button>
              ))}
            </div>
          </div>

          <div>
            {selected && (
              <>
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg">{selected.full_name}</h2>
                  <div className="flex gap-1 border border-border rounded-sm p-0.5">
                    <button
                      onClick={() => setView('history')}
                      className={`px-3 py-1 text-xs rounded-sm ${view === 'history' ? 'bg-teal-light text-teal-dark' : 'text-muted'}`}
                    >
                      History
                    </button>
                    <button
                      onClick={() => setView('messages')}
                      className={`px-3 py-1 text-xs rounded-sm ${view === 'messages' ? 'bg-teal-light text-teal-dark' : 'text-muted'}`}
                    >
                      Messages
                    </button>
                  </div>
                </div>

                {view === 'history' ? (
                  <div className="card">
                    {predictions.length === 0 ? (
                      <p className="text-sm text-muted">This patient hasn't run any predictions yet.</p>
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
                          {predictions.map((r) => (
                            <tr key={r.id} className="border-b border-border last:border-0">
                              <td className="py-2 capitalize">{r.disease.replace('_', ' ')}</td>
                              <td className="py-2 font-mono text-xs">{r.model_used}</td>
                              <td className="py-2">
                                <span className={r.probability >= 0.5 ? 'text-clay' : 'text-teal-dark'}>
                                  {Math.round(r.probability * 100)}%
                                </span>
                              </td>
                              <td className="py-2 text-muted">{new Date(r.created_at).toLocaleDateString()}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </div>
                ) : (
                  <MessageThread otherUserId={selected.id} otherName={selected.full_name} />
                )}
              </>
            )}
          </div>
        </div>
      )}
    </Layout>
  )
}
