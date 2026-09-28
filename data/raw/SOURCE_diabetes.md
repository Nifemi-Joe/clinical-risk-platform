# Data source — diabetes dataset (read this before trusting the numbers)

**This is NOT raw CDC data, and should never be cited as "CDC BRFSS" without
this caveat.** Per the Stage-2 dataset review, the provenance chain is:

1. **Original source:** CDC's Behavioral Risk Factor Surveillance System
   (BRFSS), 2015 survey wave — a real, official, annual US telephone health
   survey (~440,000 respondents that year).
2. **First derivative:** a third party (Alex Teboul) cleaned and released a
   subset of the 2015 BRFSS as "Diabetes Health Indicators Dataset" on
   Kaggle — recoding, feature selection, and row filtering decisions made
   at this step are not fully documented or independently reproducible by
   us.
3. **What we actually loaded:** `diabetes_binary_health_indicators_brfss2015.csv`
   (253,680 rows, 21 features + binary target, 0 missing values, 13.9%
   diabetic), fetched from a GitHub mirror of that same Kaggle file
   (`ritawkward/Data550_final`), verified to match the row count and column
   set independently documented on UCI's listing for "CDC Diabetes Health
   Indicators" (dataset id 891, DOI 10.24432/C53919, itself also a
   re-hosting of the same Kaggle file rather than a direct CDC release).

**What this means for the results in this report:**
- Every value here is **self-reported** (a phone survey), not a clinical
  measurement — fundamentally different data-generating process than
  cardiovascular (clinical exam) or breast cancer (imaging-derived), and a
  direct reason NOT to treat the three-disease comparison as "the same kind
  of task done three times."
- "Diabetes_binary" combines diagnosed diabetes and pre-diabetes in some
  versions of this cleaning pipeline — the exact recoding logic used by the
  original Kaggle curator is not available to us to audit line-by-line.
  Treat the target definition as "as documented by the third-party
  release," not as independently verified against CDC's own coding.
- Zero missing values is itself suspicious for a 253k-row phone survey —
  almost certainly the result of upstream imputation/filtering by the
  Kaggle curator, not because the CDC survey itself had no missing data.
  This is exactly the kind of thing that would need to be traced back to
  the raw BRFSS microdata before this dataset could be used for anything
  beyond a portfolio/methodology demonstration.

If this were a clinical deployment rather than a portfolio project, the
correct next step would be pulling the raw BRFSS 2015 microdata directly
from CDC (https://www.cdc.gov/brfss/annual_data/annual_2015.html) and
redoing the cleaning ourselves, not relying on this chain. Flagging that
honestly rather than presenting this as equivalent-quality data to the
other two diseases.
