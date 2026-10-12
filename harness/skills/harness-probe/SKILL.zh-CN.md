---
name: harness-probe
description: 验证 Skill 加载与 Python MCP Tool 调用。
loaded: false
---

此文件只供中文阅读，不会被 Harness 加载。用户要求运行探针时，以 `SKILL_MCP_OK` 调用一次 `mcp__diagnostics__probe_echo`，核对来源与返回值，最后只回复 `SKILL_MCP_OK`。
