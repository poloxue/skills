---
name: dev-flow
description: Development workflow — manage ideas, requirements, tech specs, issues, sprint planning, and sprint closure
user-invocable: true
argument-hint: "command: idea | requirement | tech-spec | story | sprint | develop | test | help"
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

## 流程总览

```
💡 Ideas → 📋 Requirements ↔ 🏗️ Tech Spec → 📦 Project board → 🛠️ 开发 → ✅ 测试验收 → 📦 Sprint 收尾
```

## 阶段路由

根据当前工作阶段，查看对应手册：

| 阶段 | 手册 |
|------|------|
| 💡 想想法 / 📋 写 PRD / 🏗️ 技术方案 | [需求与技术方案手册](requirements.md) |
| ✅ 最终需求确认 / 📦 任务拆分解 | [规划手册](planning.md) |
| 🛠️ 开发实现 | [开发手册](development.md) |
| ✅ 测试验收 / 🐛 Bug 修复 | [验收手册](acceptance.md) |
| 📦 Sprint 收尾 | [收尾手册](sprint-closure.md) |

## Repo Convention

- **Code repo** — 只放代码，保持干净
- **Plan repo**（由用户配置） — Discussions + Issues（仅 bug）+ Project board

## 命令

| 命令 | 用途 | 参考 |
|------|------|------|
| `idea <描述>` | 记录新想法到 Discussions | [需求手册](requirements.md) |
| `requirement <想法标题>` | 想法转需求（PRD + 用户故事） | [需求手册](requirements.md) |
| `tech-spec <需求标题>` | 技术评估方案 | [需求手册](requirements.md) |
| `story <需求标题>` | 把需求拆为用户故事卡片（加到当前 Sprint） | [规划手册](planning.md) |
| `sprint` | 创建新迭代看板 | [规划手册](planning.md) |
| `develop` | 进入开发阶段 | [开发手册](development.md) |
| `test` | 进入测试验收阶段 | [验收手册](acceptance.md) |
| `close` | 进入 Sprint 收尾阶段 | [收尾手册](sprint-closure.md) |
| `help` | 查看流程说明 | — |

## 关键规则

- 一个 Project board item = 一个用户故事
- Bug 才创建 GitHub Issue（走 board，与同一个 sprint 关联）
- User Story 不需要经 tech-spec 才能转 issue，简单需求可以直接转
- Tech Spec 只在方案不明确或需要决策时写
- 核心原则：Issues tab 是存储层，Project board 是视图层
