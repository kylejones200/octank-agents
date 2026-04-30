# Optional — copy to `integrations.local.md` (gitignored)

Use this when you do not want machine-specific paths in `AVAILABLE_DATA.md`, or
when they differ per developer. Agents read `integrations.local.md` **when it
exists**, before relying only on the catalog text.

## Workplace-text / sentiment

- **Path on disk:** `/Users/kylejonespatricia/Desktop/sentiment`
- **Role:** workplace-text analysis (tone, team-level signals, etc.) — sibling to
  this agent pack, not imported as a submodule here.

When session context includes outputs from that tool, cite them; otherwise do
not claim they were run.
