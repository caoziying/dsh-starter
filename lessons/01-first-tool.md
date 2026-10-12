# 练习 1：一个最小 Tool

先阅读 `harness/tools/diagnostics/tool.json`。其中 `server_name` 决定 DSH 中的前缀；`entry` 指向运行 MCP server 的 `server.py`；`tools` 列出给学习者看的函数。启动器把这个目录注册为 `mcp__diagnostics__probe_echo`。

再阅读 `server.py` 的 `@mcp.tool()`、参数类型、docstring 与返回字典。运行 `harness-probe` Skill，观察 DSH 页面中的 Skill 加载和 Tool 调用事件。

练习：复制该目录为 `tools/hello/`，修改 `id`、`server_name` 和函数名，重启后在 `harness/.runtime/generated/inventory.json` 中检查是否出现新服务。复制目录时不要保留相同的 `id` 或 `server_name`。
