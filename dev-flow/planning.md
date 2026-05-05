# 规划手册

## ✅ 需求定稿 → 任务拆分

Requirements Discussion 确认定稿后，将每个用户故事转为 Project board 卡片。

## 卡片结构

一个卡片 = 一个用户故事，包含：
- **标题**：US-XX 功能描述
- **验收条件**：直接引用 Discussion 中的 AC，同时根据功能特点补充边界情况验收条件，提高验收质量
- **参考链接**：
  - 对应的需求文档（Requirements Discussion）
  - 对应的技术方案（Tech Spec Discussion，如有）
  - 项目较大时可能有多个需求和技术文档，全部列出

## Sprint Board 设置

### 创建新迭代

```bash
python3 scripts/project.py setup <project-id> '<items>'
```

`setup` 每项支持 5 个字段: `[title, status, priority, estimate, body?]`
body 可选，传入后写入 Issue 正文（含用户故事、验收条件等）。

### 添加卡片

```bash
# 创建 Draft 卡片
python3 scripts/project.py create-draft <project-id> "标题"

# Draft → Issue（立即去 Draft）
python3 scripts/project.py convert <item-id> <repo-id>
```

创建后自动 Convert to issue（去 Draft 标识），issue 落在 plan repo 的 Issues tab，但以 board 为准。

### 移动卡片状态

```bash
python3 scripts/project.py move <project-id> <item-id> <状态> [--commit <sha>]
```

状态流转：Todo → In Progress → Done

## 其他操作

```bash
python3 scripts/project.py list <owner>       # 列出项目
python3 scripts/project.py get <project-id>   # 查看字段+卡片
```
