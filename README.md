# IDE 初始化脚本使用说明

将 `agents/` 共享配置一键映射到 Cursor / Trae 两种 IDE。

## 脚本列表

| 脚本 | 用途 | 运行方式 |
|------|------|----------|
| `scripts/init-ide.py` | 通用初始化（支持 Cursor / Trae / All） | `python scripts/init-ide.py` |
| `scripts/init-cursor.py` | 仅初始化 Cursor IDE | `python scripts/init-cursor.py` |

## 环境要求

- Python 3.10+
- Windows 系统（Junction / Symlink 依赖 Windows API）
- 以**管理员权限**运行终端（创建 Junction 需要管理员权限）

## 核心设计

`agents/rules/` 是**唯一数据源**，`.trae/rules/` 和 `.cursor/rules/` 通过 Windows Junction 指向它，修改一处自动同步。

```
agents/rules/            <-- 唯一数据源（在这里编辑）
  ├── .trae/rules/        <-- Junction（自动同步）
  └── .cursor/rules/      <-- Junction（自动同步）
```

---

## init-ide.py（通用初始化）

### 基本用法



```bash
python scripts/init-ide.py -i  trae-cn  --force

python scripts/init-ide.py -i trae-cn -t $env:USERPROFILE --force


# 初始化所有 IDE（默认）
python scripts/init-ide.py

# 仅初始化 Cursor
python scripts/init-ide.py --ide Cursor

# 仅初始化 Trae
python scripts/init-ide.py --ide Trae

# 仅初始化 Codex
python scripts/init-ide.py --ide Codex

# 仅初始化 .agent 通用目录
python scripts/init-ide.py --ide Agent

# 强制覆盖已有配置
python scripts/init-ide.py --force

# 指定目标目录
python scripts/init-ide.py --target-dir D:\my-project

# 指定源目录（agents/ 所在目录）
python scripts/init-ide.py --source-dir D:\my-project

# 源和目标分别指定
python scripts/init-ide.py --source-dir D:\my-project --target-dir C:\Users\me
```

### 参数

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--target-dir` | `-t` | 目标项目根目录（IDE 配置写入位置） | 用户主目录 |
| `--source-dir` | `-s` | 源目录（`agents/` 所在目录） | 脚本所在目录的父目录 |
| `--ide` | `-i` | 目标 IDE：`Cursor`、`Trae`、`Codex`、`Agent`、`All` | `All` |
| `--force` | `-f` | 强制覆盖已有配置 | 否 |

### 链接方式

| 目标 | 链接类型 | 源 |
|------|----------|-----|
| `.agent/rules/` | Junction（目录） | `agents/rules/` |
| `.trae/rules/` | Junction（目录） | `agents/rules/` |
| `.cursor/rules/` | Junction（目录） | `agents/rules/` |
| `.codex/rules/` | Junction（目录） | `agents/rules/` |
| `.agent/mcp.json` | Symlink/Copy（文件） | `agents/mcp/.mcp.json` |
| `.mcp.json`（Trae） | Symlink/Copy（文件） | `agents/mcp/.mcp.json` |
| `.cursor/mcp.json` | 生成文件 | `agents/mcp/mcp.json`（键名保持 `mcpServers`） |
| `.codex/config.toml` | 生成文件 | `agents/mcp/.mcp.json`（TOML 格式） |
| `.agent/skills/README.md` | 生成文件 | `agents/skills/`（技能索引） |
| `.cursor/skills/README.md` | 生成文件 | `agents/skills/`（技能索引） |
| `.codex/skills/README.md` | 生成文件 | `agents/skills/`（技能索引） |

---




### 参数

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--target-dir` | `-t` | 目标项目根目录 | 用户主目录 |
| `--skip-mcp` | — | 跳过 MCP 配置生成 | 否 |
| `--skip-rules` | — | 跳过 Rules 转换 | 否 |
| `--skip-skills` | — | 跳过 Skills 索引生成 | 否 |
| `--force` | `-f` | 强制覆盖已有 `.cursor/` 目录 | 否 |

