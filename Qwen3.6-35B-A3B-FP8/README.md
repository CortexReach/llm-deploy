# Qwen3.6-35B-A3B-FP8 vLLM Deployment

This directory contains a public, sanitized example for serving
`Qwen3.6-35B-A3B-FP8` with vLLM's OpenAI-compatible API.

The files are intentionally free of private hostnames, internal IP addresses,
SSH accounts, production paths, monitoring endpoints, credentials, and
domain-specific prompts.

## Files

```text
Qwen3.6-35B-A3B-FP8/
├── docker-compose.yml
├── README.md
└── bench.py
```

## Model

| Item | Value |
|---|---|
| Model | [Qwen3.6-35B-A3B-FP8](https://huggingface.co/Qwen/Qwen3.6-35B-A3B-FP8) |
| Server | `vllm/vllm-openai:v0.20.0` |
| API | OpenAI-compatible `/v1/chat/completions` |
| Model aliases | `qwen3`, `qwen3.6`, `qwen36` |
| Context length | `131072` |
| Tensor parallel size | `4` |
| KV cache dtype | `fp8` |
| Multimodal limit | `image=4`, `video=1` |
| Speculative decoding | MTP, `num_speculative_tokens=2` |

## Hardware Assumption

The compose file is configured for a 4-GPU host with NVIDIA GPUs. It was shaped
around 4x RTX 4090 24GB class hardware:

- tensor parallel size: `4`
- FP8 KV cache enabled
- NCCL P2P disabled for PCIe consumer GPU stability
- InfiniBand disabled

Adjust these values before using different hardware.

## Start

Set `MODEL_PATH` to the local model directory, then start the service:

```bash
export MODEL_PATH=/path/to/Qwen3.6-35B-A3B-FP8
docker compose up -d
```

The service listens on port `8000`:

```bash
curl -fsS http://localhost:8000/health
curl -s http://localhost:8000/v1/models | python3 -m json.tool
```

Stop the service:

```bash
docker compose down
```

Remove the compile/cache volume:

```bash
docker compose down -v
```

## Configuration Notes

Important vLLM flags in `docker-compose.yml`:

| Flag | Value |
|---|---|
| `--model` | `/model` |
| `--served-model-name` | `qwen3 qwen3.6 qwen36` |
| `--tensor-parallel-size` | `4` |
| `--max-model-len` | `131072` |
| `--max-num-seqs` | `24` |
| `--max-num-batched-tokens` | `16384` |
| `--gpu-memory-utilization` | `0.90` |
| `--kv-cache-dtype` | `fp8` |
| `--reasoning-parser` | `qwen3` |
| `--tool-call-parser` | `qwen3_coder` |

Offline and telemetry-related environment variables are enabled:

```text
HF_HUB_OFFLINE=1
TRANSFORMERS_OFFLINE=1
DO_NOT_TRACK=1
VLLM_NO_USAGE_STATS=1
VLLM_DO_NOT_TRACK=1
```

The example does not configure API authentication. Public or shared deployments
need an explicit authentication and network access policy outside this example.

## OpenAI SDK Example

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="EMPTY",
)

resp = client.chat.completions.create(
    model="qwen3.6",
    messages=[
        {"role": "system", "content": "You are a concise assistant."},
        {"role": "user", "content": "Summarize three common code review checks."},
    ],
    max_tokens=512,
    temperature=0.7,
    top_p=0.8,
    extra_body={"chat_template_kwargs": {"enable_thinking": False}},
)

print(resp.choices[0].message.content)
```

## Smoke Tests

Health check:

```bash
curl -fsS http://localhost:8000/health
```

Non-thinking response:

```bash
curl -s http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen3.6","messages":[{"role":"user","content":"List three code review checks."}],
       "max_tokens":120,"chat_template_kwargs":{"enable_thinking":false}}'
```

Thinking response:

```bash
curl -s http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen3.6","messages":[{"role":"user","content":"What is 18% of 250?"}],
       "max_tokens":400}'
```

Tool-call response:

```bash
curl -s http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen3.6",
       "messages":[{"role":"user","content":"Check the status of order ORD-10086."}],
       "tools":[{"type":"function","function":{"name":"get_order_status",
         "parameters":{"type":"object","properties":{"order_id":{"type":"string"}},
         "required":["order_id"]}}}],
       "tool_choice":"auto","max_tokens":300,
       "chat_template_kwargs":{"enable_thinking":false}}'
```

## Benchmark

Run the included benchmark script against the local service:

```bash
python3 bench.py baseline
```

The script writes results to:

```text
/tmp/bench-results/<label>.json
```

The benchmark prompts are generic and do not contain domain-specific examples.

## References

- [Qwen3.6-35B-A3B-FP8 model card](https://huggingface.co/Qwen/Qwen3.6-35B-A3B-FP8)
- [vLLM OpenAI-compatible server](https://docs.vllm.ai/en/latest/serving/openai_compatible_server.html)
- [vLLM tool calling](https://docs.vllm.ai/en/latest/features/tool_calling.html)
- [vLLM multimodal inputs](https://docs.vllm.ai/en/latest/features/multimodal_inputs.html)
