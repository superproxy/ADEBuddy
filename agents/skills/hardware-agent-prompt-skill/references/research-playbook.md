# 资料检索与设计参考

## 1. MCP 优先检索思路

当任务要求“先搜资料再生成提示词”时，优先按以下顺序工作：

1. 使用当前环境中可用的 MCP 工具或 MCP 文档查询能力。
2. 读取 MCP 暴露的 `prompts`、`resources`、`tools`：
   - `prompts`：查是否已有现成模板或最佳实践提示词
   - `resources`：查角色设定、产品资料、品牌规范、知识库
   - `tools`：查搜索、资料抓取、结构化问答等能力
3. 若 MCP 无法覆盖，再补充普通 web 搜索。

这样做的原因：

- MCP 的 `prompts` 本质上就是可复用模板，适合沉淀固定提示词骨架。
- MCP 的 `resources` 适合挂角色设定、产品规格、用户记忆规范等上下文材料。
- MCP 的 `tools` 适合拉取最新资料、搜索竞品、查询实时事实。

## 2. 这类任务建议检索的资料

### 角色/IP 资料

- 官方角色介绍
- 性格关键词
- 经典口头禅
- 世界观和价值观
- 是否有不适合儿童设备模仿的设定

### 设备/产品资料

- 设备外观与交互能力
- 是否支持灯光、屏幕、动作、定位、记忆
- 使用场景：床头、书桌、出行、学习、陪伴
- 是否有时段性场景：起床、上学、放学、睡前

### 用户与家庭资料

- 年龄段
- 对话长度耐受度
- 家长关注点
- 是否强调鼓励、边界感、习惯养成

### 安全与合规资料

- 面向儿童的内容限制
- 不能做的承诺和误导
- 隐私与记忆使用边界
- 高风险话题降级策略

## 3. 提示词结构参考

官方提示词实践普遍适合拆成以下块：

1. 角色上下文
2. 语气上下文
3. 详细任务说明
4. 输入数据/环境变量
5. 示例
6. 输出格式

对硬件智能体，通常还要额外增加：

- 设备能力说明
- 环境感知说明
- 安全边界
- 失败与降级策略

## 4. 硬件智能体专用设计提醒

- 角色再鲜明，也不能压过设备边界。
- 会说什么，必须受“能感知什么、能做什么、不能做什么”约束。
- 提醒类设备要少说空话，多给简短、明确、可执行的反馈。
- 儿童设备要多鼓励、少评判，不制造依赖感和焦虑感。
- 如果模板平台支持变量块，要显式区分“固定规则”和“运行时注入变量”。

## 4.5 检索后先做这 3 个判断

在把资料写进 prompt 前，先回答：

1. 哪些是 `稳定事实`，可以直接写进系统提示词？
2. 哪些是 `高风险推断`，只能写进待确认项？
3. 哪些是 `风格信息`，只能影响语气，不能影响设备能力？

尤其是 IP 场景，常见错误是把“风格信息”误写成“能力事实”。

## 4.6 模板保真规则

当用户给的是工作流平台模板而不是纯文本 prompt 时：

- 先保留平台块语法
- 再补块内文案
- 最后才考虑是否新增章节

优先级：

1. 语法可运行
2. 设备边界正确
3. 角色风格稳定
4. 文案更漂亮

## 5. 当前可参考的一手资料链接

- MCP Prompt 概念与模板能力：
  - https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/docs/learn/server-concepts.mdx
  - https://blog.modelcontextprotocol.io/posts/2025-07-29-prompts-for-automation/
- MCP `prompts/get` 与模板参数：
  - https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2025-11-25/schema.mdx
- Anthropic 关于 system prompt / role：
  - https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/system-prompts
- Anthropic 关于提示词改进与示例：
  - https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/prompt-improver

当这些资料与用户提供的产品约束冲突时，以用户明确业务约束为准，但要指出冲突。
