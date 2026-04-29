#!/usr/bin/env bash
set -euo pipefail
CONDA_ROOT="${CONDA_ROOT:?set CONDA_ROOT}"
CONDA_ENV_NAME="${CONDA_ENV_NAME:?set CONDA_ENV_NAME}"
URL="${OPENAI_COMPATIBLE_CHAT_COMPLETIONS_URL:?set OPENAI_COMPATIBLE_CHAT_COMPLETIONS_URL}"
MODEL="${MODEL_ID:-qwen3.6}"
TOK="${TOKENIZER_PATH:?set TOKENIZER_PATH}"
OUT_BASE="${OUT_BASE:-/tmp/evalscope-stress/sweep}"

source "$CONDA_ROOT/etc/profile.d/conda.sh"
conda activate "$CONDA_ENV_NAME"
mkdir -p "$OUT_BASE"

# scenario: name, in_tok, out_tok, parallels, n_per_level
run_set () {
  local NAME="$1"; local IN="$2"; local OUT="$3"; shift 3
  local pairs=("$@")
  for pair in "${pairs[@]}"; do
    local P="${pair%%:*}"; local N="${pair##*:}"
    echo "===== $NAME parallel=$P n=$N in=$IN out=$OUT ====="
    evalscope perf \
      --url "$URL" --model "$MODEL" --api openai \
      --tokenizer-path "$TOK" \
      --dataset random \
      --min-prompt-length "$IN" --max-prompt-length "$IN" --prefix-length 0 \
      --max-tokens "$OUT" --min-tokens "$OUT" \
      --number "$N" --parallel "$P" \
      --temperature 0.7 --top-p 0.8 \
      --stream \
      --name "${NAME}_p${P}" \
      --outputs-dir "$OUT_BASE/$NAME" 2>&1 | tail -45
    echo
  done
}

# Short scenario (512 in / 256 out): typical short Q&A
run_set short 512 256 "1:10" "4:20" "8:32" "16:48" "24:60" "32:64"

# Long scenario (2048 in / 512 out): typical agent context
run_set long 2048 512 "1:8" "4:16" "8:24" "16:32"

# Heavy reasoning scenario (1024 in / 1024 out)
run_set medium 1024 1024 "1:6" "4:12" "8:16" "16:20"

echo "ALL DONE."
