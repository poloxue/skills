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

### 提炼指引

从 Ideas Discussion 提取需求时，至少理清以下问题：

- **目标用户** — 谁会用到这个功能？解决谁的痛点？
- **痛点/动机** — 当前缺什么？没有这个功能会怎样？
- **成功标准** — 怎么衡量做对了？（DAU、操作耗时、报错率等）
- **优先级** — 不做会有什么后果？（阻塞后续 / 体验硬伤 / 锦上添花）

### 用户故事拆分

一个需求可能包含多个用户故事。出现以下信号说明需要拆分：

- 故事涉及完全不同的用户角色（如管理员 vs 普通用户）
- 包含多个独立的工作流（如创建 vs 审批）
- 故事太大无法在一个 Sprint 完成（"史诗故事"）

每个用户故事是一个独立的 Project board card。

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

## 功能逻辑
在拆用户故事之前，先完整描述需求的运作方式。可以包含用户流程、业务规则、状态流转等，复杂逻辑推荐用 Mermaid 描述。

## 用户故事
- US-XX: 作为 <角色>，我希望 <功能>，以便 <价值>
  - AC1: ...
  - AC2: ...
```

### 验收条件要点

- Happy path + edge case：至少覆盖正常流程和常见异常
- 具体可验证：避免"用户体验好"，改成"操作步骤 ≤ 3 步"这类可判断的描述
- 简单用列表，复杂用 Given/When/Then

### Tech Spec — 触发条件

以下情况**必须**写 Tech Spec（满足任一即可）：

- 涉及外部系统 / 第三方 API 集成
- 涉及 DB schema 变更或数据迁移
- 有 breaking API 变更
- 有性能要求（延迟、并发量等明确指标）
- 方案有争议或你也不确定怎么做

### Tech Spec 结构

```
# 技术方案

## 影响范围
哪些模块/文件会改动？影响哪些现有功能？

## 方案对比
列出所有候选方案，按以下维度评估：
- **复杂度** — 改动量、新增代码量
- **维护成本** — 长期运维负担
- **风险** — 引入 bug、性能退化、安全问题的可能性

## 详细设计
核心逻辑、数据结构、接口定义

## 风险与缓解
潜在问题和应对方案

## 排期估算
T-shirt sizing：S（1-2d）/ M（3-5d）/ L（1-2w）/ XL（>2w）
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
