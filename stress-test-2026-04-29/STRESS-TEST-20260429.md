# Qwen3.6-35B-A3B-FP8 vLLM 压力测试报告

**测试时间**：2026-04-29 11:48 ~ 11:58 (≈10 min)
**服务**：`<OPENAI_COMPATIBLE_CHAT_COMPLETIONS_URL>`（OpenAI 兼容）
**镜像**：`vllm/vllm-openai:v0.20.0`
**部署配置**：TP=4 / max-num-seqs=24 / max-model-len=131072 / FP8 KV / MTP num=2 / Prefix-caching on / Chunked-prefill on
**硬件**：4× RTX 4090 24GB · AMD EPYC 9124 ×2 · 251GB RAM
**测试工具**：evalscope `0.13.1`（CLI 与 v0.14 兼容） · 命令：`evalscope perf`
**数据集**：`random`（按 tokenizer 生成定长 prompt，离线友好；`min_tokens=max_tokens` 锁定输出长度）
**输出固定**：`min-tokens == max-tokens`，避免短回答稀释吞吐统计

---

## 1. 测试场景

| 场景 | 输入 token | 输出 token | 业务对应 |
|---|---|---|---|
| short | 512 | 256 | 短问答 / 单条业务查询 |
| medium | 1024 | 1024 | 推理类长答 / 长文本总结 |
| long | 2048 | 512 | Agent 上下文（带工具/历史） |

每个场景在多个并发档位（parallel）扫描，n 取 ≥4×parallel 保证统计稳定。

---

## 2. 全量结果

> Throughput = 系统聚合输出 token/s（非单流） · TTFT = 首 token 延迟 · TPOT = 每 output token 时间
> 所有请求 `--stream` 模式；temperature=0.7；top-p=0.8

### 2.1 short（512 in / 256 out）

| Parallel | n | wall (s) | QPS | Sys Throughput (tok/s) | TTFT mean (s) | TTFT P90 / P99 (s) | TPOT mean (s) | Latency mean (s) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|  1 | 10 | 24.83 | 0.40 |  103.1 | 0.183 | 0.195 / 0.195 | 0.010 | 2.48 |
|  4 | 20 | 15.22 | 1.31 |  336.3 | 0.216 | 0.300 / 0.392 | 0.011 | 2.92 |
|  8 | 32 | 20.73 | 1.54 |  395.1 | 0.250 | 0.318 / 0.444 | 0.020 | 5.09 |
| 16 | 48 | 13.01 | 3.69 |  944.9 | 0.425 | 0.926 / 0.927 | 0.016 | 4.13 |
| **24** | **60** | **14.28** | **4.20** | **1075.4** | 0.718 | 1.050 / 2.785 | 0.020 | 5.12 |
| 32 | 64 | 14.29 | 4.48 | 1146.7 | **2.069** | **4.515 / 4.732** | 0.024 | 6.25 |

### 2.2 medium（1024 in / 1024 out）

| Parallel | n | wall (s) | QPS | Sys Throughput (tok/s) | TTFT mean (s) | TTFT P90 / P99 (s) | TPOT mean (s) | Latency mean (s) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|  1 |  6 | 53.77 | 0.11 |  114.3 | 0.143 | — | 0.009 |  8.96 |
|  4 | 12 | 28.92 | 0.42 |  424.9 | 0.204 | 0.362 / 0.362 | 0.009 |  9.37 |
|  8 | 16 | 19.70 | 0.81 |  831.6 | 0.318 | 0.549 / 0.549 | 0.009 |  9.43 |
| **16** | **20** | **20.30** | **0.99** | **1009.1** | 0.603 | 0.816 / 0.816 | 0.011 | 11.07 |

### 2.3 long（2048 in / 512 out）

| Parallel | n | wall (s) | QPS | Sys Throughput (tok/s) | TTFT mean (s) | TTFT P90 / P99 (s) | TPOT mean (s) | Latency mean (s) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|  1 |  8 | 40.10 | 0.20 |  102.2 | 0.251 | — | 0.010 | 5.01 |
|  4 | 16 | 21.85 | 0.73 |  375.0 | 0.294 | 0.387 / 0.530 | 0.010 | 5.30 |
|  8 | 24 | 17.96 | 1.34 |  684.2 | 0.512 | 0.949 / 0.950 | 0.011 | 5.62 |
| **16** | **32** | **16.05** | **1.99** | **1021.0** | 0.900 | 1.817 / 1.819 | 0.015 | 7.44 |

---

## 3. 服务端可观测指标（测试期累计）

来源：`/metrics`（`vllm:*` 计数器）。全部计数包括压测期间全部请求。

