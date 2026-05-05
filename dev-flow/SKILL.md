---
name: dev-flow
description: Development workflow — manage ideas, requirements, tech specs, issues, and sprint planning
user-invocable: true
argument-hint: "command: idea | requirement | tech-spec | issue | sprint | help"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash(gh:*)
  - Bash(git:*)
  - Bash(python3 scripts/project.py*)
  - Bash(python3 scripts/discussion.py*)
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
📋 Requirements（PRD + 用户故事）←━━━━━━━━━━━━━━━━━━┓
    ↓ 确认                              反馈修改 ┃
🏗️ Tech Spec（评估方案，需要时才写）━━━━━━━━━━━━━━━━┛
    ↓ 确认
📦 Project board（迭代 + 任务卡片）
    ↓
🔄 BDD 测试 ← 从用户故事提取验收条件
    ↓
🔬 TDD 单元测试 ← 关键函数先写测试
    ↓
💻 开发实现
    ↓
✅ 运行全部测试（单测 → BDD 验收）
    ↓
📎 提交 + 关联卡片
```

- **Requirements ↔ Tech Spec 互相反馈修改** — Tech Spec 可能发现需求遗漏或设计不合理，需要回退修改 Requirements；反之 Requirements 变更也要同步更新 Tech Spec。通过 Discussion 评论同步，不用创建额外文档。
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
- 使用 `scripts/discussion.py` 创建：
  ```bash
  echo "正文" | python3 scripts/discussion.py create owner/repo ideas "标题"
  ```

用法：你说"有个想法"或 "/dev-flow idea"，我会先确认你想的是什么，然后记下来。

#### 📋 requirement — 想法转需求
- 从已有的 Ideas Discussion 提取内容，写成 PRD + 用户故事
- 在 Requirements 分类下开新的 Discussion（按上面的类别选择规则，不存在则用 Show and tell）
- 每个用户故事包含验收条件
- 使用 `scripts/discussion.py` 创建：
  ```bash
  python3 scripts/discussion.py create owner/repo requirements "标题" body_file.md
  ```

用法：你说"帮我把那个想法整理成需求"或 "/dev-flow requirement <想法标题>"。

#### 🏗️ tech-spec — 技术评估
- 分析需求的影响范围、实现方案、排期估算
- 在 Tech Spec 分类下开 Discussion（按上面的类别选择规则，不存在则用 General）
- 不是每个需求都需要，方案不明确或需要决策时才写
- 使用 `scripts/discussion.py` 创建：
  ```bash
  python3 scripts/discussion.py create owner/repo tech-spec "标题" body_file.md
  ```

用法：你说"评估下这个怎么实现"或 "/dev-flow tech-spec <需求标题>"。

#### 📋 issue — 需求转 Project board
- 把定稿的需求（Requirements Discussion）中的每个用户故事转为 Project board item
- 使用 `scripts/project.py` 的 setup 或 create-draft 创建 → 自动 Convert to issue（去 Draft 标识）
- issue 落在 plan repo 的 Issues tab，但你只需看 board

用法：你说"把这些需求加到看板"或 "/dev-flow issue <需求标题>"。

#### 🗺️ sprint — 启动迭代
- 创建新的 Project board（一次迭代一个）
- 使用 `scripts/project.py setup <project_id> '<items>' --repo-id <repo_id>` 完成初始化

用法：你说"开始新迭代"或 "/dev-flow sprint"。

#### ℹ️ help — 查看流程说明和可用命令
- 输出这个工作流概览

### 关键规则

- 一个 Project board item = 一个用户故事
- Bug 才创建 GitHub Issue
- User Story 不需要经 tech-spec 才能转 issue，简单需求可以直接转
- Tech Spec 只在方案不明确或需要决策时写

### 预授权工具

dev-flow 在 SKILL.md frontmatter 声明了 `allowed-tools`，限制此 skill 需要的工具范围（Read/Write/Edit/Bash 仅限于 gh、git、python3）。系统会自动放行范围内的操作，无需每次确认。

### 开发流程（BDD → TDD → 验收）

每个任务的完整周期：**BDD 验收测试 → TDD 单元测试 → 实现 → 运行全部测试 → 验收关联**

#### 1. 确认 → Project board

需求确认后：
1. 创建或复用 Sprint Project board
2. 为每个用户故事创建任务卡片（自动转为 Issue）
3. 卡片包含：用户故事标题 + 验收条件 + 参考文档链接

#### 2. 写 BDD 验收测试

基于用户故事卡片中的验收条件，先写验收测试。每个验收条件对应一条测试用例：

```text
场景: 过滤器切换
  Given 有一个包含多个 Issue 的列表
  When 用户按下 "]"
  Then 过滤器切换到 Closed
  And 列表重新加载

场景: 列表导航
  Given 有 3 条 Issue
  When 用户按下 "j"
  Then 光标移动到第 2 条
  When 用户按下 "k"
  Then 光标回到第 1 条
```

规范：
- 每个验收条件一条测试用例（直接引用 Issue 中的 AC 编号）
- 模拟用户交互（按键输入），断言系统状态变化
- **默认 mock 外部依赖** — 数据直接注入，不调真实网络/API

如果真实外部环境可以清理且限制不大，也可以用真实数据做验收测试。两种方式看场景选择，核心原则是测试可重复、可自动化。

#### 3. TDD（先写单元测试再实现）

对关键的内部函数或模块，先写单元测试再实现：

```text
函数: formatRelativeTime
  - 刚刚 → "now"
  - 5 分钟前 → "5m ago"
  - 2 天前 → "2d ago"
  - 未来时间 → "now" (边界)

