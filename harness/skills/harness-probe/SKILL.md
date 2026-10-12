---
name: harness-probe
description: Verify that DeepSeek Harness can load a local Skill and invoke a Python MCP Tool.
---

# Harness probe

When the user explicitly requests the harness probe:

1. Call `mcp__diagnostics__probe_echo` exactly once with `text` set to `SKILL_MCP_OK`.
2. Check that `source` is `python-mcp` and `echo` is `SKILL_MCP_OK`.
3. Reply with exactly `SKILL_MCP_OK`.
