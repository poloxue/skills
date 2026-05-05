# 验收与 Bug 修复手册

## ✅ 验收流程

卡片移到 Done 后，进入验收阶段：

```text
用户根据 AC 验证功能
  ↓
┌─ 符合预期 ───────→ ✅ 验收通过 → 结束
│
└─ 发现问题 ───────→ 🐛 进入 Bug 修复流程
```

## 🐛 Bug 修复流程

```text
发现问题
  ↓
① 检查代码 → 确认 bug 确实存在
  ↓
② gh issue create --label bug
   body 注明：`关联: #<user-story-number>`
  ↓
③ 加入 Sprint 看板（与 user story 同一个 board），移到 In Progress
  ↓
④ 在 user story issue 评论区留言：
   `❌ 验收未通过 — 发现 bug #<N>: <描述>`
  ↓
⑤ 在 bug issue 评论区写修复方案
   （改什么文件、怎么改，至少两三行，再简单的 bug 也要写）
  ↓
⑥ 修复（必要时写 TDD，不写 BDD）
  ↓
⑦ go test && git commit -m "fix: #<N> 描述"
  ↓
⑧ 移 Done → 用户重新验收
         ↓      ↓
      通过 ✅  不通过 → 移回 In Progress → 继续修
```

### 关键规则

**关联规则**
- Bug issue body 必须注明：`关联: #<user-story-number>`
- User story issue 评论区必须注明：`❌ 验收未通过 — 发现 bug #<N>: <描述>`
- 一个 user story 可以关联多个 bug，一个 bug 只属于一个 user story
- 首次发现 bug 才创建 bug issue，验收不通过不重复建

**修复规则**
- 验收发现的 bug 必须加入 Sprint 看板，与 user story 同 board
- **先方案再动手** — 创建 bug issue 后，先在评论区写方案再编码，不跳过
- Bug fix commit 只引用 bug issue 编号（`fix: #N`），不引用 user story
- 验收不通过 → 移回 In Progress 继续修，不建新 issue