### 功能对照

| 功能 | 源 | 目标 |
|------|-----|------|
| MCP 配置 | `agents/mcp/.mcp.json` | `.cursor/mcp.json` |
| Rules 规则 | `.trae/rules/*.md` | `.cursor/rules/*.mdc` |
| Skills 技能 | `agents/skills/*/SKILL.md` | `.cursor/skills/README.md` |

---

## 生成的目录结构

```
项目根目录/
├── agents/                        # 唯一数据源
│   ├── rules/                      # Rules（编辑这里）
│   │   ├── git-commit-message.md
│   │   ├── api/collaboration-standards.md
│   │   ├── backend/coding-standards.md
│   │   ├── backend/database-standards.md
│   │   ├── backend/ddd-standards.md
│   │   ├── design/standards.md
│   │   ├── frontend/coding-standards.md
│   │   ├── product/prd-standards.md
│   │   ├── security/standards.md
│   │   └── testing/standards.md
│   ├── mcp/.mcp.json               # MCP 源配置
│   └── skills/*/SKILL.md           # 技能定义
│
├── .trae/rules/        --Junction--> agents/rules/    （自动同步）
├── .cursor/rules/      --Junction--> agents/rules/    （自动同步）
├── .mcp.json           --Symlink---> agents/mcp/.mcp.json
├── .cursor/mcp.json                  （生成，mcpServers 键）
├── .cursor/skills/README.md          （生成，技能索引）
├── AGENTS.md                          （Trae 项目指令）
└── scripts/
    ├── init-ide.py                   （通用初始化）
    └── init-cursor.py                （Cursor 专用初始化）
```

---

## 格式差异

| 项目 | Cursor | Trae |
|------|--------|------|
| MCP 键名 | `mcpServers` | `mcpServers` |
| MCP 位置 | `.cursor/mcp.json` | `.mcp.json`（根目录） |
| Rules 目录 | `.cursor/rules/`（Junction） | `.trae/rules/`（Junction） |
| Rules 扩展名 | `.mdc` | `.md` |
| Skills | 索引文档 | `agents/skills/` 原生 |
| 项目指令 | — | `AGENTS.md` |

---

## 推荐 Skill 列表（按角色）

> 角色映射由 `skills-mapping.csv` 驱动，脚本运行时自动读取。新增/调整 Skill 只需修改 CSV 文件，无需改代码。

### CSV 配置说明

`skills-mapping.csv` 位于项目根目录，包含以下字段：

| 字段 | 说明 | 示例 |
|------|------|------|
| `skill_name` | Skill 名称（与 `agents/skills/` 目录名一致） | `drawio-skill` |
| `category` | 功能分类 | `可视化` |
| `role` | 适用角色（多个用 `\|` 分隔） | `Frontend\|Backend\|Design` |
| `description` | 功能简述 | `生成 .drawio 流程图/架构图...` |
| `trigger_keywords` | 触发关键词（多个用 `\|` 分隔） | `画图\|流程图\|架构图` |
| `installable` | 是否为通用安装型技能（`true`/`false`） | `true` |

**Skill 分类规则**：

- **内置技能**（`installable: false`）：按角色（Frontend/Backend/Design/Product）直接推荐，开箱即用
- **通用安装型技能**（`installable: true`）：不绑定特定角色，需通过 `find-skills` 安装后使用

**新增 Skill 时**：在 CSV 中追加一行即可，脚本会自动生成对应的角色映射表。

### 按角色推荐

### 前端（Frontend）

