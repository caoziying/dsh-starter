# DSH Starter：解压后学习 Tool、Skill 与本地 API

适用系统：Windows x64。首次安装需要 Python 3.11–3.13、网络连接，以及一个可用的对话模型：DeepSeek API、OpenAI 兼容的学校网关，或已下载模型的 Ollama。压缩包自带经过测试的 Node 22.19.0 和 DeepSeek Harness 0.1.5-rc.2 运行时，不包含模型权重和 API Key。

## 五分钟入门

建议解压到较短路径，例如 `C:\dsh-starter`。Windows PowerShell 的 `Expand-Archive` 在包含深层 Node 模块的 ZIP 上可能出现路径错误；可使用 Windows 自带的 `tar.exe`：

```powershell
New-Item -ItemType Directory -Force C:\dsh-starter
tar.exe -xf .\dsh-starter-win-x64-<版本>.zip -C C:\dsh-starter
```

进入压缩包内的 `dsh-starter-win-x64-<版本>` 目录，再打开 PowerShell：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1 -Provider DeepSeek
notepad .\harness\config\secrets.env
powershell -NoProfile -ExecutionPolicy Bypass -File .\doctor.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\start.ps1
```

在 `secrets.env` 中填写 `DEEPSEEK_API_KEY`。启动命令会打印带本地访问 token 的网页地址。学校网关使用 `setup.ps1 -Provider School -Model <模型名>`，填写 `SCHOOL_API_KEY` 和 `SCHOOL_BASE_URL`。本地 Ollama 使用 `setup.ps1 -Provider Ollama -Model <已安装模型名>`，无需 API Key；它需要先在 Ollama 中下载模型。

在对话框依次尝试：

1. `运行 harness-probe skill`。成功时只返回 `SKILL_MCP_OK`。
2. `请用 protein-sequence-summary skill 分析序列 ACDEFGHIKLMNPQRSTVWY`。
3. 联网时尝试：`请分析 UniProt A5PLL7 的序列长度与氨基酸组成`。

不调用对话模型的本地自检（`start.ps1` 启动后）：

```powershell
.\harness\.venv\Scripts\python.exe -m unittest discover -s .\tests -p test_local.py -v
.\harness\.venv\Scripts\python.exe .\tests\smoke_mcp.py
.\harness\.venv\Scripts\python.exe .\tests\smoke_mcp.py --online  # 另测 UniProt
```

结束后执行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\stop.ps1
```

## 学习路线

| 入口 | 学到什么 |
|---|---|
| `harness/tools/diagnostics/` | 最小 Python MCP Tool，理解注册与调用 |
| `harness/tools/uniprot/` | Tool 请求公开 HTTP API，处理参数和错误 |
| `services/sequence_demo/app.py` | 独立 FastAPI 服务与 `/readyz`、`/analyze` |
| `harness/tools/sequence/` | MCP Tool 如何通过 HTTP 调用本地服务 |
| `harness/skills/` | Skill 如何组织多个 Tool 的调用顺序 |
| `lessons/` | 跟做教程和真实 MGCA 接入示例 |

完整目录及开发步骤见 [PROJECT_GUIDE.md](PROJECT_GUIDE.md)。本包的序列分析只计算确定性的长度和氨基酸组成，不进行药物活性或临床预测。

## 出错时

先运行 `doctor.ps1`。服务日志位于 `harness/logs/`；注册清单位于 `harness/.runtime/generated/inventory.json`。修改 Tool manifest 或 Skill 后先停止，再重新运行 `start.ps1`。
