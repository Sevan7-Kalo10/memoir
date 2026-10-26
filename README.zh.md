# memoir

**面向 Claude Code 与 DeepSeek Harness agent 的记忆生命周期管理。**

内置记忆回答“这条事实要不要存”，memoir 回答“这条事实还成立吗，该长、该淡、该并，还是该退役”。

一个仓库，两种装法：Claude Code 的 skill，和带着同一份规格的 DeepSeek Harness 插件包。

## 安装

### Claude Code

```
/plugin marketplace add Sevan7-Kalo10/memoir
/plugin install memoir
```

SessionStart hook 负责加载启动文件，Stop hook 在会话收尾时提醒你做维护。把 `MEMOIR_STORE` 指向你的记忆目录。

### DeepSeek Harness

```
dsh plugin --profile web add github:Sevan7-Kalo10/memoir
```

这条注册的是 `/memoir-status`。**会话启动时不注入任何记忆上下文**——插件包不碰上下文，skill 只在被调用时读记忆。真想要启动加载，自己接，见 `references/spec-startup-ritual.md`。

skill 本身从文件系统发现，不看包里的清单（当前版本的 `dsh.skills` 没有消费方），所以还要链一次：

```
ln -s "$DSH_HOME/profiles/web/node_modules/dsh-memoir" "$DSH_HOME/skills/memoir"
```

```powershell
New-Item -ItemType SymbolicLink -Path "$env:USERPROFILE\.dsh\skills\memoir" `
  -Target "$env:USERPROFILE\.dsh\profiles\web\node_modules\dsh-memoir"
```

也可以只作用于单个项目：链进 `<项目>/.dsh/skills/memoir`。

<details>
<summary>手动安装（不用插件系统）</summary>

```
git clone https://github.com/Sevan7-Kalo10/memoir.git
```

把仓库目录复制或链接到 `~/.claude/skills/memoir/`。

</details>

## 它做什么

memoir 用一个问题把记忆切成两层：**半年后这条还重要吗？**

- **热层**（`HOT-MEMORY.md`，约 2000 token）：最近发生的事、在跑的项目、当前的行为准则。每次会话收尾重写，回答“醒来时我需要知道什么”。
- **冷层**（`memory/*.md`）：关于这个人的永久洞察——身份、价值观、偏好、行为模式。判据不是“我们聊过”，而是“这条揭示了他是什么样的人”。

每条记忆带两根独立的轴——**重要度**（1–5）和**新鲜度**——外加一个寿命态：

```
seedling → active → stable → fading → archived
               ↑                      |
               |______ restore _______|
```

引擎是会话收尾流程：更新热层，从对话里挑出值得永久保留的洞察，跑维护（衰减、合并提案、归档候选），查缺口，备份。agent 只提案，由人确认。

行为纠正（“别做 X”“以后都 Y”）写成结构化的 feedback 文件：事件、根因、改法、怎么套用。重要度永远是 5。

## v2.1 新增

- **`references/spec-migration.md`**——v0.1.x 到 v2 的 frontmatter 迁移规格。仓库从 2.0.0 起就一直链着它，但文件根本不存在。里面有字段映射和两个让老库存迁不动的坑：`metadata.type` 不等于 `layer`，文件 mtime 是批量写入的痕迹。
- **按日期触发的维护**——一枚“上次维护”的日期戳比数会话可靠。记忆库可能几个月没有会话，也可能一天开十次。
- **DeepSeek Harness 插件包**——同一份规格，加一个 `/memoir-status` 命令。
- **我们真正在跑的脚本**——`memoir_due.py`（会话启动查维护是否超期）、`memoir_maintain.py`（出提案，`--apply` 只写寿命态转移）、`memoir_index.py`（重建 MEMORY.md 索引）、`memoir_recall.py`（可选的召回 hook）。只用 Python 标准库。

## 命令

| 命令 | 用途 |
|------|------|
| `/memoir:init` | 带引导问题地初始化记忆目录 |
| `/memoir:status` | 健康检查：token 预算、陈旧度、域计数 |
| `/memoir:remember <fact>` | 带引导 frontmatter 地新建一条记忆 |
| `/memoir:digest` | 执行会话收尾流程 |
| `/memoir:maintain` | 衰减、合并、归档提案 |
| `/memoir:audit` | 缺口分析：聊过的话题 vs 存下的记忆 |
| `/memoir:archive <file>` | 把记忆移进归档 |
| `/memoir:restore <file>` | 从归档恢复 |
| `/memoir:merge <f1> <f2>` | 合并两条相关记忆 |

在 DeepSeek Harness 上，斜杠命令来自 skill 正文（agent 读 SKILL.md）；`/memoir-status` 另外由插件包原生注册。

## 目录

| 路径 | 用途 |
|------|------|
| `SKILL.md` | skill 本体：模型、工作流、触发器 |
| `references/` | 按需加载的规格：模型、摄入、维护、迁移、启动仪式 |
| `templates/` | 空白热记忆、冷记忆、feedback 文件、触发器 |
| `hooks/` | Claude Code 的 SessionStart（启动文件 + 查维护期）/ Stop hook |
| `scripts/` | 工具：查期、维护提案、重建索引、可选召回 |
| `lib/index.js` | DeepSeek Harness 插件包：`/memoir-status` |

## 设计缘由

memoir 为什么是 skill 而不是 Python CLI、v0.1.x 错在哪、这些模式真正从哪来：[docs/design-rationale.md](docs/design-rationale.md)。
