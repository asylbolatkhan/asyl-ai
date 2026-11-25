"""Модельді subject бойынша бағалап, models/metrics.json сақтау.

Іске қосу / Запуск:  python scripts/train_eval.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gaitlens.model import METRICS_PATH, run_all  # noqa: E402


def main() -> None:
    out = run_all()
    for key in ("3class", "binary", "3class_raw", "binary_raw"):
        r = out[key]
        print(f"\n== {key}  ({r['n_cycles']} cycles, {r['n_subjects']} subjects, {r['cv']})")
        for name, m in r["results"].items():
            print(f"  {name:7s} acc={m['accuracy']:.3f}  bacc={m['balanced_accuracy']:.3f}  "
                  f"F1={m['macro_f1']:.3f}  per-subject bacc={m['per_subject_bacc_mean']:.3f}+/-{m['per_subject_bacc_sd']:.3f}")
    print("\nTop features (3class):")
    for f in out["importance_3class"][:8]:
        print(f"  {f['feature']:20s} {f['importance']:.4f}")
    print(f"\nSaved: {METRICS_PATH}")


if __name__ == "__main__":
    main()
