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
    ↓ 确认后 Convert to issue
🏗️ Tech Spec（评估方案，需要时才写）
```

### Repo Convention

- **Code repo** — 只放代码，保持干净，对外可见时可公开
- **Plan repo**（由用户配置） — Discussions + Issues + Project，全部 private

### Commands

#### 💡 idea — 记录新想法
- 在计划仓库的 Discussions 的 Ideas 分类下开 Discussion
- 随意记录，不需要格式

用法：你说"有个想法"或 "/dev-flow idea"，我会先确认你想的是什么，然后记下来。

#### 📋 requirement — 想法转需求
- 从已有的 Ideas Discussion 提取内容，写成 PRD + 用户故事
- 在 Requirements 分类下开新的 Discussion
- 每个用户故事包含验收条件

用法：你说"帮我把那个想法整理成需求"或 "/dev-flow requirement <想法标题>"。

#### 🏗️ tech-spec — 技术评估
- 分析需求的影响范围、实现方案、排期估算
- 在 Tech Spec 分类下开 Discussion
- 不是每个需求都需要，方案不明确或需要决策时才写

用法：你说"评估下这个怎么实现"或 "/dev-flow tech-spec <需求标题>"。

#### 📋 issue — 需求转 Issue
- 把定稿的需求（Requirements Discussion）中的每个用户故事转为 Issue
- 验收条件写在 Issue body 里
- 自动创建/更新 Project board 并排入迭代

用法：你说"把这些需求转成 issue"或 "/dev-flow issue <需求标题>"。

#### 🗺️ sprint — 启动迭代
- 创建新的 Project board（一次迭代一个）
- 自定义字段：优先级、工时估算、状态

用法：你说"开始新迭代"或 "/dev-flow sprint"。

#### ℹ️ help — 查看流程说明和可用命令
- 输出这个工作流概览

### 关键规则

- 一个 Issue = 一个用户故事
- 每个 Issue 包含验收条件（集成测试用例）
- 不需要经 tech-spec 才能转 issue，简单需求可以直接转
- Tech Spec 只在方案不明确或需要决策时写
