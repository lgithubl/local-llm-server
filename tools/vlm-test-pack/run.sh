#!/usr/bin/env sh
set -eu

BASE_URL="${1:-${VLM_BASE_URL:-http://127.0.0.1:8082}}"
MODEL="${MODEL:-qwen-vl}"

cd "$(dirname "$0")"

if [ ! -d images ] || [ -z "$(find images -maxdepth 1 -type f \( -name '*.png' -o -name '*.jpg' -o -name '*.jpeg' -o -name '*.webp' \) -print -quit)" ]; then
  python3 generate_fixtures.py --out images
fi

python3 run_vlm_smoke.py \
  --base-url "$BASE_URL" \
  --model "$MODEL" \
  --images images \
  --out results

