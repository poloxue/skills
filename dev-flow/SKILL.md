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
  - Bash(python3 **/scripts/project.py*)
  - Bash(python3 **/scripts/discussion.py*)
---

## 首次使用

如果还不知道用户的计划仓库是哪个，先问用户：

> "就是用这个仓库来跟踪开发讨论和计划的吗？还是另有其他仓库？"

确认后，建议用户把 `Plan repo: <owner>/<repo>` 保存在用户级或项目级的配置中。

## Development Workflow

```
💡 Ideas → 📋 Requirements → 🏗️ Tech Spec → 📦 Project board
    ↓                                               ↓
🔄 BDD 测试 → 🔬 TDD 单元测试 → 💻 开发实现 → ✅ 运行全部测试
    ↓
📎 提交 + 关联卡片 → 验收
```

- **Requirements ↔ Tech Spec 互相反馈修改** — 通过 Discussion 评论同步
- **User Story** → Project board draft item → Convert to issue（去 Draft）
- **Bug** → 直接在 plan repo 创建 GitHub Issue（不走 board）
- **核心原则**：Issues tab 是存储层，Project board 是视图层

### Repo Convention

- **Code repo** — 只放代码，保持干净
- **Plan repo**（由用户配置） — Discussions + Issues（仅 bug）+ Project board

### Commands

- `/dev-flow idea <描述>` — 记录新想法到 Discussions
- `/dev-flow requirement <想法标题>` — 想法转需求（PRD + 用户故事）
- `/dev-flow tech-spec <需求标题>` — 技术评估（需要决策时才写）
- `/dev-flow issue <需求标题>` — 需求转 Project board 卡片
- `/dev-flow sprint` — 启动新迭代
- `/dev-flow help` — 查看流程说明

### 关键规则

- 一个 Project board item = 一个用户故事
- Bug 才创建 GitHub Issue
- User Story 不需要经 tech-spec 才能转 issue，简单需求可以直接转
- Tech Spec 只在方案不明确或需要决策时写

### 预授权工具

frontmatter 的 `allowed-tools` 限制了操作范围（gh/git/python3 脚本），系统自动放行。

---

## 开发实现流程

按卡片开发时，先读 **[workflow.md](workflow.md)**。功能开发和 bug 修复是两套独立流程。

## 参考信息

脚本用法和已知坑见 **[references.md](references.md)**。
