ARG CUDA_VERSION=12.2.2
ARG UBUNTU_VERSION=22.04
ARG LLAMA_CPP_REF=master
ARG CUDA_ARCHITECTURES=52

FROM nvidia/cuda:${CUDA_VERSION}-devel-ubuntu${UBUNTU_VERSION} AS build

ARG LLAMA_CPP_REF
ARG CUDA_ARCHITECTURES

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    ca-certificates \
    cmake \
    git \
    libcurl4-openssl-dev \
    build-essential \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /src

RUN git clone https://github.com/ggml-org/llama.cpp.git \
  && cd llama.cpp \
  && git fetch --depth 1 origin "$LLAMA_CPP_REF" \
  && git checkout --detach FETCH_HEAD \
  && cmake -S . -B build \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_CUDA_ARCHITECTURES="$CUDA_ARCHITECTURES" \
    -DGGML_CUDA=ON \
    -DBUILD_SHARED_LIBS=OFF \
    -DLLAMA_BUILD_EXAMPLES=OFF \
    -DLLAMA_BUILD_TESTS=OFF \
    -DLLAMA_CURL=ON \
  && cmake --build build --target llama-server -j"$(nproc)"

FROM nvidia/cuda:${CUDA_VERSION}-runtime-ubuntu${UBUNTU_VERSION}

ARG CUDA_VERSION
ARG CUDA_ARCHITECTURES

LABEL ai.lgithubl.cuda.version="${CUDA_VERSION}" \
      ai.lgithubl.cuda.architectures="${CUDA_ARCHITECTURES}" \
      ai.lgithubl.m40.expected_compute_capability="5.2"

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    ca-certificates \
    libcurl4 \
    libgomp1 \
  && rm -rf /var/lib/apt/lists/*

ENV HOST=0.0.0.0 \
    PORT=8080 \
    MODEL_TYPE=sakura \
    MODEL_PATH=/models/model.gguf \
    N_GPU_LAYERS=999 \
    CTX_SIZE=4096 \
    PARALLEL=1 \
    LLAMA_SERVER_BIN=/app/llama-server

COPY --from=build /src/llama.cpp/build/bin/llama-server /app/llama-server

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8080

ENTRYPOINT ["/entrypoint.sh"]
