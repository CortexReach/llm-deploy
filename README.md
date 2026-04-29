# llm-deploy

Public deployment examples for serving large language models.

This repository currently contains a sanitized vLLM deployment example for
`Qwen3.6-35B-A3B-FP8`.

## Contents

```text
.
├── Qwen3.6-35B-A3B-FP8/
│   ├── .env.example
│   ├── README.md
│   ├── bench.py
│   └── docker-compose.yml
├── CONTRIBUTING.md
├── LICENSE
├── README.md
└── SECURITY.md
```

## Qwen3.6-35B-A3B-FP8

The deployment example serves
[`Qwen3.6-35B-A3B-FP8`](https://huggingface.co/Qwen/Qwen3.6-35B-A3B-FP8)
with vLLM's OpenAI-compatible API.

See [Qwen3.6-35B-A3B-FP8/README.md](Qwen3.6-35B-A3B-FP8/README.md) for
setup, configuration notes, smoke tests, and benchmark usage.

## What Is Included

- Docker Compose service definition for vLLM
- OpenAI-compatible API smoke tests
- Small benchmark script for TTFT and throughput checks
- Offline and telemetry-related runtime environment variables
- Generic, sanitized prompts and placeholder paths

## What Is Not Included

- Model weights
- Private deployment paths
- Internal IP addresses or hostnames
- Credentials, tokens, or API keys
- Production monitoring configuration

## License

This repository is released under the MIT License. See [LICENSE](LICENSE).
