# Documentation index

| Doc | Description |
|---|---|
| [Architecture](architecture/ARCHITECTURE.md) | Layers, data flows, bootstrap phases, spec index |
| [Agent registry (human)](AGENT_REGISTRY.md) | Role catalog; canonical JSON is [`../registry/registry.json`](../registry/registry.json) |
| [Message schema](specs/MESSAGE_SCHEMA.md) | Inter-agent envelopes and payloads |
| [Org state](specs/ORG_STATE.md) | Live organizational memory spec |
| [Constraint engine](specs/CONSTRAINT_ENGINE.md) | Rule types, evaluation, audit |
| [Exception queue](specs/EXCEPTION_QUEUE.md) | Human exception interface |
| [Prompt templates](specs/PROMPT_TEMPLATES.md) | Bootstrap LLM prompts for SKILL / WORKFLOW / AGENT |
| [Archive: concept chat](archive/concept-chat-bootstrap.md) | Historical brainstorm; not maintained |
| [Corpus → tasks](../corpus/CORPUS_TO_TASKS.md) | Optional pipeline: email corpus to JSONL tasks |
| [Integrations example](../learning/integrations.local.example.md) | Optional machine-specific paths (e.g. sentiment tool); copy to `integrations.local.md` (gitignored) |

Constraint **artifacts** (rule files) live under [`../constraints/`](../constraints/) at repo root.
