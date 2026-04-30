# octank-agents

Spec-first **digital org** pack: AI agent roles (`roles/`), workflows (`workflows/`), and a validated [`registry/registry.json`](registry/registry.json).

## Quick start

```bash
python3 scripts/validate_registry.py
```

Optional: `pip install pre-commit && pre-commit install`, then commits run the same validator.

Smoke test (corpus paths must exist per `enron/corpus_config.json`):

```bash
./scripts/smoke_pipeline.sh
```

## Where to read

1. **[docs/architecture/ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md)** — system shape and spec index  
2. **[docs/AGENT_REGISTRY.md](docs/AGENT_REGISTRY.md)** — who exists and what files they load  
3. **[learning/AVAILABLE_DATA.md](learning/AVAILABLE_DATA.md)** — optional corpus / learning pipeline  

Commands and pipelines: **[scripts/README.md](scripts/README.md)**. Full doc list: **[docs/README.md](docs/README.md)**.

## Repository layout

| Area | Contents |
|---|---|
| `docs/` | Architecture + normative specs |
| `roles/`, `workflows/` | Agent and workflow markdown |
| `registry/` | `registry.json` + JSON Schema |
| `constraints/` | Stub for future rule packs (see `constraints/README.md`) |
| `enron/`, `learning/` | Corpus config, learning manifests (generated files gitignored) |
| `scripts/` | Validation, corpus helpers, hooks |
