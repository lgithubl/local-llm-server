# local-llm-server

Reusable `llama-server` Docker image for local OpenAI-compatible LLM endpoints.

The image does not include models. Mount GGUF files into `/models` and choose a mode with environment variables.

The default image build compiles `llama.cpp` with CUDA architecture `52`, which matches NVIDIA Tesla M40/Maxwell GPUs. If you build for newer GPUs, override the build arg:

```bash
docker build \
  --build-arg CUDA_ARCHITECTURES=75 \
  -t local-llm-server:cuda75 .
```

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

## Qwen2.5-VL 7B abliterated model pack

Use the `Build Model Pack` GitHub Action with its defaults to build the recommended
vision model artifact:

```text
qwen2.5-vl-7b-abliterated-q4_k_m-model
```

The artifact contains both required files:

```text
Qwen2.5-VL-7B-Instruct-abliterated.Q4_K_M.gguf
Qwen2.5-VL-7B-Instruct-abliterated.mmproj-Q8_0.gguf
```

After downloading the artifact, unpack it on the host:

```bash
mkdir -p /data/llm-models-qwen-vl
unzip qwen2.5-vl-7b-abliterated-q4_k_m-model.zip
tar -C /data/llm-models-qwen-vl -I zstd -xf qwen2.5-vl-7b-abliterated-q4_k_m-model.tar.zst
```

Run it on a different port from Sakura and text-only prompt models:

```bash
docker run -d \
  --name local-llm-qwen-vl \
  --restart unless-stopped \
  --gpus all \
  -p 8082:8080 \
  -v /data/llm-models-qwen-vl:/models:ro \
  -e MODEL_TYPE=qwen-vl \
  -e MODEL_PATH=/models/Qwen2.5-VL-7B-Instruct-abliterated.Q4_K_M.gguf \
  -e MMPROJ_PATH=/models/Qwen2.5-VL-7B-Instruct-abliterated.mmproj-Q8_0.gguf \
  -e CTX_SIZE=8192 \
  -e N_GPU_LAYERS=999 \
  ghcr.io/lgithubl/local-llm-server:m40
```

Then point Manga Studio vision features at:

```bash
LLM_API_BASE=http://host.docker.internal:8082
```

## Prompt / instruct model for Manga Studio

The model pack action defaults to the Qwen-VL pack above. Override the workflow
inputs to build the smaller text-only prompt model artifact:

```text
qwen2.5-1.5b-instruct-q4_k_m-model
```

After downloading the artifact, unpack it on the host:

```bash
mkdir -p /data/llm-models-instruct
unzip qwen2.5-1.5b-instruct-q4_k_m-model.zip
tar -C /data/llm-models-instruct -I zstd -xf qwen2.5-1.5b-instruct-q4_k_m-model.tar.zst
```

Run it on a different port from Sakura:

```bash
docker run -d \
  --name local-llm-instruct \
  --restart unless-stopped \
  --gpus all \
  -p 8081:8080 \
  -v /data/llm-models-instruct:/models:ro \
  -e MODEL_TYPE=text \
  -e MODEL_PATH=/models/qwen2.5-1.5b-instruct-q4_k_m.gguf \
  -e CTX_SIZE=4096 \
  -e N_GPU_LAYERS=999 \
  ghcr.io/lgithubl/local-llm-server:m40
```

Then point Manga Studio at:

```bash
LLM_API_BASE=http://host.docker.internal:8081
```

## k3s with Tesla M40

On the node, `nvidia-smi` must show the M40 before Kubernetes can use it. Install the NVIDIA container runtime and device plugin so the node advertises `nvidia.com/gpu`.

Example pod shape:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: local-llm-server
spec:
  containers:
    - name: server
      image: ghcr.io/lgithubl/local-llm-server:m40
      ports:
        - containerPort: 8080
      env:
        - name: MODEL_TYPE
          value: sakura
        - name: MODEL_PATH
          value: /models/model.gguf
        - name: N_GPU_LAYERS
          value: "999"
      volumeMounts:
        - name: models
          mountPath: /models
          readOnly: true
      resources:
        limits:
          nvidia.com/gpu: 1
  volumes:
    - name: models
      hostPath:
        path: /opt/models
        type: Directory
```

If it still runs on CPU, check that the node has `nvidia.com/gpu` capacity and that the pod has the GPU limit:

```bash
kubectl describe node | grep -A5 nvidia.com/gpu
kubectl describe pod local-llm-server | grep -A8 Limits
kubectl logs local-llm-server
```
