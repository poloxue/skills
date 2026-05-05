# 需求与技术方案手册

## 💡 Idea — 记录新想法

在计划仓库的 Discussions 的 Ideas 分类下开 Discussion，随意记录，不需要格式。

用法：在 Claude Code 中说"有个想法"或 `/dev-flow idea`。

## 📋 Requirement — 想法转需求

从已有的 Ideas Discussion 提取内容，写成 PRD + 用户故事，在 Requirements 分类下开新的 Discussion。

### Discussion Category 选择规则

| 用途 | 首选 category | Fallback |
|------|--------------|----------|
| 💡 Ideas | `Ideas` | —（一定存在） |
| 📋 Requirements | `Requirements` | `Show and tell` |
| 🏗️ Tech Spec | `Tech Spec` | `General` |

category slug 是自动生成的：`Requirements` → `requirements`，`Tech Spec` → `tech-spec`。

### PRD 结构

```
# 标题

## 背景
为什么需要这个功能？

## 目标
解决什么问题？衡量标准是什么？

## 范围
- **包含**：明确在这个需求内的
- **不包含**：明确不在这个需求内的

## 用户故事
- US-XX: 作为 <角色>，我希望 <功能>，以便 <价值>
  - AC1: ...
  - AC2: ...
```

每个用户故事包含验收条件。

### Tech Spec 结构

只在方案不明确或需要决策时写。分析影响范围、实现方案、排期估算。

```
# 技术方案

## 影响范围
哪些模块/文件会改动？

## 方案对比
列出可选方案，说明选择理由

## 详细设计
核心逻辑、数据结构、接口定义

## 风险与缓解
潜在问题和应对方案

## 排期估算
预计工作量
```

### 脚本使用

```bash
# 创建 Discussion
echo "正文" | python3 scripts/discussion.py create owner/repo ideas "标题"
python3 scripts/discussion.py create owner/repo requirements "标题" body_file.md # 如果不是文件，可创建临时文件，用完删除
python3 scripts/discussion.py create owner/repo tech-spec "标题" body_file.md # 如果不是文件，可创建临时文件，用完删除

# 其他操作
python3 scripts/discussion.py list <owner/repo>
python3 scripts/discussion.py get <discussion-id>
python3 scripts/discussion.py update <id> [body] [--title]
python3 scripts/discussion.py close <id>
python3 scripts/discussion.py reopen <id>
```
