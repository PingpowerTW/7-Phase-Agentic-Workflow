#!/usr/bin/env python3
"""
Laya Decision Model CLI Helper for Antigravity & Local Terminal
Calls local Ollaya runtime at http://127.0.0.1:11435/api/decide
"""
import sys
import json
import argparse
import urllib.request
import urllib.error

OLLAYA_URL = "http://127.0.0.1:11435/api/decide"
DEFAULT_MODEL = "laya:multilingual"

def call_decide(state: str, preset: str = None, questions: dict = None, model: str = DEFAULT_MODEL):
    payload = {
        "model": model,
        "state": state
    }
    if preset:
        payload["preset"] = preset
    if questions:
        payload["questions"] = questions

    req = urllib.request.Request(
        OLLAYA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        return {"error": str(e), "success": False}

def main():
    parser = argparse.ArgumentParser(description="Query local Laya decision model via Ollaya")
    parser.add_argument("state", help="The text / context to evaluate")
    parser.add_argument("--preset", choices=["guard", "triage", "router", "moderation", "email"], default=None,
                        help="Built-in preset to use")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Model name (default: laya:multilingual)")
    parser.add_argument("--raw", action="store_true", help="Print full raw JSON")
    
    args = parser.parse_args()
    preset = args.preset or "router"
    
    result = call_decide(args.state, preset=preset, model=args.model)
    if args.raw or "error" in result:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    answers = result.get("answers", {})
    duration_ms = result.get("total_duration", 0) / 1_000_000
    print(f"[{args.model}] Preset: {preset} (latency: {duration_ms:.1f}ms)")
    print("-" * 50)
    for k, v in answers.items():
        vtype = v.get("type")
        if vtype == "choice":
            print(f"  {k:18} : {v.get('choice')} (confidence: {v.get('confidence', 0):.2f})")
        elif vtype == "noul":
            val = v.get("noul", 0)
            flag = "YES" if val > 0.5 else "NO"
            print(f"  {k:18} : {flag} (prob: {val:.2f})")
        elif vtype == "score":
            print(f"  {k:18} : {v.get('score', 0):.2f} / 3")
        else:
            print(f"  {k:18} : {v}")

if __name__ == "__main__":
    main()
