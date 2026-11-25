"""Демонстрациялық есептерді жасау / Генерация демонстрационных отчётов.

Іске қосу / Запуск:  python scripts/make_demo.py [subject ...]
Нәтиже / Результат:  demo/GaitLens_<subject>_<kk|ru>.html
"""
import sys
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from gaitlens.report import patient_report  # noqa: E402

# s61520_1  — типтік: ұршық созылуы жақсарды, GPS нашарлады / типичный случай
# s61520_7  — кері байланыс ұршықты жақсартпады / обратная связь не улучшила бедро
# s61520_22 — ұршық моменті жоқ (деректер сапасы) / нет момента бедра (качество данных)
DEFAULT = ["s61520_1", "s61520_7", "s61520_22"]


def main() -> None:
    subjects = sys.argv[1:] or DEFAULT
    out = ROOT / "demo"
    out.mkdir(exist_ok=True)
    warnings.simplefilter("ignore")
    for s in subjects:
        for lang in ("kk", "ru"):
            path = out / f"GaitLens_{s}_{lang}.html"
            path.write_text(patient_report(s, lang), encoding="utf-8")
            print(f"saved: {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
