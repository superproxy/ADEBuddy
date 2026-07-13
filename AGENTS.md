# AdeBuddy — Harness Engineering 入口

- **项目目标**：把 agents/ 共享配置（LLM/MCP/Skills/Rules）一键映射到多 IDE 的桌面工具
- **技术栈**：Python 3 + Flask + pywebview + PyInstaller（桌面应用）+ Vue 3 + Vite（前端）
- **主要业务流程**：配置编辑 → 生成 → 同步多 IDE

> 原 AGENTS.md（仓库级治理文档）已备份为 `AGENTS.old.md`，含业务角色路由 / Rules / MCP / Skills 矩阵。

## 文档导航

| 文档 | 内容 |
|---|---|
| [docs/project-overview.md](docs/project-overview.md) | 项目定位、项目结构、Skill 目录体系（三源）、插件导入导出 |
| [docs/build-release.md](docs/build-release.md) | 发布流程（Release）、安装更新（升级覆盖）、Windows 批处理脚本规范 |
| [docs/agent-governance.md](docs/agent-governance.md) | Agent 架构拓扑、协作流程、治理规则、FAQ/最佳实践、自我迭代、协同进度、Skill 依赖表、通信协议 |
