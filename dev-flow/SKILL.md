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

### 开发流程（BDD → TDD → 验收）

每个任务的完整周期：**BDD 验收测试 → TDD 单元测试 → 实现 → 运行全部测试 → 验收关联**

#### 1. 写 BDD 验收测试

基于用户故事的验收条件，先写 Go 测试。每个验收条件对应一个 `t.Run`：

```go
func TestIssueFilter(t *testing.T) {
    t.Run("默认选中 [Open]", func(t *testing.T) {
        m := testModel()
        v := m.View()
        assert(t, strings.Contains(v, "[Open]"), "should show [Open]")
    })
    t.Run("按 ] 切换到 Closed", func(t *testing.T) {
        m := testModel()
        m.Update(sendKey("]"))
        assert(t, m.filter == "closed", "should switch to closed")
    })
}
```

规范：
- 每个验收条件一条 `t.Run`
- `sendKey("j")` / `sendKey("]")` 模拟按键
- **不依赖网络** — mock 数据直接注入模型

#### 2. TDD（先写单元测试再实现）

对关键的内部函数，先写单元测试：

```go
func TestRelTime(t *testing.T) {
    t.Run("刚刚返回 now", func(t *testing.T) {
        assert(t, relTime(time.Now()) == "now", "just now")
    })
    t.Run("一小时前", func(t *testing.T) {
        assert(t, relTime(time.Now().Add(-1*time.Hour)) == "1h ago", "")
    })
    t.Run("边界: 未来时间", func(t *testing.T) {
        assert(t, relTime(time.Now().Add(time.Hour)) == "now", "future time")
    })
}
```

原则：
- 内部纯函数（relTime、truncate）先写单元测试再实现
- 覆盖边界值：空输入、负数、极大值
- 单元测试和 BDD 测试通过后，功能才算完成

#### 3. 开始实现

写代码让所有测试通过。TUI 的按键响应通过 `m.Update(sendKey(...))` 模拟。

#### 4. 运行全部测试

```bash
go test ./... -v
```

全绿才能进入验收。

#### 5. 迭代中修正测试

如果实现过程中发现测试有问题，测试也要一起改：

- **验收条件不变，测试实现有 bug** → 修测试
- **验收条件变了** → 先更新 Issue 中的用户故事和验收条件，再更新测试
- **新增分支场景** → 追加新 `t.Run`，不修改已有断言的语义

不要把过时的测试留在那里，也不要不准确的测试强行通过。

#### 6. 提交 + 关联卡片

```bash
git commit -m "feat: US-XX #N 功能描述" && \
  SHA=$(git rev-parse HEAD) && \
  python3 scripts/project.py move <project-id> <item-id> "Done" --commit "$SHA"
```

#### 测试辅助函数模板

```go
func sendKey(s string) tea.Msg {
    return tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune(s)}
}

func testModel() *Model {
    m := New()
    m.SetContext(module.Context{Owner: "test", Repo: "repo"})
    m.ready = true
    m.width = 80
    return m
}

func assert(t *testing.T, ok bool, msg string) {
    t.Helper()
    if !ok {
        t.Error(msg)
    }
}
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