| Skill | 说明 | 触发场景 |
|-------|------|----------|
| `stitch-prototype-skill` | 使用 Stitch MCP 从文本描述生成 UI 原型 | 提到 stitch、原型图、界面生成、文生页面、交互原型 |
| `mastergo-magic-skill` | 使用 MasterGo Magic MCP 生成中保真原型和前端代码 | 提到 MasterGo、设计稿转代码、C2D、D2C |
| `drawio-skill` | 生成 .drawio 流程图、架构图、可视化图表 | 需要画模块结构图、组件关系图、界面流程图 |
| `mermaid-sequence-from-flow` | 将业务流程转为 Mermaid 序列图 | 需要画序列图、时序图、交互流程图 |

### 后端（Backend）

| Skill | 说明 | 触发场景 |
|-------|------|----------|
| `restful-api-design-skill` | RESTful API 设计、规范自检、OpenAPI 文档生成 | 设计 API 接口、接口文档、接口规范检查 |
| `task-plan-skill` | PRD/需求拆解为可执行任务计划（里程碑、依赖、风险） | 任务计划、研发排期、WBS、里程碑 |
| `drawio-skill` | 生成架构图、服务关系图、数据流图 | 需要画架构图、ER 图、服务拓扑图 |

### 设计（Design）

| Skill | 说明 | 触发场景 |
|-------|------|----------|
| `stitch-prototype-skill` | 使用 Stitch MCP 快速生成界面原型 | 需要快速出原型方案、设计迭代 |
| `mastergo-magic-skill` | MasterGo 设计稿到代码协作 | MasterGo 相关设计流程 |
| `prd-to-mastergo-interaction-skill` | 从 PRD 提炼页面与用例，生成 MasterGo 交互原型 | 根据 PRD 生成交互图、原型交互流程图 |
| `drawio-skill` | 生成用户流程图、信息架构图 | 需要画用户旅程、信息架构、页面流程图 |

### 产品（Product）

| Skill | 说明 | 触发场景 |
|-------|------|----------|
| `usecase-prd-skill` | 将需求转为基于用例的 PRD（用户动作→系统响应→验收标准） | 写需求文档、PRD、用户故事、功能拆解 |
| `task-plan-skill` | 需求拆解为任务计划与排期 | 项目计划、研发排期、里程碑 |
| `weekly-report-skill` | 周报/月报生成结构化工作汇报 | 根据周报生成报告、整理工作汇报 |
| `prd-to-mastergo-interaction-skill` | 推动需求向交互稿过渡 | PRD 转交互原型 |

### 通用安装型技能（Installable）

> 以下技能不绑定特定角色，需通过 `find-skills` 安装后使用。

| Skill | 分类 | 说明 | 触发场景 |
|-------|------|------|----------|
| `find-skills` | 技能发现 | 帮助发现和查找仓库中的 AI 技能 | 不知道有哪些技能可用、想找特定功能的技能 |
| `personnel-recruitment` | 人力资源 | 结构化招聘（JD 优化、简历筛选、面试设计、评分卡） | 招聘、岗位画像、JD 优化、简历筛选 |
| `hardware-agent-prompt-skill` | 硬件AI | 为硬件 AI 智能体生成提示词与角色设定 | 写硬件智能体提示词、设备人格设定、儿童陪伴设备话术 |
| `elon-musk-perspective` | 思维模型 | 马斯克思维模型分析（第一性原理、五步算法、白痴指数） | 成本拆解、第一性原理思考、激进迭代决策 |

---

## MCP 环境变量初始化

MCP 配置（`mcp.json`）中包含大量 API Key，不能直接提交到版本控制。通过以下机制实现密钥与配置分离：

### 文件结构

```
agents/mcp/
├── mcp-env.json           ← 本地密钥配置（不提交，已加入 .gitignore）
├── mcp-env.example.json   ← 密钥模板（可提交，供团队成员参考）
├── mcp.template.json      ← MCP 配置模板（可提交，用 ${KEY} 占位）
├── mcp.json               ← 运行时配置（由脚本生成，不提交）
├── init-mcp-env.ps1       ← Windows 初始化脚本
├── init-mcp-env.sh        ← Linux/Mac 初始化脚本
├── remove-mcp-env.ps1     ← Windows 移除脚本
└── remove-mcp-env.sh      ← Linux/Mac 移除脚本
```

