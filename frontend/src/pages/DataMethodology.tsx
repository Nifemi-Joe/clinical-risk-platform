import PublicNav from '../components/PublicNav'

const DATASETS = [
  {
    name: 'Cardiovascular disease',
    source: 'UCI Heart Disease dataset',
    citation: 'Janosi, Steinbrunn, Pfisterer & Detrano (1988), UCI Machine Learning Repository, DOI 10.24432/C52P4X, CC BY 4.0.',
    detail: 'Four sites: Cleveland Clinic, Hungarian Institute of Cardiology, University Hospital Zurich/Basel, and Long Beach VA — collected 1981–1989 from patients referred for coronary angiography, not a general screening population.',
    caveat: 'ca and thal — the two most important features found by SHAP — are themselves outputs of the same diagnostic workup that produces the label, flagged before any model was trained.',
  },
  {
    name: 'Breast cancer',
    source: 'UCI Breast Cancer Wisconsin (Diagnostic)',
    citation: 'Wolberg, Mangasarian, Street & Street (1993), UCI Machine Learning Repository, DOI 10.24432/C5DW2B, CC BY 4.0.',
    detail: '569 samples, 30 features computed from digitized images of fine needle aspirates — engineered specifically to be near-linearly separable.',
    caveat: 'Used deliberately as a negative control, not a primary study — there is very little discrimination headroom left for models to differ on, and no demographic variables exist for fairness analysis.',
  },
  {
    name: 'Diabetes',
    source: 'BRFSS-derived "CDC Diabetes Health Indicators"',
    citation: 'Third-party-cleaned derivative of CDC BRFSS 2015 survey data, re-hosted on UCI (id 891, DOI 10.24432/C53919) — not a direct CDC release.',
    detail: '253,680 self-reported survey responses, 13.9% diabetic prevalence. Every value is self-reported over the phone, not clinically measured.',
    caveat: 'The provenance chain is three hops from CDC (CDC → third-party Kaggle cleaning → UCI mirror) — the exact recoding logic used upstream is not independently auditable. Never labeled "CDC BRFSS" without this caveat.',
  },
]

const IMPROVEMENTS = [
  { title: 'Stress-test the FT-Transformer result across seeds', body: 'It beat the pre-registered hypothesis on one split (n=61 test rows) — needs 5–10 more splits before that\u2019s trustworthy, not just interesting.' },
  { title: 'Remove workup-derived features and re-measure', body: 'Rerun the cardiovascular comparison without ca/thal to see how much of the ~0.95 ROC-AUC depends on features that are themselves diagnostic outputs.' },
  { title: 'Pull raw BRFSS microdata directly from CDC', body: 'Replace the third-party-cleaned diabetes dataset with a self-audited extract from CDC\u2019s own annual release.' },
  { title: 'Run TabPFN for real', body: 'Currently blocked by a gated Hugging Face license and unreachable host in the build environment — the integration point is documented and ready.' },
  { title: 'Full nested cross-validation', body: 'The current comparison uses RandomizedSearchCV inside a single CV loop, not full nested CV — a reasonable first pass, not yet the final word.' },
  { title: 'Clinical review of the model\u2019s reasoning', body: 'A clinician sanity-checking whether the SHAP explanations make medical sense is worth more than another statistic.' },
]

export default function DataMethodology() {
  return (
    <div className="min-h-screen">
      <PublicNav />
      <div className="max-w-3xl mx-auto px-6 py-16">
        <p className="data-label mb-2">Full transparency</p>
        <h1 className="text-3xl mb-4">Where the data came from, and where it falls short</h1>
        <p className="text-muted max-w-prose mb-12">
          Every dataset here was evaluated critically before use, not assumed
          suitable. Below is the honest chain for each one — source, what it
          actually is, and the caveat that has to travel with any result
          built on it.
        </p>

        <div className="space-y-10 mb-16">
          {DATASETS.map((d) => (
            <div key={d.name} className="border-l-2 border-teal pl-6">
              <h2 className="text-lg mb-1">{d.name}</h2>
              <p className="data-label mb-2">{d.source}</p>
              <p className="text-sm text-muted mb-2">{d.citation}</p>
              <p className="text-sm mb-3">{d.detail}</p>
              <p className="text-sm bg-clay-light text-clay border-l-2 border-clay pl-3 py-2">{d.caveat}</p>
            </div>
          ))}
        </div>

        <h2 className="text-2xl mb-6">How this can be improved</h2>
        <p className="text-muted max-w-prose mb-8">
          Ordered by what would most change the trustworthiness of the
          results, not by ease of implementation.
        </p>
        <div className="space-y-6">
          {IMPROVEMENTS.map((item, i) => (
            <div key={item.title} className="flex gap-4">
              <span className="font-mono text-xs text-muted pt-1 w-5 shrink-0">{i + 1}</span>
              <div>
                <h3 className="text-sm font-medium mb-1">{item.title}</h3>
                <p className="text-sm text-muted">{item.body}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
