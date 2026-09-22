"""Regenerate the synthetic fixture dataset and monitoring batches (deterministic)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in ("packages/ml", "packages/shared"):
    sys.path.insert(0, str(ROOT / p))

from modelguard_ml.synthetic import generate_loans, generate_monitoring_batches  # noqa: E402


def main() -> None:
    fixtures = ROOT / "data" / "fixtures"
    (fixtures / "monitoring").mkdir(parents=True, exist_ok=True)
    df = generate_loans()
    df.to_csv(fixtures / "synthetic_loans.csv", index=False)
    print(f"wrote synthetic_loans.csv rows={len(df)} default_rate={df.default_flag.mean():.3f}")
    for as_of, batch in generate_monitoring_batches():
        path = fixtures / "monitoring" / f"batch_{as_of}.csv"
        batch.to_csv(path, index=False)
        print(f"wrote {path.name} rows={len(batch)} default_rate={batch.default_flag.mean():.3f}")


if __name__ == "__main__":
    main()