函数: truncateText
  - 短文本 → 原样返回
  - 超长文本 → 截断加省略号
  - max <= 0 → 返回空
```

原则：
- 内部关键逻辑先写测试再实现
- 覆盖边界值：空输入、负数、极大值
- 单元测试和 BDD 测试都通过后，功能才算完成

#### 4. 开始实现

写代码让所有测试通过。

#### 5. 运行全部测试

```bash
# Go
go test ./... -v
go test ./module/ -v -run TestIssueFilter

# Rust
cargo test
cargo test test_issue_filter

# JavaScript / TypeScript
npm test
npx jest --testNamePattern="IssueFilter"

# Python
pytest
pytest -k "test_issue_filter"
```

不同语言替换为相应的测试命令，全绿才能验收。测试框架不限，核心是自动化、可重复。

#### 6. 迭代中修正测试

如果实现过程中发现测试有问题，测试也要一起改：

- **验收条件不变，测试有 bug** → 修测试
- **验收条件变了** → 先更新 Issue 卡片中的用户故事和 AC，再更新测试
- **新增分支场景** → 追加新用例，不修改已有断言

不要把过时的测试留在那里，也不要不准确的测试强行通过。

#### 7. 提交 + 关联卡片

```bash
git commit -m "feat: US-XX #N 功能描述" && \
  SHA=$(git rev-parse HEAD) && \
  python3 scripts/project.py move <project-id> <item-id> "Done" --commit "$SHA"
```

### 提交规范

每次提交必须关联 Issue，确保 GitHub 自动链接 commit 和卡片：

1. **Commit message 包含 `#N`** — 在 commit message 中添加对应 Issue 编号（如 `#3`），GitHub 自动将 commit 链接到该 Issue
2. **Move 到 Done 时 `--commit`**：
   ```bash
   python3 scripts/project.py move <project-id> <item-id> "Done" --commit "$SHA"
   ```
3. **约定**：
   - Commit 标题格式：`<type>: US-XX #N <描述>`（如 `feat: US-07 #9 issue list view`）
   - Move 脚本自动在 Issue 上添加评论：`✅ 已实现 (Done) + commit URL`

### 脚本设计原则

1. **不重复 `gh` 已有的能力。** Issue CRUD、PR、label 管理直接用 `gh` 命令，脚本只解决 `gh` 原生不支持的场景（Discussion、Project board、批量操作）。
2. **GraphQL wrapper 必须有错误检查。** 每次 `gql()` 调用后先校验 `errors` 和 `data`，不做检查视为 bug。
3. **能用 `gh` 一行搞定的不写 Python。** 调用 `gh issue edit`、`gh api` 比手写 GraphQL mutation 更稳定。
4. **输出一致性。** 成功只输出结果。所有错误走 stderr。退出码 0 表示成功。

### 复用脚本

技能目录下包含以下脚本：

**`scripts/project.py`** — Project 管理工具，支持增改查和状态切换：

```bash
python3 scripts/project.py list <owner>                    # 列出项目
python3 scripts/project.py get <project-id>                 # 查看字段+卡片
python3 scripts/project.py create-draft <project-id> "标题"  # 创建 Draft
python3 scripts/project.py move <project-id> <item-id> <状态> # 移动卡片
python3 scripts/project.py convert <item-id> <repo-id>       # Draft → Issue
python3 scripts/project.py setup <project-id> '<items>'      # Sprint 初始化
```

`setup` 每项支持 5 个字段: `[title, status, priority, estimate, body]`
body 可选，传入后写入 Issue 正文（含用户故事、验收条件等）。

**`scripts/discussion.py`** — Discussion 管理工具，支持增改查和开关：

```bash
python3 scripts/discussion.py list <owner/repo>             # 列出讨论
python3 scripts/discussion.py get <discussion-id>           # 查看全文
python3 scripts/discussion.py create <owner/repo> <分类> "标题" [body]  # 创建
python3 scripts/discussion.py update <id> [body] [--title]  # 更新正文/标题
python3 scripts/discussion.py close <id>                    # 关闭
python3 scripts/discussion.py reopen <id>                   # 重新打开
```

分类: `ideas` / `requirements` / `tech-spec` (自动 fallback)

### 已知坑 (GitHub Projects V2 API)

1. **Status 是默认字段** — 每个 Project board 自动带一个 Status 字段（Todo/In Progress/Done），不能手动创建
2. **singleSelectOptions 需要 description** — GitHub API 要求每个选项必须有 description 字段（可传空字符串）
3. **createProjectV2Field 返回 projectV2Field** — 不是 `field`
4. **DraftIssue 的判断** — 它的 `content.__typename == "DraftIssue"`，不是 null
5. **convertProjectV2DraftIssueItemToIssue** — 返回字段名是 `clientMutationId`，不是 `issue`
6. **token 权限** — Fine-grained token 必须有 `project` scope（read/write），否则 query/mutation 会失败
7. **Claude Code 权限** — 需要 `Bash(gh *)` 才能通过 Claude 执行 gh 命令
8. **字符串拼接** — 用 Python subprocess 比 shell 拼接安全（避免引号转义）
