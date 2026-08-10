#!/usr/bin/env python3
"""Stateless direct llama.cpp actor client."""
import hashlib, json, time, urllib.request
from .generate_cases import case_to_prompt

ENDPOINT = "http://127.0.0.1:8080/v1/chat/completions"
SYSTEM = "You execute deterministic finite-state machines. Return only valid JSON matching the requested schema."

def build_request(case, model, temperature=0.0, seed=None):
    payload = {"model": model, "temperature": temperature,
               "max_tokens": 1024,
               "chat_template_kwargs": {"enable_thinking": False},
               "messages": [{"role":"system","content":SYSTEM},
                            {"role":"user","content":case_to_prompt(case)}]}
    if seed is not None: payload["seed"] = seed
    return payload

def call_actor(case, model, temperature=0.0, seed=None, timeout=180):
    payload = build_request(case, model, temperature, seed)
    body = json.dumps(payload, separators=(",", ":")).encode()
    started = time.perf_counter()
    req = urllib.request.Request(ENDPOINT, data=body, headers={"Content-Type":"application/json"}, method="POST")
    record = {"case_id":case["case_id"],"stage":case["stage"],"model":model,"endpoint":ENDPOINT,
              "temperature":temperature,"seed":seed,"prompt_sha256":hashlib.sha256(body).hexdigest(),
              "request":payload,"timestamp_start":time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            record.update({"http_status":response.status,"raw_http_response":raw,"latency_ms":round((time.perf_counter()-started)*1000,2)})
            try: record["response"] = json.loads(raw)
            except json.JSONDecodeError: record["response"] = None
    except Exception as exc:
        record.update({"http_status":None,"raw_http_response":"","response":None,"error":repr(exc),"latency_ms":round((time.perf_counter()-started)*1000,2)})
    return record

def assistant_text(record):
    try: return record["response"]["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError): return ""
