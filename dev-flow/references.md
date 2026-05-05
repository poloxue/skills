# 参考信息

## Discussion Category 选择规则

| 用途 | 首选 category | Fallback |
|------|--------------|----------|
| 💡 Ideas | `Ideas` | —（一定存在） |
| 📋 Requirements | `Requirements` | `Show and tell` |
| 🏗️ Tech Spec | `Tech Spec` | `General` |

category slug 是自动生成的：`Requirements` → `requirements`，`Tech Spec` → `tech-spec`。

## 提交规范

每次提交必须关联 Issue，确保 GitHub 自动链接 commit：

1. **Feature commit** — 引用 user story 的 Issue 编号：`feat: US-XX #N 描述`
2. **Bug fix commit** — 引用 bug 的独立 Issue 编号：`fix: #N 描述`（不要引用 user story）
3. **Move 到 Done 时 `--commit`**：

```bash
git commit -m "fix: #15 rate limit warning position" && \
  SHA=$(git rev-parse HEAD) && \
  python3 scripts/project.py move <project-id> <item-id> "Done" --commit "$SHA"
```

## 脚本设计原则

1. **不重复 `gh` 已有的能力。** Issue CRUD、PR、label 管理直接用 `gh` 命令。
2. **GraphQL wrapper 必须有错误检查。** 每次 `gql()` 调用后先校验 `errors` 和 `data`。
3. **能用 `gh` 一行搞定的不写 Python。** 调用 `gh issue edit`、`gh api` 更稳定。
4. **输出一致性。** 成功只输出结果。错误走 stderr。退出码 0 表示成功。

## 复用脚本

**`scripts/project.py`** — Project 管理工具：

```bash
python3 scripts/project.py list <owner>                    # 列出项目
python3 scripts/project.py get <project-id>                 # 查看字段+卡片
python3 scripts/project.py create-draft <project-id> "标题"  # 创建 Draft
python3 scripts/project.py move <project-id> <item-id> <状态> # 移动卡片
python3 scripts/project.py convert <item-id> <repo-id>       # Draft → Issue
python3 scripts/project.py setup <project-id> '<items>'      # Sprint 初始化
```

`setup` 每项支持 5 个字段: `[title, status, priority, estimate, body?]`

**`scripts/discussion.py`** — Discussion 管理工具：

```bash
python3 scripts/discussion.py list <owner/repo>             # 列出讨论
python3 scripts/discussion.py get <discussion-id>           # 查看全文
python3 scripts/discussion.py create <owner/repo> <分类> "标题" [body]  # 创建
python3 scripts/discussion.py update <id> [body] [--title]  # 更新
python3 scripts/discussion.py close <id>                    # 关闭
python3 scripts/discussion.py reopen <id>                   # 重新打开
```

## 已知坑 (GitHub Projects V2 API)

1. **Status 是默认字段** — 每个 Project board 自动带一个 Status 字段，不能手动创建
2. **singleSelectOptions 需要 description** — 每个选项必须有 description 字段（可传空字符串）
3. **createProjectV2Field 返回 projectV2Field** — 不是 `field`
4. **DraftIssue 的判断** — `content.__typename == "DraftIssue"`，不是 null
5. **convertProjectV2DraftIssueItemToIssue** — 返回字段名是 `clientMutationId`，不是 `issue`
6. **token 权限** — Fine-grained token 必须有 `project` scope（read/write）
7. **Claude Code 权限** — 需要 `Bash(gh *)` 才能通过 Claude 执行 gh 命令
8. **字符串拼接** — 用 Python subprocess 比 shell 拼接安全（避免引号转义）