| 指标 | 值 |
|---|---|
| `request_success_total{stop}` | 29 |
| `request_success_total{length}` | 396 |
| `request_success_total{abort/error/repetition}` | **0** |
| 总成功请求 | **425** |
| `prompt_tokens_total` | 619,533 |
| `generation_tokens_total` | 369,520 |
| MTP draft passes | 146,243 |
| MTP draft tokens | 292,486（= 146,243 × 2，确认 num_speculative_tokens=2） |
| MTP accepted tokens | 223,227 |
| **MTP 接受率（整体）** | **76.3%** |
| MTP 接受率 pos0 | 84.2%（123,187 / 146,243） |
| MTP 接受率 pos1 | 68.4%（100,040 / 146,243） |

GPU 测试结束快照：4 卡显存 22.9–23.0GB / 24.6GB（93–94%）；GPU util 41–76%（采样瞬时值）。

---

## 4. 关键发现

### 4.1 服务稳定性 ✅

- **425 个请求 0 失败 0 aborted**（abort/error/repetition 全为 0），含 `parallel=32` 超出 `max-num-seqs=24` 的排队场景。
- 无 KV 爆显存、无 OOM、无 NCCL hang。
- `--enable-prefix-caching` + `--enable-chunked-prefill` 在突发流量下保持 TPOT 稳定。

### 4.2 单流性能符合 README 基线 ✅

短问答 parallel=1 单流 **103 tok/s**（README 标称 106 tok/s）；medium 1024-out 场景达到 **114 tok/s**（更长 decode 摊薄了首块开销）。
说明 v0.20.0 镜像 + 现有参数仍处于上次调优后的稳态。

### 4.3 系统吞吐天花板 ≈ 1.0–1.1 K tok/s

三个场景在 parallel=16~24 时同时落在 ~1000 tok/s 附近：
- short p24 ≈ **1075 tok/s**
- long  p16 ≈ **1021 tok/s**
- medium p16 ≈ **1009 tok/s**

进一步加并发到 32（**超过 max-num-seqs=24**），吞吐仅 +6.6%（1146 vs 1075），但：
- **TTFT mean 飙到 2.07s（×3）**，P90 4.5s，P99 4.7s
- 出现明显排队（vLLM 调度器排队 8 个请求等待入 batch）

**结论**：硬天花板由 4× 4090（无 NVLink）通信 + AllReduce 决定。当前 max-num-seqs=24 是合理的容量上限。

### 4.4 MTP 推测解码状态健康 ✅

| 位置 | 接受率 | 与 README 对比 |
|---|---|---|
| pos0 | 84.2% | README: 81% (+3%) |
| pos1 | 68.4% | README: 64% (+4%) |
| 整体 | 76.3% | README: 72% (+4%) |

接受率好于历史基线，可能受 v0.20.0 中 `align mamba cache mode for spec-decoding` 与 GDN 修复影响。**保持 num_speculative_tokens=2 不变**。

### 4.5 short p4→p8 吞吐增益异常（仅 +18%）

short 场景 p4 → p8 吞吐 336→395（+18%），低于 medium 的 +96% 与 long 的 +82%。同档 P90 latency 飙到 11.3s（vs P50 3.16s）。
怀疑原因：极短 prefill（512 in）下 chunked-prefill 的调度边界在 8 路并发突发时与 MTP 验证窗口冲突。
**影响**：仅出现在「短输入 + 中并发」段，p16 起就恢复正常曲线。日常负载（含业务 agent 类长上下文）不会落到该死区。

### 4.6 Latency vs 并发 — TTFT 拐点在 24

| Parallel | short TTFT mean | 评价 |
|---|---|---|
| 1 | 0.18s | 极佳 |
| 4 | 0.22s | 优秀（用户感知无差别） |
| 8 | 0.25s | 良好 |
| 16 | 0.43s | 可接受 |
| 24 | 0.72s | **临界**（仍可用但已可感知） |
| 32 | 2.07s | **不可接受** — 已排队 |

业务 agent 类首字时间 **建议保持在 ≤24 并发**。

---

## 5. 评价

### 5.1 综合判定：**通过 / 服务可用于生产**

| 维度 | 判定 |
|---|---|
| **稳定性** | ⭐⭐⭐⭐⭐ 0 失败 / 425 请求 |
| **吞吐** | ⭐⭐⭐⭐ 系统聚合 ~1.05 K tok/s · 与 4090×4 + 35B-A3B FP8 理论相符 |
| **首字延迟** | ⭐⭐⭐⭐ p≤24 时 P99 < 3s · short 场景 P50 ≤ 0.6s |
| **Decode 速度** | ⭐⭐⭐⭐⭐ TPOT mean 在 9–24 ms 区间，即使在 p32 仍 < 35ms |
| **MTP** | ⭐⭐⭐⭐⭐ 接受率 76% 强于历史 |
| **资源饱和** | ⭐⭐⭐ 显存 94% · GPU util 41–76%（PCIe 通信限制，符合 4090 拓扑） |

