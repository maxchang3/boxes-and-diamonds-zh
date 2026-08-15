# B&D 组装器工作说明

本仓库只负责《盒子与钻石》中文版的组装、构建和发行；正文翻译、共享术语和翻译 worker 规范属于兄弟仓库 `../OpenLogic-Zh/`，从其 `.agents/translation/` 入口读取。

保持两个仓库并排，`\olpath` 固定指向 `../OpenLogic-Zh`。中文正文构建使用 `make zh`、`make zh-print`，`make check` 同时做中文构建和英文回归；`make screen` 只用于本地英文对照，不作为中文 release 产物。

封面肖像由 `scripts/fetch-portraits.sh` 按需从官方 portraits 仓库下载，资产不提交 Git；构建产物、版本和 release-please 配置属于本仓库，不能把这些下游事实写回 OpenLogic-Zh 的正文规范。

改动共享 TeX 前确认英文驱动仍能由 pdfLaTeX 构建，中文专属文字必须位于语言分支；同步上游或发布前先查看本仓库 diff 和 `make check` 结果，不擅自修改 remote、分支或推送。
