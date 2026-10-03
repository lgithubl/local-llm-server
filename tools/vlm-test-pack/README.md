# VLM test pack

Use this pack after `local-llm-server` is running with the Qwen-VL model pack.

Default server URL:

```text
http://127.0.0.1:8082
```

## Run

```bash
./run.sh
```

Or pass a custom URL:

```bash
./run.sh http://192.168.1.20:8082
```

The script writes:

```text
results/report.md
results/raw/*.json
results/raw/*.txt
```

## Add your own manga panels

Put `.png`, `.jpg`, `.jpeg`, or `.webp` files into `images/`, then run again:

```bash
./run.sh http://127.0.0.1:8082
```

## Pass criteria for Manga Studio Smart Import

- JSON parseable: at least 80% of images.
- Usable schema/content: at least 70% of images.
- Average image latency: below 90 seconds for interactive-ish use.

If latency is higher, the model can still be used for an offline `Enhance script` step.

## No image generation here

This test only checks whether the VLM can describe panels well enough to fill
Manga Studio script fields such as `ACTION`, `PROMPT`, `COMPOSITION`,
`ENVIRONMENT`, `LIGHTING`, and `FX`.

