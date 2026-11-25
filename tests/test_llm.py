"""Claude option: request shape and fallback behaviour, tested offline with a mock HTTP transport."""
import json

import pytest

anthropic = pytest.importorskip("anthropic")
httpx = pytest.importorskip("httpx2")

from gaitlens import summary  # noqa: E402

FACTS = {"subject": "s61520_1", "side": "RIGHT", "changes": [{"param": "GPS_a", "delta": 1.9}]}


def _client(handler):
    return anthropic.Anthropic(api_key="test",
                               http_client=anthropic.DefaultHttpxClient(transport=httpx.MockTransport(handler)))


def _message(text="**Жалпы сурет**\n- ok", stop_reason="end_turn"):
    content = [{"type": "text", "text": text}] if text is not None else []
    return {"id": "msg_1", "type": "message", "role": "assistant", "model": summary.LLM_MODEL,
            "content": content, "stop_reason": stop_reason, "stop_sequence": None,
            "usage": {"input_tokens": 10, "output_tokens": 5}}


def test_request_shape_and_text():
    seen = {}

    def handler(req):
        seen["body"] = json.loads(req.content)
        seen["beta"] = req.headers.get("anthropic-beta", "")
        return httpx.Response(200, json=_message())

    out = summary.llm_summary(FACTS, "draft", "kk", client=_client(handler))
    assert out.startswith("**Жалпы сурет**")
    body = seen["body"]
    assert body["model"] == "claude-opus-5-5"
    assert body["fallbacks"] == "default"
    assert "server-side-fallback-2026-07-01" in seen["beta"]
    assert body["output_config"] == {"effort": "low"}
    assert "thinking" not in body
    # only computed facts are sent — no raw data columns
    assert "s61520_1" in body["messages"][0]["content"]
    assert "казахском" in body["system"]


def test_refusal_raises_so_ui_falls_back():
    with pytest.raises(RuntimeError, match="refusal"):
        summary.llm_summary(FACTS, "draft", "ru",
                            client=_client(lambda r: httpx.Response(200, json=_message("", "refusal"))))


def test_api_error_raises():
    err = {"type": "error", "error": {"type": "invalid_request_error", "message": "bad"}}
    c = _client(lambda r: httpx.Response(400, json=err))
    with pytest.raises(anthropic.BadRequestError):
        summary.llm_summary(FACTS, "draft", "ru", client=c)


def test_numbers_grounded_blocks_invented_numbers():
    draft = "GPS 9.2° (Δ +1.9°), ұршық 2.3°-қа толығырақ түзелді"
    ok, extra = summary.numbers_grounded("GPS 9,2°, айырма +1.9°", draft)
    assert ok and not extra
    ok, extra = summary.numbers_grounded("GPS 9.2°, дәлдік 97.5%", draft)
    assert not ok and "97.5" in extra


def test_web_export_payload():
    import json
    import re
    from pathlib import Path
    p = Path(__file__).resolve().parent.parent / "web" / "js" / "analysis.js"
    if not p.exists():
        pytest.skip("run scripts/export_web.py first")
    s = p.read_text(encoding="utf-8")
    d = json.loads(s[s.index("{"):s.rindex("}") + 1])
    assert len(d["subjects"]) == 29 and d["model"]["binary"]["results"]["logreg"]["balanced_accuracy"] > 0.8
    for sub in d["subjects"].values():
        for lng, md in sub.get("llm", {}).items():   # every stored AI text passed the number check
            assert lng in ("kk", "ru") and md
    assert not re.search(r"sk-(proj-)?[A-Za-z0-9_-]{20,}", s)   # no API key in the browser bundle
