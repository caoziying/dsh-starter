# 练习 2：从 FastAPI 到 Tool，再到 Skill

`services/sequence_demo/app.py` 是常驻 API 服务。它暴露 `GET /readyz` 供启动器检查，以及 `POST /analyze` 处理序列。`harness/tools/sequence/server.py` 发送 JSON 请求，并把结果返回给 DSH。`protein-sequence-summary` Skill 决定何时调用它。

启动项目后，可直接检验 API：

```powershell
Invoke-RestMethod http://127.0.0.1:8015/readyz
$body = @{sequence='ACDEFGHIKLMNPQRSTVWY'} | ConvertTo-Json
Invoke-RestMethod http://127.0.0.1:8015/analyze -Method Post -ContentType 'application/json' -Body $body
```

接着在网页输入 `请用 protein-sequence-summary skill 分析序列 ACDEFGHIKLMNPQRSTVWY`，观察相同的数据如何经过 Skill 和 MCP Tool 返回。

如果输入的是 UniProt Entry，Skill 先使用 `uniprot_get_fasta`。该 Tool 与本地 FastAPI 没有依赖关系，展示了调用公开网络服务的另一种 Tool 来源。网络不可用时可以直接输入原始序列完成本地练习。

改造练习：给 FastAPI 添加一个新统计字段，并在 Tool 的说明及 Skill 中解释该字段。验证 API 单独运行、Tool 调用和网页对话三个层次。
