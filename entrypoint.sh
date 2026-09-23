#!/usr/bin/env sh
set -eu

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8080}"
MODEL_TYPE="${MODEL_TYPE:-sakura}"
MODEL_PATH="${MODEL_PATH:-/models/model.gguf}"
N_GPU_LAYERS="${N_GPU_LAYERS:-999}"
CTX_SIZE="${CTX_SIZE:-4096}"
PARALLEL="${PARALLEL:-1}"

if [ ! -f "$MODEL_PATH" ]; then
  echo "Model file not found: $MODEL_PATH" >&2
  echo "Mount a model volume at /models or set MODEL_PATH." >&2
  exit 64
fi

set -- llama-server \
  --host "$HOST" \
  --port "$PORT" \
  -m "$MODEL_PATH" \
  -c "$CTX_SIZE" \
  --parallel "$PARALLEL"

case "$MODEL_TYPE" in
  sakura|text)
    set -- "$@" -ngl "$N_GPU_LAYERS"
    ;;
  qwen-vl|vision)
    if [ -z "${MMPROJ_PATH:-}" ]; then
      echo "MMPROJ_PATH is required for MODEL_TYPE=$MODEL_TYPE" >&2
      exit 64
    fi
    if [ ! -f "$MMPROJ_PATH" ]; then
      echo "MM projector file not found: $MMPROJ_PATH" >&2
      exit 64
    fi
    set -- "$@" -ngl "$N_GPU_LAYERS" --mmproj "$MMPROJ_PATH"
    ;;
  *)
    echo "Unsupported MODEL_TYPE=$MODEL_TYPE" >&2
    exit 64
    ;;
esac

if [ -n "${LLAMA_SERVER_ARGS:-}" ]; then
  # shellcheck disable=SC2086
  set -- "$@" $LLAMA_SERVER_ARGS
fi

exec "$@"
