"""
Shared, disease-agnostic data loading utilities.

Design principle: this module ONLY reads raw files into a DataFrame and
applies dataset-documented recoding (e.g. "?" -> NaN, target binarization).
It must never fit anything statistical (no imputation, no scaling, no
encoding) — that all happens inside the sklearn Pipeline in
`preprocessing.py`, fit only on training folds, to keep every downstream
experiment leakage-safe by construction.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.diseases.cardio.schema import (
    COLUMN_NAMES,
    SITE_FILES,
    TARGET_BINARY,
    TARGET_RAW,
)

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"


def load_site(site: str, raw_dir: Path = RAW_DIR) -> pd.DataFrame:
    """Load one UCI Heart Disease site file (cleveland/hungarian/switzerland/va).

    Applies only documented, non-statistical recoding:
      - "?" -> NaN (the dataset's own missing-value marker)
      - binarized target: num == 0 -> 0 (no disease), num > 0 -> 1 (disease)
    No imputation, scaling, or encoding happens here.
    """
    if site not in SITE_FILES:
        raise ValueError(f"Unknown site '{site}'. Expected one of {list(SITE_FILES)}")

    path = raw_dir / SITE_FILES[site]
    if not path.exists():
        raise FileNotFoundError(
            f"Raw file not found at {path}. Fetch the official UCI Heart "
            f"Disease site files into data/raw/ before running the pipeline."
        )

    df = pd.read_csv(path, header=None, names=COLUMN_NAMES, na_values="?")
    df["site"] = site

    # Binarize target per documented convention: presence (1-4) vs absence (0).
    # This is a real modeling decision, not a data-cleaning step - it collapses
    # severity grades 1-4 together, discarding ordinal information. Flagged in
    # Stage 2 review; kept binary here to match the vast majority of published
    # baselines this project's results will be compared against, but the raw
    # `num` column is preserved for anyone who wants to revisit that choice.
    df[TARGET_BINARY] = (df[TARGET_RAW] > 0).astype(int)

    return df


def load_all_sites(raw_dir: Path = RAW_DIR) -> pd.DataFrame:
    """Load and concatenate all four sites, tagged by `site` column."""
    frames = [load_site(site, raw_dir) for site in SITE_FILES]
    return pd.concat(frames, ignore_index=True)


def missingness_report(df: pd.DataFrame) -> pd.DataFrame:
    """Per-site, per-column missingness rates - used to document the
    structural (site-dependent) missingness pattern flagged in dataset review,
    rather than assuming missingness is random across sites."""
    report = (
        df.groupby("site")
        .apply(lambda g: g.isna().mean(), include_groups=False)
        .round(3)
    )
    return report
