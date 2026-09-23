# local-llm-server

Reusable `llama-server` Docker image for local OpenAI-compatible LLM endpoints.

The image does not include models. Mount GGUF files into `/models` and choose a mode with environment variables.

## Sakura

```bash
docker run --rm --gpus all \
  -p 8080:8080 \
  -v /path/to/models:/models \
  -e MODEL_TYPE=sakura \
  -e MODEL_PATH=/models/sakura-7b-qwen2.5-v1.0-iq4xs.gguf \
  ghcr.io/lgithubl/local-llm-server:latest
```

Then call:

```bash
curl http://127.0.0.1:8080/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"sakura","messages":[{"role":"user","content":"将下面日文翻译成简体中文：こんにちは"}],"stream":false}'
```

## Qwen VL Shape

```bash
docker run --rm --gpus all \
  -p 8080:8080 \
  -v /path/to/models:/models \
  -e MODEL_TYPE=qwen-vl \
  -e MODEL_PATH=/models/qwen2.5-vl.gguf \
  -e MMPROJ_PATH=/models/mmproj.gguf \
  ghcr.io/lgithubl/local-llm-server:latest
```

Sakura is text-only. Qwen-VL requires a matching language-model GGUF plus `mmproj` GGUF.
