#!/usr/bin/env python3
"""vLLM benchmark using stdlib + requests. TTFT, ITL, throughput.
Usage: python3 bench.py <label>
"""
import json, time, sys, statistics, os, requests
from concurrent.futures import ThreadPoolExecutor, as_completed

URL = "http://localhost:8000/v1/chat/completions"
LABEL = sys.argv[1] if len(sys.argv) > 1 else "run"

PROMPTS = [
    ("short_factual",
     [{"role":"system","content":"你是通用助手，回答简洁。"},
      {"role":"user","content":"列出三个常见的代码评审关注点。"}],
     200, False),
    ("reasoning_no_think",
     [{"role":"system","content":"你是通用助手。"},
      {"role":"user","content":"一个服务的平均请求耗时从 120ms 上升到 180ms。请计算涨幅百分比，并给出可能排查方向。"}],
     400, False),
    ("reasoning_with_think",
     [{"role":"user","content":"某系统每分钟处理 1200 个任务，失败率 0.8%。如果目标失败率是 0.2%，需要减少多少失败任务？"}],
     1200, True),
]

def call(name, msgs, max_tok, thinking):
    body = {
        "model": "qwen3.6",
        "messages": msgs,
        "max_tokens": max_tok,
        "stream": True,
        "temperature": 1.0 if thinking else 0.7,
        "top_p": 0.95 if thinking else 0.8,
        "stream_options": {"include_usage": True},
        "chat_template_kwargs": {"enable_thinking": thinking},
    }
    t0 = time.time()
    ttft = None
    completion_tokens = 0
    with requests.post(URL, json=body, stream=True, timeout=180) as r:
        for line in r.iter_lines():
            if not line or not line.startswith(b"data:"):
                continue
            data = line[5:].strip()
            if data == b"[DONE]":
                break
            try:
                chunk = json.loads(data)
            except Exception:
                continue
            if ttft is None and chunk.get("choices") and any(chunk["choices"][0].get("delta", {}).get(k) for k in ("content","reasoning_content","reasoning")):
                ttft = time.time() - t0
            usage = chunk.get("usage")
            if usage:
                completion_tokens = usage.get("completion_tokens", completion_tokens)
    total = time.time() - t0
    decode_time = max(total - (ttft or 0), 0.001)
    return {
        "name": name,
        "ttft": ttft,
        "total": total,
        "completion_tokens": completion_tokens,
        "tput_tps": completion_tokens / decode_time,
    }

def percentile(xs, p):
    if not xs:
        return None
    s = sorted(xs)
    k = max(0, min(len(s) - 1, int(round((p / 100.0) * (len(s) - 1)))))
    return s[k]

def summarize(results, conn, wall):
    by = {}
    for r in results:
        by.setdefault(r["name"], []).append(r)
    out = {"concurrency": conn, "total_wall": round(wall, 2), "by_class": {}}
    for name, rs in by.items():
        ttfts = [r["ttft"] for r in rs if r["ttft"]]
        tputs = [r["tput_tps"] for r in rs]
        out["by_class"][name] = {
            "n": len(rs),
            "ttft_p50": round(percentile(ttfts, 50), 3) if ttfts else None,
            "ttft_p90": round(percentile(ttfts, 90), 3) if ttfts else None,
            "tput_mean": round(statistics.mean(tputs), 1),
            "tput_p50": round(percentile(tputs, 50), 1),
            "tokens_mean": round(statistics.mean([r["completion_tokens"] for r in rs]), 0),
        }
    all_tputs = [r["tput_tps"] for r in results]
    out["agg"] = {
        "tput_mean": round(statistics.mean(all_tputs), 1),
        "tput_p50": round(percentile(all_tputs, 50), 1),
    }
    return out

def run(conn, n_iter=3):
    tasks = []
    for _ in range(n_iter):
        for p in PROMPTS:
            tasks.append(p)
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=conn) as ex:
        futs = [ex.submit(call, *p) for p in tasks]
        results = [f.result() for f in as_completed(futs)]
    wall = time.time() - t0
    return summarize(results, conn, wall)

def main():
    out = {"label": LABEL, "tests": []}
    for conn in [1, 4]:
        print(f"\n=== concurrency={conn} ===", flush=True)
        s = run(conn)
        out["tests"].append(s)
        for name, st in s["by_class"].items():
            print(f"  {name:25s}  ttft_p50={st['ttft_p50']:>5}s  tput_mean={st['tput_mean']:>5} tok/s  tokens={st['tokens_mean']:>4}")
        print(f"  AGG tput_mean = {s['agg']['tput_mean']} tok/s   wall = {s['total_wall']}s")
    os.makedirs("/tmp/bench-results", exist_ok=True)
    fp = f"/tmp/bench-results/{LABEL}.json"
    json.dump(out, open(fp, "w"), indent=2, ensure_ascii=False)
    print(f"\n>>> saved {fp}")

if __name__ == "__main__":
    main()
