# uv migration

Goal: replace every active requirements-based install with uv projects and committed locks, preserving independently deployed service dependencies.

Architecture: root non-package project contains docs and lightweight smoke tools. Each service is a separate non-package uv project with its own uv.lock and dev test group. No workspace, because speech and web have different framework pins and speech runtime has platform-specific Torch dependencies. Speech runtime CPU/CUDA extras are mutually exclusive; tests need neither. Python root >=3.12,<3.13 (docs extension floor); web/ml >=3.11,<3.13; speech >=3.10,<3.13 to preserve CUDA base Python3.10.

1. Root/web/ml manifests, locks, Docker, uv test runner and CI. Verify: uv lock --check for all, uv sync --locked, make test, docs strict build, Docker build and demo smoke in CI.
2. Speech manifests, CPU/CUDA lock sources and Docker images. Verify: no-model tests, lock hashes, CPU and cu128 Torch source metadata and target wheel resolution. Do not download multi-GB models on host.
3. Active docs/READMEs and Make targets use uv. Remove requirements and constraints files; historical maintenance records remain snapshots. Verify: deslop, source review, no active pip or requirements commands, strict docs build.
4. Independent review, final checks, commit/push build/uv. No PR or deployment requested.

User steering: remove THIRD_PARTY_NOTICES.md. Add optional fully local GPU generation with Ollama, no mandatory Google/Gemini access. compose.ollama.yaml + compose.gpu.yaml activate gpu-materials, cache models in a named volume, initialize selected local model before ml/web become available; cloud remains explicit. Verify merged Compose routes, readiness ordering, no published LLM port or cloud provider, real local-compatible HTTP request via model stub. Actual target GPU and Gemini error requested asynchronously; infer no regional availability claim.
