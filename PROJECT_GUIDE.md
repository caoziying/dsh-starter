# 项目架构与二次开发

```text
用户 → DSH Web → 模型 → Skill → MCP Tool → 本地 FastAPI / 公开 UniProt API
```

Tool 是模型可以调用的有参函数。Skill 是模型按需读取的操作说明。本地 FastAPI 是独立进程，MCP Tool 通过 HTTP 请求它；服务实现与 Harness 保持分离。DSH 的启动器扫描 `harness/tools/*/tool.json` 和 `harness/skills/*/SKILL.md`，生成注册补丁与清单。

```text
dsh-starter/
├── setup.ps1 / doctor.ps1 / start.ps1 / stop.ps1
├── harness/
│   ├── launcher.py               # DSH 注册、模型路由、进程启停
│   ├── config/                  # provider.json、secrets.env、系统提示词
│   ├── tools/                   # 三个 MCP 服务
│   ├── skills/                  # 两个 Skill
│   ├── .runtime/node/           # 便携 Node（构建时复制）
│   └── .runtime/packages/       # 固定版本 DSH（构建时复制）
├── services/sequence_demo/     # 无模型权重的 FastAPI 示例
├── lessons/                    # 跟做教程与 MGCA 进阶示例
└── tests/                      # 本地自动化验收
```

## 三个 Tool

| MCP 名称 | 函数 | 来源 | 前提 |
|---|---|---|---|
| `diagnostics` | `probe_echo(text)` | 包内纯 Python 示例 | 无 |
| `uniprot` | `uniprot_get_fasta(entry)` | UniProt REST `uniprotkb/<entry>.fasta` | 联网 |
| `sequence` | `sequence_analyze(sequence)` | 包内 FastAPI `/analyze` | 启动 `start.ps1` |

`tool.json` 是注册清单；`server.py` 是真正的 MCP 实现。`tool.zh-CN.json` 只供阅读，不加载。新手可复制 `diagnostics` 目录，改 `id`、`server_name`、入口和函数，再运行 `start.ps1`。函数应有类型标注、明确的 docstring、输入校验和可读的失败信息。

## 两个 Skill

`harness-probe` 演示最小的 Skill → Tool 调用。`protein-sequence-summary` 演示根据用户输入选择工具：给 UniProt ID 时先获取 FASTA；给原始序列时直接调用本地分析 Tool；最后报告来源、长度及主要氨基酸组成。`SKILL.md` 的 frontmatter 中 `name` 必须等于目录名。`SKILL.zh-CN.md` 是不加载的中文对照。

## 本地服务如何接入

`services/sequence_demo/app.py` 用 FastAPI 提供 `GET /readyz` 和 `POST /analyze`。`start.ps1` 先启动它，再启动 DSH。`harness/tools/sequence/server.py` 只负责请求这个 API，不在 Tool 进程中实现分析算法。修改为真实模型时，先在服务进程加载权重和预热，再保持 Tool 的 HTTP 调用边界。参见 [MGCA 接入教程](lessons/03-mgca-integration.md)。

## 模型与密钥

`setup.ps1 -Provider DeepSeek` 使用官方兼容接口；`-Provider School -Model ...` 使用学校网关；`-Provider Ollama -Model ...` 使用本地已安装模型。选择结果写入 `harness/config/provider.json`，密钥只放 `harness/config/secrets.env` 或进程环境变量。所有运行态、密钥、日志和结果都被 `.gitignore` 排除。压缩包内只有 `secrets.env.example`。

修改示例并验证后，可在解压目录运行 `build_starter.ps1` 重新生成 ZIP；产物写入 `dist/`。构建脚本按白名单复制源码和便携运行时，不会复制虚拟环境、密钥、配置选择、日志或结果。

## 验收

构建脚本只收集白名单文件，写入 `MANIFEST.sha256` 和 ZIP SHA256。验收须在与源码不同的目录解压，检查 `doctor.ps1`、服务 `/readyz`、三个 Tool 的注册、两个 Skill 的发现，并执行 `tests/smoke_mcp.py`；再在已配置模型的情况下从网页完成上述两条对话。没有模型或密钥时，确定性本地测试仍可运行，网页对话不能完成。包含深层 Node 模块的 ZIP 建议用 Windows 自带 `tar.exe` 解压到短路径。

## 来源

- DeepSeek Harness：<https://github.com/deepseek-ai/deepseek-harness>；运行时固定为 `0.1.5-rc.2`。
- UniProt REST：<https://rest.uniprot.org/>。
- FastAPI：<https://fastapi.tiangolo.com/>。
- 真实 MGCA 示例来自项目作者提供的冻结模型包，权重不包含在本教学包。

重新分发时应保留 `licenses/` 中的来源和许可说明，并核对运行时依赖的第三方许可。
