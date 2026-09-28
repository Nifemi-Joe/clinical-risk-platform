"""
Phase 3: modern tabular models.

TabPFN: attempted, blocked. TabPFN's pretrained weights are served from a
gated Hugging Face repo (Prior-Labs/tabpfn_3) requiring license acceptance
and an authenticated download - `huggingface.co` is not reachable from this
build environment's network, and license acceptance is a per-user action
that can't be done on someone else's behalf. This is documented, not routed
around. To run TabPFN yourself: `hf auth login` (or set `HF_TOKEN`) after
accepting the license at https://huggingface.co/Prior-Labs/tabpfn_3, on a
machine with unrestricted network access, then rerun this module.

FT-Transformer: implemented from scratch below (feature tokenizer + a small
Transformer encoder + classification head), rather than pulling in a third
-party implementation - avoids further heavy/gated dependencies, and is a
more honest demonstration of understanding the architecture than calling a
library. Deliberately small (2 layers, 4 heads, d=32) given ~240 training
rows - a large transformer on this little data would just memorize noise,
which is itself the expected/documented result being tested here (per the
Stage-1 hypothesis that deep tabular models likely underperform GBTs on
small clinical tabular data).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

try:
    import torch
    import torch.nn as nn

    HAS_TORCH = True
except ImportError:  # pragma: no cover
    HAS_TORCH = False

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from src.diseases.cardio.schema import CATEGORICAL_FEATURES, NUMERIC_FEATURES, TARGET_BINARY  # noqa: E402
from src.pipeline.data_loading import load_site  # noqa: E402
from src.pipeline.evaluation import bootstrap_ci, compute_metrics  # noqa: E402
from src.pipeline.preprocessing import build_preprocessor  # noqa: E402

RANDOM_STATE = 42
FEATURE_COLS = NUMERIC_FEATURES + CATEGORICAL_FEATURES
REPORTS_DIR = ROOT / "reports"

if HAS_TORCH:
    torch.manual_seed(RANDOM_STATE)

    class FTTransformer(nn.Module):
        """Minimal FT-Transformer: each input feature (already numeric/one-hot
        from the shared preprocessor) is projected to a d-dim token, a learned
        [CLS] token is prepended, both pass through a standard Transformer
        encoder, and the CLS output is classified. This deliberately reuses the
        SAME leakage-safe ColumnTransformer as every other model in this
        project rather than a bespoke embedding scheme, for a fair comparison."""

        def __init__(self, n_features: int, d_model: int = 32, n_heads: int = 4, n_layers: int = 2):
            super().__init__()
            # Each of the n_features (already-preprocessed, scalar) inputs gets
            # its own learned linear "tokenizer" -> a [n_features, d_model] token set.
            self.feature_tokenizers = nn.ModuleList(
                [nn.Linear(1, d_model) for _ in range(n_features)]
            )
            self.cls_token = nn.Parameter(torch.randn(1, 1, d_model) * 0.02)
            encoder_layer = nn.TransformerEncoderLayer(
                d_model=d_model, nhead=n_heads, dim_feedforward=d_model * 2,
                dropout=0.1, batch_first=True,
            )
            self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=n_layers)
            self.head = nn.Sequential(nn.LayerNorm(d_model), nn.Linear(d_model, 1))

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            # x: (batch, n_features)
            tokens = torch.stack(
                [tok(x[:, i : i + 1]) for i, tok in enumerate(self.feature_tokenizers)], dim=1
            )  # (batch, n_features, d_model)
            cls = self.cls_token.expand(x.size(0), -1, -1)
            seq = torch.cat([cls, tokens], dim=1)
            encoded = self.encoder(seq)
            cls_out = encoded[:, 0, :]
            return self.head(cls_out).squeeze(-1)

    def train_ft_transformer(X_train_t, y_train, X_test_t, y_test, epochs: int = 150):
        n_features = X_train_t.shape[1]
        model = FTTransformer(n_features=n_features)
        optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=1e-4)
        loss_fn = nn.BCEWithLogitsLoss()

        X_train_th = torch.tensor(X_train_t, dtype=torch.float32)
        y_train_th = torch.tensor(y_train.values, dtype=torch.float32)
        X_test_th = torch.tensor(X_test_t, dtype=torch.float32)

        model.train()
        for epoch in range(epochs):
            optimizer.zero_grad()
            logits = model(X_train_th)
            loss = loss_fn(logits, y_train_th)
            loss.backward()
            optimizer.step()
            if (epoch + 1) % 50 == 0:
                print(f"  epoch {epoch+1}/{epochs}  train BCE loss = {loss.item():.4f}")

        model.eval()
        with torch.no_grad():
            test_logits = model(X_test_th)
            y_prob = torch.sigmoid(test_logits).numpy()
        return y_prob


if __name__ == "__main__":
    print("=== TabPFN ===")
    print(
        "BLOCKED: requires an authenticated, license-accepted download from a "
        "gated Hugging Face repo (Prior-Labs/tabpfn_3). huggingface.co is not "
        "reachable from this environment's network allowlist, and license "
        "acceptance is a per-user step. No result fabricated. To run: accept "
        "the license at https://huggingface.co/Prior-Labs/tabpfn_3, "
        "`hf auth login`, and rerun this module on a machine with normal "
        "network access."
    )

    print("\n=== FT-Transformer (implemented from scratch) ===")
    if not HAS_TORCH:
        print(
            "SKIPPED: torch is not installed. This is expected on Intel Macs "
            "with no compatible PyTorch build, or on Python 3.13+ combined "
            "with an Intel Mac. See requirements-modern-tabular.txt for exact "
            "options (a separate Python 3.10-3.12 env, or run this phase on "
            "Linux/CI/cloud instead). Nothing else in this project needs torch."
        )
        sys.exit(0)

    df = load_site("cleveland")
    X, y = df[FEATURE_COLS], df[TARGET_BINARY]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE
    )

    preprocessor = build_preprocessor()
    X_train_t = preprocessor.fit_transform(X_train)
    X_test_t = preprocessor.transform(X_test)
    # Some ColumnTransformer outputs are sparse depending on sklearn version;
    # FT-Transformer needs dense tensors.
    if hasattr(X_train_t, "toarray"):
        X_train_t, X_test_t = X_train_t.toarray(), X_test_t.toarray()

    y_prob = train_ft_transformer(X_train_t, y_train, X_test_t, y_test)
    metrics = compute_metrics(y_test, y_prob)
    point, lo, hi = bootstrap_ci(y_test, y_prob, roc_auc_score, n_boot=1000)
    metrics["roc_auc_ci_lower"], metrics["roc_auc_ci_upper"] = lo, hi

    print(f"\nFT-Transformer  ROC-AUC={metrics['roc_auc']:.3f} [{lo:.3f},{hi:.3f}]  "
          f"PR-AUC={metrics['pr_auc']:.3f}  Brier={metrics['brier_score']:.3f}")

    row = pd.DataFrame([{"model": "ft_transformer", **metrics}])
    existing = pd.read_csv(REPORTS_DIR / "cardio_within_site_results.csv")
    updated = pd.concat([existing, row], ignore_index=True).sort_values(
        "roc_auc", ascending=False
    )
    updated.to_csv(REPORTS_DIR / "cardio_within_site_results.csv", index=False)
    print("\nAppended to reports/cardio_within_site_results.csv")
    print(updated[["model", "roc_auc", "pr_auc", "brier_score"]].to_string(index=False))
