# 进阶：把真实 MGCA 模型接入相同架构

本目录仅提供接入说明；教学包不包含 MGCA/ESM2 权重、ZINC 数据、ADMET 权重或计算环境。真实模型需要授权获取其权重并单独安装依赖。

原项目的 `mgca/app.py` 是 FastAPI/ASGI 入口，调用冻结目录中的 MGCA API 和推理引擎，并挂载 Morgan 预计算分块路由。原项目的 `deepseek-harness/tools/koff/server.py` 是 MCP 适配器，通过 HTTP 调用 MGCA 服务；`koff-batch-screening/SKILL.md` 描述何时获取 UniProt FASTA、检查服务状态、选用单分子或批量筛选工具。

按下面顺序改造本教学包：

1. 把模型服务独立放到 `services/<model_name>/`，提供 `/readyz` 和有明确输入输出 schema 的 `/predict`。在服务启动时加载权重并完成预热；`/readyz` 只有准备好时才返回 ready。
2. 用命令行单独启动服务，并直接调用 HTTP API 验证数值、错误状态和耗时。服务日志与请求 ID 要能关联。
3. 复制 `harness/tools/sequence/`，改为调用 `/predict`。在 `tool.json` 中使用独立 `id` 和 `server_name`，在 MCP 函数中处理超时及 API 错误。
4. 增加 `harness/skills/<workflow>/SKILL.md`，规定输入准备、服务就绪检查、工具选择、输出解释和限制。
5. 运行 `start.ps1`，先看 `inventory.json`，再从对话框调用 Skill 与 Tool。结果应标记为模型预测，不能与实测值混淆。

这个分层同样适用于图像模型、数据库、检索服务或其他本地推理任务。
