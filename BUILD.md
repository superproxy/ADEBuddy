# AgentBuddy 构建指南

## 快速构建（推荐）

```bash
# macOS / Linux
./build.sh --windowed --clean

# Windows
build.cmd --windowed --clean
```

## 构建流程

`build.sh` / `build.cmd` 自动完成 4 步：

1. **前端构建**：`cd frontend && npm run build-only` -> 产出 `tools/dist-ui/`
2. **Python 依赖检查**：自动安装缺失的 flask/pyyaml/requests/pywebview/pyinstaller
3. **PyInstaller 打包**：`python build.py` -> 产出 `dist/AgentBuddy/`
4. **验证**：确认前端产物（dist-ui/index.html）已进 bundle

## 参数

| 参数 | 说明 |
|---|---|
| `--windowed` | 无控制台（macOS 生成 .app / Windows 无黑框） |
| `--clean` | 构建前清理 dist/ build/ |
| `--no-frontend` | 跳过前端构建（使用已有 tools/dist-ui） |
| `--no-verify` | 跳过密钥泄漏扫描（不推荐） |

## 开发模式

```bash
# 前端热更新（5173）+ 后端 Flask（5050）
cd frontend && npm run dev        # 终端 1
./run.sh --no-webview             # 终端 2，浏览器开 http://127.0.0.1:5173
```

## 生产模式

```bash
cd frontend && npm run build-only  # 构建前端
./run.sh                           # pywebview 加载 tools/dist-ui
```

## 文件结构

```
frontend/               # Vue 3 + Vite 工程（开发/构建用，不打包）
  src/                  #   SFC 组件 + stores + api
  dist-ui -> ../tools/  #   构建产物输出到 tools/dist-ui/

tools/
  config_ui.html        # 旧版 UI（/old 路由备用）
  dist-ui/              # Vue 3 构建产物（Flask 根路由 serve）
  config_server.py      # Flask 后端
  static/               # 旧版 Vue/Tailwind 运行时（兼容期保留）

scripts/
  agentctl.py           # CLI 入口（sync/generate/env）
  lib/                  #   llm/mcp/skills/plugins/ide 模块

app.py                  # pywebview 桌面启动器
app.spec                # PyInstaller 打包配置
build.sh / build.cmd    # 一键构建脚本
run.sh / run.cmd        # 一键启动脚本
```
