"""
Diabetes data loading. Same design rule as the other loaders: only
documented, non-statistical recoding here (none needed for this dataset -
already 0/1 coded) plus a DOCUMENTED, fixed-size stratified subsample - not
silent truncation. The subsample is drawn once with a fixed random_state so
results are reproducible, and prevalence is preserved by stratifying on the
target.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from src.diseases.diabetes.schema import SUBSAMPLE_RANDOM_STATE, SUBSAMPLE_SIZE, TARGET_BINARY

RAW_PATH = (
    Path(__file__).resolve().parents[3]
    / "data" / "raw" / "diabetes_binary_health_indicators_brfss2015.csv"
)


def load_diabetes_df(subsample: bool = True) -> pd.DataFrame:
    if not RAW_PATH.exists():
        raise FileNotFoundError(
            f"Raw file not found at {RAW_PATH}. See data/raw/SOURCE_diabetes.md "
            f"for how to fetch it."
        )
    df = pd.read_csv(RAW_PATH)
    if not subsample or len(df) <= SUBSAMPLE_SIZE:
        return df

    # Stratified subsample - proportion of diabetic/non-diabetic rows in the
    # sample matches the full 253,680-row dataset (13.9% prevalence),
    # documented explicitly rather than silently changing the class balance.
    sampled, _ = train_test_split(
        df,
        train_size=SUBSAMPLE_SIZE,
        stratify=df[TARGET_BINARY],
        random_state=SUBSAMPLE_RANDOM_STATE,
    )
    return sampled.reset_index(drop=True)
