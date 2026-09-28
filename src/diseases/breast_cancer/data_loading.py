"""
Breast cancer data loading. Same design rule as cardio's data_loading.py:
this module only loads and recodes documented values (here: flipping the
target polarity, see schema.py) - no imputation, scaling, or encoding.
"""
from __future__ import annotations

import pandas as pd
from sklearn.datasets import load_breast_cancer

from src.diseases.breast_cancer.schema import TARGET_BINARY


def load_breast_cancer_df() -> pd.DataFrame:
    data = load_breast_cancer(as_frame=True)
    df = data.frame.copy()
    # Flip target polarity: sklearn's 0=malignant/1=benign -> our
    # 1=malignant (condition of concern) for consistency with cardio schema.
    df[TARGET_BINARY] = 1 - df["target"]
    return df
