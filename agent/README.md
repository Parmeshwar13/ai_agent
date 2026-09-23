# Agent

Not implemented. Phase 5.

This tree is the future tool-calling agent. Phase 1 does not import it, does not call a model, and does not execute commands.

When it is built:

- The model talks to tools, not to the host filesystem.
- Every tool call is stored as an agent step.
- Runs are resumable and bounded.
- Tests are reported from command output, not from the model's claim.
- Git work happens on a task branch. `main` is not the working branch.

See `docs/architecture.md`.