### 5.2 对照 README

部署文档预期：「单流 106 tok/s · 并发 4 系统 ~397 tok/s · 短问答 TTFT 101ms」

实测：

| 指标 | README | 实测（random ds） | 偏差 |
|---|---|---|---|
| 单流 tok/s | 106 | 103.1 | **-3%**（在采样误差内） |
| 并发 4 系统 tok/s | ≈400 | 336.3（short）/ 374.9（long） | **-7~16%** |
| 短问答 TTFT | 101 ms | 183 ms | **+82 ms** |

并发 4 系统吞吐与 TTFT 比 README 略低，原因主要是 **测试 prompt 不同**：README 用业务样板 prompt（已被 prefix-cache 命中），本次用 `random` 数据集（每条都是首次见，prefix-cache 几乎无作用）。压测口径更"悲观"，更接近**真实首次请求** 场景。

### 5.3 容量建议

| 场景 | 安全并发上限 | 备注 |
|---|---|---|
| 短问答（如医嘱速查） | **20** | 给 `max-num-seqs=24` 留 ~15% 余量，TTFT P99 < 1.5s |
| Agent 上下文（2K~4K in） | **12** | KV 占用更高，留更多余量 |
| 推理长答（含 thinking） | **8** | thinking 模式实际输出更长（≥2K tokens） |

**触发限流的指标**（见 README 第四节阈值）：
- `vllm:num_requests_waiting > 5` 持续 1min → 扩容信号
- `vllm:gpu_cache_usage_perc > 0.95` → 立即降 `max-model-len` 或 `max-num-seqs`

### 5.4 待跟进

1. **short p4→p8 死区**：建议复跑该档（更大 n=64，多次取均值）确认是否抖动；若复现，可尝试将 `max-num-batched-tokens` 从 16384 调整为 8192/32768 观察。
2. **prefix-cache 实测**：补一组用业务样板 prompt 的对照实验，量化 prefix-caching 在并发场景的实际收益。
3. **冷启基线**：当前都是 warm 测试。建议在重启容器后立即跑一次 short p1，对比首请求 TTFT。
4. **加 thinking 模式压测**：`enable_thinking=true` + `max_tokens=4096`（实际 1k~2k 输出）下重测 medium 场景 — 反映真实推理类调用。

---

## 6. 复现命令

```bash
ssh <USER>@<SERVER_IP> -p <PORT>
source /path/to/anaconda3/etc/profile.d/conda.sh
conda activate <CONDA_ENV>

# 单档示例
evalscope perf \
  --url <OPENAI_COMPATIBLE_CHAT_COMPLETIONS_URL> \
  --model qwen3.6 --api openai \
  --tokenizer-path /path/to/tokenizer \
  --dataset random \
  --min-prompt-length 512 --max-prompt-length 512 --prefix-length 0 \
  --max-tokens 256 --min-tokens 256 \
  --number 60 --parallel 24 \
  --temperature 0.7 --top-p 0.8 --stream \
  --name short_p24 \
  --outputs-dir /tmp/evalscope-stress/sweep/short

# 批量扫描脚本（含 short/medium/long）
bash /tmp/evalscope-stress/run_sweep.sh   # 写入 /tmp/evalscope-stress/sweep.log
```

结果产物（保留在 <SERVER_IP>）：

```
/tmp/evalscope-stress/
├── run_sweep.sh                   # 扫描脚本（短/中/长 × 多并发档位）
├── sweep.log                      # 全部 stdout（含 percentile 表）
└── sweep/
    ├── short/<ts>/short_p{1,4,8,16,24,32}/{benchmark_summary.json,benchmark_data.db}
    ├── medium/<ts>/medium_p{1,4,8,16}/...
    └── long/<ts>/long_p{1,4,8,16}/...
```

每个 `benchmark_data.db` 含每条请求的完整时间序列（chunk-level latency），可用 sqlite3 进一步分析。

---

## 7. 一句话结论

> **Qwen3.6-35B-A3B-FP8 在 4× RTX 4090 + vLLM v0.20.0 + 现有配置下满足生产负载**：单流 ~103 tok/s，系统吞吐顶到 ~1.05 K tok/s 时（parallel ≤ 24）TTFT 仍可控；超过 max-num-seqs=24 后 TTFT 显著恶化，**应在网关层把并发上限设到 24（推荐 20，留余量）**。