### 工作流程

**团队成员首次使用：**

```powershell
# 1. 复制密钥模板并填入真实 Key
cp agents/mcp/mcp-env.example.json agents/mcp/mcp-env.json
# 编辑 mcp-env.json，填入各服务的 API Key

# 2. 运行初始化脚本
.\agents\mcp\init-mcp-env.ps1 -Scope User
```

### 脚本功能

1. 读取 `mcp-env.json` 中的密钥
2. 将密钥写入系统环境变量（支持 Process / User / Machine 三级）
3. 从 `mcp.template.json`（含 `${KEY}` 占位符）替换生成最终的 `mcp.json`

### Windows 用法

```powershell
# 写入当前用户环境变量（永久生效，推荐）
.\agents\mcp\init-mcp-env.ps1 -Scope User

# 跳过确认提示
.\agents\mcp\init-mcp-env.ps1 -Scope User -Force

# 仅当前会话（不写入系统）
.\agents\mcp\init-mcp-env.ps1

# 仅导出环境变量，不生成 mcp.json
.\agents\mcp\init-mcp-env.ps1 -Scope User -ExportOnly

# 删除已写入的环境变量
.\agents\mcp\remove-mcp-env.ps1 -Scope User
```

### Linux / Mac 用法

```bash
# 写入 shell 配置文件（永久生效）
source agents/mcp/init-mcp-env.sh --scope user

# 仅当前会话
source agents/mcp/init-mcp-env.sh

# 删除
source agents/mcp/remove-mcp-env.sh
```

### Scope 说明

| Scope | 说明 | 生命周期 |
|-------|------|----------|
| `Process` | 仅当前终端会话 | 关终端即失效 |
| `User` | 写入当前用户环境变量 | 永久，新终端自动生效 |
| `Machine` | 写入系统环境变量（需管理员） | 所有用户永久生效 |

### 密钥清单

| 变量名 | 对应 MCP 服务 |
|--------|--------------|
| `AMAP_MAPS_API_KEY` | 高德地图 |
| `WECOM_WEBHOOK_URL` | 企业微信 |
| `BOSS_COOKIE` / `BOSS_BST` | BOSS直聘 |
| `TAVILY_API_KEY` | Tavily 搜索 |
| `FIRECRAWL_API_KEY` | Firecrawl 爬虫 |
| `YUQUE_TOKEN` | 语雀 |
| `STITCH_API_KEY` | Stitch 原型 |
| `MASTERGO_MAGIC_TOKEN` | MasterGo Magic |
| `CONTEXT7_API_KEY` | Context7 文档 |

### 版本控制边界

| 文件 | 提交？ | 说明 |
|------|--------|------|
| `mcp.template.json` | 是 | 只有 `${KEY}` 占位符，无真实密钥 |
| `mcp-env.example.json` | 是 | 只有 key 名，值为空字符串 |
| `mcp-env.json` | 否 | 包含真实密钥 |
| `mcp.json` | 否 | 由脚本生成，包含真实密钥 |

---

## 常见问题

### Q: 提示 "需要管理员权限"？

Junction 创建需要管理员权限。右键终端 → "以管理员身份运行"，或使用管理员 PowerShell。

### Q: 已有配置被覆盖了怎么办？

脚本默认不覆盖已有配置。如需覆盖，使用 `--force` / `-f` 参数。

### Q: 如何只更新 Rules 不更新 MCP？

```bash
# init-ide.py 不支持跳过单项，使用 init-cursor.py
python scripts/init-cursor.py --skip-mcp --skip-skills --force
```

### Q: 修改 agents/rules/ 后需要重新运行脚本吗？

不需要。Junction 是目录链接，修改 `agents/rules/` 下的文件会自动同步到 `.trae/rules/` 和 `.cursor/rules/`。
