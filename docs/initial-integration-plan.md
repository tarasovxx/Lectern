# LEctern initial integration plan

Goal: combine the existing teaching UI and learning material generation with whole-recording local speech recognition in one reproducible repository.

Architecture: services/web (AdaptiveEducationWeb), services/ml (AdaptiveEducationML), services/speech (yadrovichi). Keep existing code and APIs; add a web adapter for local whole-file transcription. Docker Compose provides demo, local CPU, local GPU, and explicit cloud configuration. Default demo contains synthetic data and never represents real model output.

Constraints: local processing by default; no automatic cloud fallback; no secrets or recordings in git; preserve source provenance. First integration is a foundation, not validated pedagogical recognition. No SQ naming. The user authorized reuse, autonomous implementation, commits and push without coauthor trailers.

1. Import the three source snapshots and record provenance. → verify: compare files with downloaded snapshots, run each upstream suite.
2. Connect web uploads to whole-file local speech API; preserve speaker IDs and end timestamps; show local analytics and transcript even without an LLM. Provide explicit demo mode with synthetic fixture. → verify: test adapter mapping, local pipeline success/error, no chunk transcription call, demo flow.
3. Package speech API with isolated per-request files and cleanup; provide lightweight demo backend, CPU Dockerfile and GPU Dockerfile. → verify: API tests without models, cleanup after success/failure, health readiness semantics.
4. Provide root Compose, env example, Makefile and CI. Keep ports on loopback and external providers opt-in. → verify: compose config for demo/local/GPU/cloud; all CPU suites; smoke HTTP upload/status/results.
5. Write Russian README, source inventory, materials checklist and current limitations. → verify: commands and service names match configuration; reviewer checks branch; commit and push feature branch.

Review focus: stable speakers across long recordings; local mode with missing LLM; failed speech service; source/cache deletion; no GPU available. Integration tests use fixtures and do not prove ASR quality or RTF.
