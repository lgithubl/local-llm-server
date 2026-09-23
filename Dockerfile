FROM ghcr.io/ggml-org/llama.cpp:server

ENV HOST=0.0.0.0 \
    PORT=8080 \
    MODEL_TYPE=sakura \
    MODEL_PATH=/models/model.gguf \
    N_GPU_LAYERS=999 \
    CTX_SIZE=4096 \
    PARALLEL=1

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8080

ENTRYPOINT ["/entrypoint.sh"]
