"""web/ қалтасын бір HTML файлға жинау (Netlify-ға немесе флешкаға салу үшін).

    python scripts/build_single.py      →  dist/index.html
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
OUT = ROOT / "dist" / "index.html"


def main() -> None:
    html = (WEB / "index.html").read_text(encoding="utf-8")
    html = re.sub(r'<link rel="stylesheet" href="([^"]+)">',
                  lambda m: "<style>\n" + (WEB / m.group(1).split("?")[0]).read_text(encoding="utf-8") + "</style>", html)
    html = re.sub(r'<script src="([^"]+)"></script>',
                  lambda m: "<script>\n" + (WEB / m.group(1).split("?")[0]).read_text(encoding="utf-8").replace("</script", "<\\/script")
                  + "</script>", html)
    assert not re.search(r"sk-(proj-)?[A-Za-z0-9_-]{20,}", html), "API key must never reach the browser bundle"
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    print(f"saved: {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
