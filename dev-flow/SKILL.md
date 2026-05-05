---
name: dev-flow
description: Development workflow — manage ideas, requirements, tech specs, issues, and sprint planning
user-invocable: true
argument-hint: "command: idea | requirement | tech-spec | issue | sprint | help"
---

## 首次使用

如果还不知道用户的计划仓库是哪个，先问用户：

> "就是用这个仓库来跟踪开发讨论和计划的吗？还是另有其他仓库？"

确认后，建议用户把 `Plan repo: <owner>/<repo>` 保存在用户级或项目级的配置中，以便后续的会话和 agent 都能使用这个配置。

## Development Workflow

### Flow

```
💡 Ideas（随意记录）
    ↓ 整理筛选
📋 Requirements（PRD + 用户故事）
    ↓ 确认 → Project board item (自动转为 plan repo issue 去除 Draft 标识)
🏗️ Tech Spec（评估方案，需要时才写）
```

- **User Story** → Project board 创建 draft item → 立即 Convert to issue（去 Draft 标识）。issue 落在 plan repo 的 Issues tab，但你只看 board 不看 Issues tab
- **Bug** → 直接在 plan repo 创建 GitHub Issue（不走 board）
- **核心原则**：Issues tab 是存储层，Project board 是视图层。User Story 以 board 上的卡片为准

### Repo Convention

- **Code repo** — 只放代码，保持干净，对外可见时可公开
- **Plan repo**（由用户配置） — Discussions + Issues（仅 bug）+ Project board

### Discussion Category 选择规则

创建 Discussion 时按优先级选择 category，不存在则 fallback：

| 用途 | 首选 category | Fallback |
|------|--------------|----------|
| 💡 Ideas | `Ideas` | —（一定存在） |
| 📋 Requirements | `Requirements` | `Show and tell` |
| 🏗️ Tech Spec | `Tech Spec` | `General` |

实现方式：
- 先通过 GraphQL 查询仓库的 `discussionCategories` 列表获取 slug 列表
- 检查首选 slug 是否存在，存在则用它，否则用 fallback
- 注意 category slug 是自动生成的：`Requirements` → `requirements`，`Tech Spec` → `tech-spec`

### Commands

#### 💡 idea — 记录新想法
- 在计划仓库的 Discussions 的 Ideas 分类下开 Discussion
- 随意记录，不需要格式

用法：你说"有个想法"或 "/dev-flow idea"，我会先确认你想的是什么，然后记下来。

#### 📋 requirement — 想法转需求
- 从已有的 Ideas Discussion 提取内容，写成 PRD + 用户故事
- 在 Requirements 分类下开新的 Discussion（按上面的类别选择规则，不存在则用 Show and tell）
- 每个用户故事包含验收条件

用法：你说"帮我把那个想法整理成需求"或 "/dev-flow requirement <想法标题>"。

#### 🏗️ tech-spec — 技术评估
- 分析需求的影响范围、实现方案、排期估算
- 在 Tech Spec 分类下开 Discussion（按上面的类别选择规则，不存在则用 General）
- 不是每个需求都需要，方案不明确或需要决策时才写

用法：你说"评估下这个怎么实现"或 "/dev-flow tech-spec <需求标题>"。

#### 📋 issue — 需求转 Project board
- 把定稿的需求（Requirements Discussion）中的每个用户故事转为 Project board item
- 使用 `scripts/setup_sprint.py` 创建 draft → 自动 Convert to issue（去 Draft 标识）
- issue 落在 plan repo 的 Issues tab，但你只需看 board

用法：你说"把这些需求加到看板"或 "/dev-flow issue <需求标题>"。

#### 🗺️ sprint — 启动迭代
- 创建新的 Project board（一次迭代一个）
- 使用 `scripts/setup_sprint.py <project_id> '<items>' --repo-id <repo_id>` 完成初始化

用法：你说"开始新迭代"或 "/dev-flow sprint"。

#### ℹ️ help — 查看流程说明和可用命令
- 输出这个工作流概览

### 关键规则

- 一个 Project board item = 一个用户故事
- Bug 才创建 GitHub Issue
- User Story 不需要经 tech-spec 才能转 issue，简单需求可以直接转
- Tech Spec 只在方案不明确或需要决策时写

### 复用脚本

技能目录下的 `scripts/setup_sprint.py` 封装了 Project board 初始化的完整流程：

```bash
python3 scripts/setup_sprint.py <project_id> '<items_json>'
```

脚本会自动创建 Priority / Estimate 字段（跳过默认的 Status），创建 draft items 并设好字段值。

### 已知坑 (GitHub Projects V2 API)

1. **Status 是默认字段** — 每个 Project board 自动带一个 Status 字段（Todo/In Progress/Done），不能手动创建
2. **singleSelectOptions 需要 description** — GitHub API 要求每个选项必须有 description 字段（可传空字符串）
3. **createProjectV2Field 返回 projectV2Field** — 不是 `field`
4. **DraftIssue 的判断** — 它的 `content.__typename == "DraftIssue"`，不是 null
5. **convertProjectV2DraftIssueItemToIssue** — 返回字段名是 `clientMutationId`，不是 `issue`
6. **token 权限** — Fine-grained token 必须有 `project` scope（read/write），否则 query/mutation 会失败
7. **Claude Code 权限** — 需要 `Bash(gh *)` 才能通过 Claude 执行 gh 命令
8. **字符串拼接** — 用 Python subprocess 比 shell 拼接安全（避免引号转义）
