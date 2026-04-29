# Contributing

Contributions are welcome.

## Scope

This repository is for public, reusable deployment examples. Contributions
should avoid private infrastructure details, internal hostnames, IP addresses,
credentials, customer data, production logs, and domain-specific sensitive
prompts.

## Local Checks

For the current Qwen3.6 example:

```bash
python3 -m py_compile Qwen3.6-35B-A3B-FP8/bench.py
docker compose -f Qwen3.6-35B-A3B-FP8/docker-compose.yml config
```

## Pull Requests

Please include:

- What changed
- Why it changed
- How it was tested
- Any compatibility notes for hardware, vLLM versions, or model paths
