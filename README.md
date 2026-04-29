# llm-deploy

Public deployment examples for serving large language models with
OpenAI-compatible APIs.

Each model lives in its own directory with a self-contained Compose file,
environment template, README, and optional benchmark scripts.

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

## Model Catalog

| Model | Runtime | API | Directory | Status |
|---|---|---|---|---|
| [Qwen3.6-35B-A3B-FP8](https://huggingface.co/Qwen/Qwen3.6-35B-A3B-FP8) | vLLM `v0.20.0` | OpenAI-compatible | [`Qwen3.6-35B-A3B-FP8/`](Qwen3.6-35B-A3B-FP8/) | Available |

## Directory Contract

Every model directory should be usable on its own and follow this shape:

```text
<model-name>/
├── .env.example          # Local path and runtime placeholders
├── README.md             # Model-specific setup and notes
├── docker-compose.yml    # Serving configuration
└── bench.py              # Optional local benchmark script
```

Model directories may include additional files when a runtime needs them, but
public examples should keep private environment details out of version control.

## What Is Included

- Docker Compose service definitions
- OpenAI-compatible API smoke tests
- Runtime-specific configuration notes
- Optional benchmark scripts for TTFT and throughput checks
- `.env.example` files with placeholder paths
- Generic, sanitized prompts and examples

## What Is Not Included

- Model weights
- Private deployment paths
- Internal IP addresses or hostnames
- Credentials, tokens, or API keys
- Production monitoring configuration

## Quick Start

Choose a model directory, copy its environment template, set `MODEL_PATH`, and
start the service:

```bash
cd Qwen3.6-35B-A3B-FP8
cp .env.example .env
docker compose up -d
```

Check the local service:

```bash
curl -fsS http://localhost:8000/health
curl -s http://localhost:8000/v1/models | python3 -m json.tool
```

Stop the service:

```bash
docker compose down
```

## Adding Another Model

Add a new top-level directory named after the model or deployment target:

```text
<model-name>/
├── .env.example
├── README.md
└── docker-compose.yml
```

The model README should document:

- Model name and upstream model card
- Runtime image and version
- Required hardware assumptions
- Exposed API and model aliases
- Required environment variables
- Start, stop, health check, and smoke test commands
- Any parser, tool-calling, multimodal, or quantization settings

Before publishing, scan the new files for private infrastructure details,
credentials, production paths, logs, or domain-specific sensitive examples.

## Validation

For the current Qwen3.6 example:

```bash
python3 -m py_compile Qwen3.6-35B-A3B-FP8/bench.py
docker compose -f Qwen3.6-35B-A3B-FP8/docker-compose.yml config
```

## License

This repository is released under the MIT License. See [LICENSE](LICENSE).
