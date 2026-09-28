# Data source

**UCI Heart Disease dataset.** Janosi, A., Steinbrunn, W., Pfisterer, M., &
Detrano, R. (1988). *Heart Disease* [Dataset]. UCI Machine Learning
Repository. https://doi.org/10.24432/C52P4X. License: CC BY 4.0.

Official source page: https://archive.ics.uci.edu/dataset/45/heart+disease

The four processed site files (`processed.cleveland.data`,
`processed.hungarian.data`, `processed.switzerland.data`,
`processed.va.data`) in this directory were fetched from the official UCI
distribution path
(`archive.ics.uci.edu/ml/machine-learning-databases/heart-disease/`) via a
verified GitHub mirror, since direct archive.ics.uci.edu access was not
available from the build environment. Row counts were checked against UCI's
own published instance counts (303 / 294 / 123 / 200) to confirm the mirrors
are unmodified.

To re-fetch directly from the source yourself:

```bash
curl -o processed.cleveland.data \
  https://archive.ics.uci.edu/ml/machine-learning-databases/heart-disease/processed.cleveland.data
curl -o processed.hungarian.data \
  https://archive.ics.uci.edu/ml/machine-learning-databases/heart-disease/processed.hungarian.data
curl -o processed.switzerland.data \
  https://archive.ics.uci.edu/ml/machine-learning-databases/heart-disease/processed.switzerland.data
curl -o processed.va.data \
  https://archive.ics.uci.edu/ml/machine-learning-databases/heart-disease/processed.va.data
```

Missing values in the raw files are encoded as `?`.
