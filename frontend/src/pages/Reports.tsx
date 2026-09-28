import { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import PublicNav from '../components/PublicNav'
import { getReportsSummary } from '../lib/api'

function ModelTable({ rows }: { rows: any[] }) {
  if (!rows || rows.length === 0) return <p className="text-sm text-muted">No data available.</p>
  const sorted = [...rows].sort((a, b) => b.roc_auc - a.roc_auc)
  const hasSensitivity = rows.some((r) => r.sensitivity_recall !== undefined)
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="text-left text-muted border-b border-border">
          <th className="py-2 font-normal">Model</th>
          {rows.some((r) => r.variant) && <th className="py-2 font-normal">Variant</th>}
          <th className="py-2 font-normal">ROC-AUC</th>
          <th className="py-2 font-normal">PR-AUC</th>
          {hasSensitivity && <th className="py-2 font-normal">Sensitivity</th>}
          <th className="py-2 font-normal">Brier</th>
        </tr>
      </thead>
      <tbody>
        {sorted.map((r) => (
          <tr key={r.model + (r.test_site || '') + (r.variant || '')} className="border-b border-border last:border-0">
            <td className="py-2 font-mono text-xs">{r.model}{r.test_site ? ` → ${r.test_site}` : ''}</td>
            {rows.some((row) => row.variant) && <td className="py-2 text-xs">{r.variant || '—'}</td>}
            <td className="py-2">{r.roc_auc?.toFixed(3)}</td>
            <td className="py-2">{r.pr_auc?.toFixed(3)}</td>
            {hasSensitivity && (
              <td className="py-2">
                <span className={r.sensitivity_recall < 0.1 ? 'text-clay font-medium' : ''}>
                  {r.sensitivity_recall?.toFixed(3)}
                </span>
              </td>
            )}
            <td className="py-2">{r.brier_score?.toFixed(3)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

export default function Reports() {
  const [data, setData] = useState<Record<string, any[]> | null>(null)

  useEffect(() => {
    getReportsSummary().then(setData).catch(() => setData({}))
  }, [])

  const cardioChart = data?.cardio_within_site
    ?.filter((r) => r.model !== 'majority_baseline')
    .map((r) => ({ name: r.model, roc_auc: r.roc_auc }))
    .sort((a, b) => b.roc_auc - a.roc_auc)

  return (
    <div className="min-h-screen">
      <PublicNav />
      <div className="max-w-4xl mx-auto px-6 py-16">
        <p className="data-label mb-2">Real results, not illustrative</p>
        <h1 className="text-3xl mb-3">Reports</h1>
        <p className="text-muted max-w-prose mb-12">
          Every number here comes directly from the experiment CSVs produced
          by the actual pipeline runs — the same files documented in the
          technical report, served live from the backend.
        </p>

        {!data ? (
          <p className="text-sm text-muted">Loading…</p>
        ) : (
          <div className="space-y-12">
            {cardioChart && (
              <section>
                <h2 className="text-lg mb-4">Cardiovascular — within-site ROC-AUC by model</h2>
                <div className="card">
                  <ResponsiveContainer width="100%" height={280}>
                    <BarChart data={cardioChart} layout="vertical" margin={{ left: 40 }}>
                      <CartesianGrid stroke="#D8E0DA" horizontal={false} />
                      <XAxis type="number" domain={[0, 1]} tick={{ fontSize: 11, fill: '#5B6B63' }} />
                      <YAxis type="category" dataKey="name" width={140} tick={{ fontSize: 11, fill: '#5B6B63' }} />
                      <Tooltip contentStyle={{ borderRadius: 2, borderColor: '#D8E0DA', fontSize: 13 }} />
                      <Bar dataKey="roc_auc" fill="#1F6F5C" radius={[0, 2, 2, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </section>
            )}

            <section>
              <h2 className="text-lg mb-4">Cardiovascular — cross-site generalization</h2>
              <div className="card">
                <ModelTable rows={data.cardio_cross_site} />
              </div>
              <p className="text-xs text-muted mt-2">
                Trained once on Cleveland; each row is the same model evaluated
                on a genuinely different hospital, with zero refitting.
              </p>
            </section>

            <section>
              <h2 className="text-lg mb-4">Breast cancer — negative control</h2>
              <div className="card">
                <ModelTable rows={data.breast_cancer} />
              </div>
            </section>

            <section>
              <h2 className="text-lg mb-4">Diabetes — imbalance stress test</h2>
              <div className="card">
                <ModelTable rows={data.diabetes} />
              </div>
              <p className="text-xs text-muted mt-2">
                Watch the "variant" difference between default and balanced
                logistic regression / random forest — this is where the
                sensitivity collapse shows up (see data &amp; methodology page).
              </p>
            </section>
          </div>
        )}
      </div>
    </div>
  )
}
