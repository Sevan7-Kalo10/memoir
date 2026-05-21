[English](README.en.md) | 中文

# ksteam-memoir

**让 AI 拥有会演化的记忆。**

memoir 不是一个记忆数据库。它是一套记忆的生命周期——出生、成长、触发、衰减、归档。不是"存起来以后搜"，是"该醒的时候自己醒"。

## 核心理念

传统记忆系统（RAG、向量库）是检索优先：你问 → 我搜 → 返回片段。
memoir 是演化优先：记忆有呼吸。权重升了沉了、话题滑进来域跟着亮灯、低权重自己归档。

```
memoir 记住的不是"内容"，是"时间线上发生过的事"。
```

## 当前状态（2026-05-21 v0.1.4）

**能开箱即用的：**

| 平台 | 集成方式 | 状态 |
|------|---------|------|
| Claude Code | 丢进项目文件夹 → AI 读一次 CLAUDE.md 就知道怎么用 | 完整可用 |
| Python API | `pip install ksteam-memoir` → `build_load_plan()` → 贴进 system prompt | 完整可用 |
| CLI | `memoir create/load/search/maintain` 全套命令 | 可用（Windows cmd 有限制，见下） |

**已知局限（诚实地说）：**

- **Windows cmd 下 `memoir create` 不可用。** 中文参数截断 + rich 交互提示编码崩溃。绕过：PowerShell 正常；或手动创建 .md 文件 → `memoir append` 补充内容。
- **tags 只是标签，不自动生成触发规则。** 用户在 frontmatter 写 `tags: [哲学, 加缪]`，不代表说"加缪"时会触发这条记忆。trigger 表需要手工维护。
- **`memoir create` 后 MEMORY.md 索引自动更新已修（v0.1.4），但只追加到 "## Other" 段。** 域索引的手工整理仍需人工。
- **DeepSeek TUI、Cline 等有 tool use 的工具：** 需要手动约定"启动时跑 memoir status / memoir load --render"。AI 不会自动知道 memoir 的存在。

**如果你只用在 Claude Code 上——memoir 现在就够用。** 其他工具的适配在看路线图走。

## 能做什么

- **个人 AI 伴侣** — 跨会话记住你的偏好、共同经历、只有你们懂的梗。不用每次都从头开始。
- **角色扮演角色** — 持续的人设层、演化的关系、选择性的记忆。
- **长期编程助手** — 记住你的代码规范、历史架构决策、以及那个"千万别碰"的模块。
- **研究/阅读伴侣** — 追踪读过的书、关联的洞见、尚未解答的问题。
- **多智能体协作** — 每个 agent 有独立记忆库，共享精炼快照而非原始上下文。

任何需要"连续性超过上下文窗口"的场景。

## 安装

```bash
pip install ksteam-memoir
```

## 快速开始（Claude Code）

```bash
cd your-project
memoir init
```

在项目的 `CLAUDE.md` 中加入：

```markdown
你使用 ksteam-memoir 管理记忆。
启动时跑 `memoir status`。用户说"加载记忆"时跑 `memoir load --render`。
对话中有值得记的内容时跑 `memoir create`。
```

然后正常跟 AI 对话——AI 读到 CLAUDE.md 后会自己判断什么时候调哪个命令。

## 命令总览

| 命令 | 做什么 |
|------|--------|
| `memoir status` | 看记忆库：多少条、权重分布、归档数 |
| `memoir create -t "标题" -w 权重 -c "内容" --tags "标签"` | 创建新记忆。先搜已有文件（续写优先） |
| `memoir append core/文件名.md -c "内容"` | 给已有记忆续写一条带时间戳的条目 |
| `memoir load --render` | 渲染当前该加载的记忆，输出直接贴进 AI 上下文 |
| `memoir search "关键词"` | FTS5 全文搜索 |
| `memoir trigger "用户说的话"` | 调试：哪些记忆会被这句话唤醒 |
| `memoir maintain --dry-run` | 预览权重衰减和归档（不修改） |
| `memoir maintain` | 执行衰减和归档 |
| `memoir archive-cmd core/旧文件.md` | 手动归档 |
| `memoir restore 旧文件.md` | 恢复归档记忆（权重自动降一级） |

## 权重体系

| weight | 含义 | 衰减规则 |
|--------|------|---------|
| 5 | 这是我的一部分 | 永不衰减 |
| 4 | 很重要 | 60天→降3 |
| 3 | 记得就行 | 30天→降2 |
| 2 | 暂时记着 | 60天→降1 |
| 1 | 快忘了 | 90天→自动归档 |

## 三层加载

1. **核心层**（always）—— core 域、w=5。永远在线。
2. **浮现层**（weight）—— w≥4 自动浮上来。人醒着时自然记得的事。
3. **潜伏层**（trigger）—— 话题滑进去才亮。不是忘了，是等人敲门。

## 路线图

| 优先级 | 项目 | 说明 |
|--------|------|------|
| 进行中 | AI_GUIDE.md | `memoir init` 时自动生成自然语言操作指南，AI 读完就知道怎么用 |
| 下一步 | MCP Server | 暴露 7 个 MCP 工具。任何支持 MCP 的工具（DSTUI、Cline）零代码接入 |
| 计划中 | 系统提示词集成 | 为无 tool use 的聊天 UI 提供静态注入方案 |
| 计划中 | CLI 完善 | 修复 Windows cmd 编码问题；tags→trigger 自动生成 |

## 竞品对比

| | memoir | RAG/向量库 | ReMe |
|---|--------|-----------|------|
| 驱动方式 | 演化驱动 | 查询驱动 | 文件驱动 |
| 记忆生命周期 | 有（衰减/归档） | 无 | 无 |
| 触发方式 | 级联唤醒 | 向量相似度 | 文件名 |
| 存储格式 | Markdown + YAML frontmatter | 向量 | Markdown |
| 接入方式 | CLI + Python API → MCP | SDK | CLI |
| 开箱即用 | 仅 Claude Code | — | — |

## 为什么叫 memoir

memoir（回忆录）不是 diary（日记）。日记是"今天发生了什么"，回忆录是"什么值得被记下来"。memoir 对待记忆的方式是回忆录式的——不是所有都留，留的要演化。

## 许可证

MIT
