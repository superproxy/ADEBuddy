目前加入 ACP 生态的成员包括：

IDE 端：JetBrains 全家桶、Zed 等。
Agent 端：Claude Code、Codex、Gemini CLI、Kimi CLI、Qoder CLI 等。


ACP 底层基于 JSON-RPC 2.0 协议（与 LSP 完全相同），Agent 作为 Server 运行一个独立的进程，IDE 通过 stdin/stdout 与之通信。好处是 Agent 不需要被打包进 IDE 插件里，保持独立性和可维护性。

ACP Agent Process

IDE (ACP Client)

stdin/stdout
JSON-RPC

ACP Server
JSON-RPC

AI Backend
(Claude/GPT/...)

MCP Tools
Filesystem/Git/...

AI Assistant
Plugin



####安装
要在 IDEA 里用 ACP 接入 Claude Code，需要满足：

IDE 版本：IntelliJ IDEA 2024.2 到 2025.3.x 或更高版本。ACP 支持从 2025 年底开始逐步集成，确保你的 IDEA 已更新到支持 ACP 的构建。
AI Assistant 插件：确保已安装并启用
Claude Code：已安装并能正常运行
claude-code-acp：Zed 提供的 ACP 适配器（下文会讲如何安装）
你可以检查 AI Assistant 插件版本，在 File > Settings > Plugins 里搜索 "JetBrains AI Assistant"，确认版本号在 2025.12 之后。

https://www.toutiao.com/article/7600407886539326003/?wid=1781145910987

