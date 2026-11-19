"""Bounded, opt-in auditions of alternative Cloudflare text AIs.

Offline by default; never selects a winner, publishes or changes production.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

MODELS = {
    "gpt_oss_20b": "@cf/openai/gpt-oss-20b",
    "llama_4_scout": "@cf/meta/llama-4-scout-17b-16e-instruct",
}
MAX_PROMPT = 1200
MAX_RESPONSE_BYTES = 500_000

def candidate_payload(key, prompt):
    if key not in MODELS:
        raise ValueError("Unknown candidate; no inference")
    if not isinstance(prompt, str) or not 20 <= len(prompt) <= MAX_PROMPT:
        raise ValueError("Prompt must be 20-1200 characters")
    return {"messages": [
        {"role": "system", "content": "You are an independent scientific video storyboard reviewer. Flag unsupported claims and suggest visual variety. Never claim source verification. Answer concisely."},
        {"role": "user", "content": prompt},
    ], "max_tokens": 256, "temperature": 0}

def run_candidate(key, prompt, account, token, opener=None):
    if not re.fullmatch(r"[0-9a-fA-F]{32}", account or "") or not token:
        raise ValueError("Cloudflare credentials unavailable; no inference")
    body = json.dumps(candidate_payload(key, prompt)).encode()
    url = "https://api.cloudflare.com/client/v4/accounts/" + account + "/ai/run/" + MODELS[key]
    req = urllib.request.Request(url, data=body, headers={
        "Authorization": "Bearer " + token, "Content-Type": "application/json"
    }, method="POST")
    open_fn = opener or urllib.request.urlopen
    try:
        with open_fn(req, timeout=40) as response:
            if response.status != 200:
                raise RuntimeError("Cloudflare rejected model audition")
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as exc:
        raise RuntimeError("Cloudflare model audition HTTP " + str(exc.code)) from None
    if len(raw) > MAX_RESPONSE_BYTES:
        raise ValueError("Provider response too large")
    obj = json.loads(raw)
    if not isinstance(obj, dict) or obj.get("success") is not True:
        raise ValueError("Model response was not successful")
    result = obj.get("result")
    if not isinstance(result, dict):
        raise ValueError("Missing result")
    text = result.get("response")
    if not isinstance(text, str) or not text.strip():
        choices = result.get("choices")
        if isinstance(choices, list) and choices and isinstance(choices[0], dict):
            message = choices[0].get("message")
            if isinstance(message, dict):
                text = message.get("content")
    if not isinstance(text, str) or not text.strip():
        # gpt-oss can use the OpenAI Responses-style output envelope.
        outputs = result.get("output")
        chunks = []
        if isinstance(outputs, list):
            for entry in outputs:
                if not isinstance(entry, dict) or entry.get("type") != "message":
                    continue
                for part in entry.get("content", []):
                    if isinstance(part, dict) and part.get("type") == "output_text":
                        value = part.get("text")
                        if isinstance(value, str) and value.strip():
                            chunks.append(value.strip())
        text = "\n".join(chunks)
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Missing usable model review")
    return text.strip()[:6000]

def audition(prompt, names, live=False, max_calls=0, account="", token="", runner=run_candidate):
    if not names or len(names) != len(set(names)) or any(n not in MODELS for n in names):
        raise ValueError("Unknown or repeated models")
    if max_calls < 0 or max_calls > 2:
        raise ValueError("Hard cap: at most 2 calls")
    for key in names:
        candidate_payload(key, prompt)
    if live and (max_calls < len(names) or not account or not token):
        raise ValueError("Live auditions need explicit per-model budget and credentials")
    report = {"schema": 1, "live": bool(live), "calls_attempted": 0,
              "publish_allowed": False, "editorial_approved": False, "candidates": []}
    for key in names:
        item = {"key": key, "model": MODELS[key], "status": "planned"}
        report["candidates"].append(item)
        if live:
            report["calls_attempted"] += 1
            try:
                item["response"] = runner(key, prompt, account, token)
                item["status"] = "unverified_review"
            except (RuntimeError, ValueError, TimeoutError) as exc:
                item["status"] = "failed"
                item["error_type"] = type(exc).__name__
    return report

def main():
    parser = argparse.ArgumentParser(description="Free-tier constrained model audition; dry-run by default")
    parser.add_argument("--prompt-file", required=True)
    parser.add_argument("--model", action="append", choices=tuple(MODELS), required=True)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--max-calls", type=int, default=0)
    parser.add_argument("--out", default="output/model-audition.json")
    args = parser.parse_args()
    prompt = Path(args.prompt_file).read_text(encoding="utf-8")
    result = audition(prompt, args.model, live=args.live, max_calls=args.max_calls,
        account=os.getenv("CLOUDFLARE_ACCOUNT_ID", ""),
        token=os.getenv("CLOUDFLARE_API_TOKEN", ""))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Audition recorded; calls attempted:", result["calls_attempted"],
          "; publication disabled")

if __name__ == "__main__":
    main()
