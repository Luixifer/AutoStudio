# AutoStudio: optional auditions of free-tier text AI (19 Nov 2026)

AutoStudio already has Llama 3.1, Gemma 4, Llama 4 Scout, FLUX.1/2, Kokoro, Whisper and Silero integration. This **adds a test harness**, not a replacement for the working pipeline.

Two **additional/alternative text critic roles** can be benchmarked on exactly the same documentary storyboard prompt:

- `gpt_oss_20b`: `@cf/openai/gpt-oss-20b`; potential alternate narration / scientific-risk critic.
- `llama_4_scout`: `@cf/meta/llama-4-scout-17b-16e-instruct`; reuse existing vision family as a textual second opinion (not a newly installed model).

## Offline trial, zero requests
```sh
python -m unittest tests.test_free_ai_audition -v
python -m scripts.free_ai_audition --prompt-file docs/quality/free_ai_example_prompt.txt --model gpt_oss_20b --model llama_4_scout
```

Cloudflare real trials are **not enabled** by this change. To opt in deliberately from a configured runner, pass `--live --max-calls 2` and pre-existing GitHub secrets. Maximum two attempts, no retry, no automatic production changes, no YouTube publication, no quota guarantee. A zero-cost test does not establish model output quality.

## Next gates
Compare response validity, science risk, specificity, hallucinations and latency on identical independently sourced prompts; then choose any production integration only after a real reviewed comparison. Do not use the Qwen3 30B A3B FP8 model: Cloudflare documents planned deprecation on 20 November 2026. Whisper/Silero/Kokoro are already installed as optional CPU paths; no duplication.

Official model references: https://developers.cloudflare.com/workers-ai/models/gpt-oss-20b/ and https://developers.cloudflare.com/workers-ai/models/ .
