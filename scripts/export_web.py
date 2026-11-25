"""Python талдауын веб-интерфейске экспорттау → web/js/analysis.js

    python scripts/export_web.py            # шаблон қорытындылары + бар болса бұрынғы ЖИ мәтіндері
    python scripts/export_web.py --llm      # OpenAI арқылы мәтіндерді жаңадан жасау (OPENAI_API_KEY, .env)

Кілт браузерге ешқашан берілмейді: ЖИ мәтіндері осы жерде алдын ала жасалып, дайын күйінде сақталады.
"""
import argparse
import json
import sys
import warnings
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
warnings.simplefilter("ignore")

from gaitlens import analysis, data, model, stats, summary  # noqa: E402
from gaitlens.params import GPS_MCID  # noqa: E402

OUT = ROOT / "web" / "js" / "analysis.js"
LLM_CACHE = ROOT / "models" / "llm_summaries.json"


def _r(x, nd=3):
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    return None if x != x else round(x, nd)


def sections_json(sections):
    return [[title, [[str(ln), getattr(ln, "kind", None)] for ln in lines]] for title, lines in sections]


def subject_block(s: str, metrics: dict | None) -> dict:
    A = analysis.analyze_subject(s)
    out = {
        "gps": {c: {"mean": _r(v["mean"]), "delta": _r(v["delta"])} for c, v in A["gps"].items()},
        "counts": A["counts"], "unstable": A["unstable"],
        "unstableCycles": [[r.condition, int(r.cycle), _r(r.robust_z, 1)]
                           for r in A["anom"][A["anom"].unstable].itertuples()],
        "variability": {r.condition: _r(r.mean_sd, 2) for r in A["var"].itertuples()},
        "hipPeak": A["facts"]["hip_curve"],
        "changes": [{"param": r.param, "cond": r.condition, "base": _r(r.mean_base), "value": _r(r.mean_cond),
                     "delta": _r(r.delta), "cliffs": _r(r.cliffs), "magnitude": r.magnitude,
                     "p": _r(r.p_holm, 6), "significant": bool(r.significant), "direction": r.direction}
                    for r in stats.ranked_changes(A["cmp"]).itertuples()],
        "summary": {lng: sections_json(summary.template_summary(A["facts"], lng)) for lng in ("kk", "ru")},
        "facts": A["facts"],
    }
    if metrics:
        out["modelAcc"] = metrics["binary"]["results"]["logreg"].get("per_subject", {}).get(s)
    return out, A


def cohort_block() -> dict:
    t = stats.cohort_tests()
    rows = []
    for r in t.itertuples():
        rows.append({"pair": r.pair, "a": r.a, "b": r.b, "param": r.param, "n": int(r.n),
                     "meanA": _r(r.mean_a), "meanB": _r(r.mean_b), "diff": _r(r.mean_diff),
                     "p": _r(r.p_holm, 6), "nBetter": None if r.n_better != r.n_better else int(r.n_better)})
    return {"tests": rows}


def model_block(metrics: dict | None) -> dict | None:
    if not metrics:
        return None
    keep = {}
    for k in ("3class", "binary", "3class_raw", "binary_raw"):
        m = metrics[k]
        keep[k] = {"labels": m["labels"], "nCycles": m["n_cycles"], "nSubjects": m["n_subjects"], "cv": m["cv"],
                   "results": {name: {kk: v for kk, v in r.items() if kk != "per_subject"}
                               for name, r in m["results"].items()}}
    keep["importance3"] = metrics["importance_3class"][:10]
    keep["importance2"] = metrics["importance_binary"][:10]
    return keep


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--llm", action="store_true", help="generate AI-refined texts with OpenAI")
    ap.add_argument("--only", nargs="*", help="limit --llm to these subjects")
    args = ap.parse_args()

    metrics = model.load_metrics()
    cache = json.loads(LLM_CACHE.read_text(encoding="utf-8")) if LLM_CACHE.exists() else {}
    subjects, analyses = {}, {}
    for s in data.subjects():
        subjects[s], analyses[s] = subject_block(s, metrics)
    if args.llm:
        from concurrent.futures import ThreadPoolExecutor

        from dotenv import load_dotenv

        load_dotenv(ROOT / ".env")
        jobs = [(s, lng) for s in subjects if not args.only or s in args.only for lng in ("kk", "ru")]

        def run(job):
            s, lng = job
            A = analyses[s]
            try:
                return s, lng, summary.openai_summary(A["facts"], analysis.template_markdown(A, lng), lng), None
            except Exception as e:  # noqa: BLE001 — keep the template text on any failure
                return s, lng, None, f"{type(e).__name__}: {str(e)[:80]}"

        with ThreadPoolExecutor(max_workers=8) as pool:
            for s, lng, text, err in pool.map(run, jobs):
                if text:
                    cache.setdefault(s, {})[lng] = text
                else:
                    cache.setdefault(s, {}).pop(lng, None)
                    print(f"  {s} {lng}: template kept ({err})")
        print(f"  AI texts accepted: {sum(len(v) for v in cache.values())}/{2 * len(subjects)}")
    for s, block in subjects.items():
        if cache.get(s):
            block["llm"] = cache[s]
        block.pop("facts")
    if args.llm:
        LLM_CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")

    payload = {"generated": date.today().isoformat(), "llmModel": summary.OPENAI_MODEL if cache else None,
               "gpsMcid": GPS_MCID, "subjects": subjects, "cohort": cohort_block(), "model": model_block(metrics)}
    OUT.write_text("// Generated by scripts/export_web.py from the Python analysis (gaitlens/). Do not edit.\n"
                   "const GAITLENS = " + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n",
                   encoding="utf-8")
    print(f"saved: {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} KB), llm texts: {len(cache)} subjects")


if __name__ == "__main__":
    main()
