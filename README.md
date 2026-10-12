# DSH Starter

一个用于学习 DeepSeek Harness 二次开发的 Windows x64 示例项目：从对话框调用 Skill、MCP Tool，再调用公开 API 或本地 FastAPI 服务。项目提供 3 个 Tool、2 个 Skill 和一个无需模型权重的序列分析服务。

```text
用户 → DSH Web → 对话模型 → Skill → MCP Tool → 公开 API / 本地 FastAPI
```

## 从哪里开始

| 你的目标 | 入口 |
|---|---|
| 解压后运行和体验 | 下载仓库 **Releases** 中的 `dsh-starter-win-x64-*.zip`，按 [快速入门](README_FIRST.md) 操作 |
| 阅读源码、开发 Tool 或 Skill | 从本仓库的 [项目架构与开发指南](PROJECT_GUIDE.md) 开始 |
| 按步骤学习 | 阅读 [`lessons/`](lessons/) |

**Git 仓库保存教学源码，不包含便携 Node/DSH 运行时。** 因此直接克隆本仓库后，不能只运行 `start.ps1` 就启动 DSH。Release ZIP 包含经过测试的 Node 22.19.0 与 DeepSeek Harness 0.1.5-rc.2 运行时；首次配置仍需 Windows x64、Python 3.11–3.13、网络连接，以及 DeepSeek API、学校兼容网关或已下载模型的 Ollama。ZIP 不包含 API Key 和模型权重。

## 项目内容

| 路径 | 用途 |
|---|---|
| `harness/tools/diagnostics/` | 最小 MCP Tool，演示工具注册与调用 |
| `harness/tools/uniprot/` | 从 UniProt 公开 API 获取 FASTA |
| `services/sequence_demo/` | FastAPI 示例服务，提供 `/readyz` 和 `/analyze` |
| `harness/tools/sequence/` | 通过 HTTP 调用上述本地服务的 MCP Tool |
| `harness/skills/harness-probe/` | 最小 Skill → Tool 示例 |
| `harness/skills/protein-sequence-summary/` | 组合 FASTA 获取与序列分析的 Skill |
| `tests/` | 本地测试与 MCP 冒烟检查 |

## 运行发行包

下载并解压 Release ZIP，进入其中的项目目录，在 PowerShell 中执行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1 -Provider DeepSeek
notepad .\harness\config\secrets.env
powershell -NoProfile -ExecutionPolicy Bypass -File .\doctor.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\start.ps1
```

在 `secrets.env` 中填写自己的 `DEEPSEEK_API_KEY`。学校网关和 Ollama 的配置方法见[快速入门](README_FIRST.md)。停止服务时运行 `powershell -NoProfile -ExecutionPolicy Bypass -File .\stop.ps1`。

## 开发与安全

新增 Tool 时参考 `harness/tools/diagnostics/`，新增 Skill 时参考 `harness/skills/harness-probe/`。本地 API 的接入方式见[项目架构与开发指南](PROJECT_GUIDE.md)；真实模型服务的延伸例子见 [MGCA 接入教程](lessons/03-mgca-integration.md)。

密钥保存在 `harness/config/secrets.env`，不要提交到 Git。仓库只提供 `secrets.env.example`；`.gitignore` 排除了密钥、个人模型配置、虚拟环境、运行时、日志和结果。第三方来源与许可说明见 [`licenses/UPSTREAM.md`](licenses/UPSTREAM.md)。
