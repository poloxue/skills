# 开发流程

功能开发完整周期：
**移卡片 → 读/写方案 → BDD → TDD → 实现 → 测试 → 提交 + 关联 + 移 Done → 等验收**

Bug 修复是独立流程，见下文。

---

## 1. 领取卡片 → 移 In Progress

```bash
python3 scripts/project.py move <project-id> <item-id> "In Progress"
```

## 2. 写方案到 issue 评论（必做，不跳过）

移卡片到 In Progress 后，**必须先写方案，才能进入下一步测试环节**。不管任务多简单都必须写，哪怕只有两三行说明改动范围和涉及文件。

- **有关联技术文档**（Discussion / issue 评论中的方案）→ 通读后在 issue 评论中写实施计划
- **无关联文档** → 直接写方案到 issue 评论

方案存放规则：

| 场景 | 方案存放位置 | 关联方式 |
|------|------------|---------|
| 简单改动（几行代码） | issue 评论，说明改什么文件和怎么改 | — |
| 单个复杂 issue | issue 评论，写明方案 + 改动范围 | — |
| 跨多个 issue 的改动 | Discussion，每个关联 issue 评论贴链接 | 参考 `references.md` 分类规则 |

**写完方案才能往下走。**

## 3. 写 BDD 验收测试

基于用户故事卡片中的验收条件，先写验收测试。每个验收条件对应一条测试用例：

```text
场景: 过滤器切换
  Given 有一个包含多个 Issue 的列表
  When 用户按下 "]"
  Then 过滤器切换到 Closed
  And 列表重新加载
```

规范：
- 每个验收条件一条测试用例（直接引用 Issue 中的 AC 编号）
- 模拟用户交互（按键输入），断言系统状态变化
- **默认 mock 外部依赖** — 数据直接注入，不调真实网络/API

## 4. TDD（先写单元测试再实现）

对关键的内部函数或模块，先写单元测试再实现：

```text
函数: formatRelativeTime
  - 刚刚 → "now"
  - 5 分钟前 → "5m ago"
  - 2 天前 → "2d ago"
  - 未来时间 → "now" (边界)
```

原则：
- 内部关键逻辑先写测试再实现
- 覆盖边界值：空输入、负数、极大值
- 单元测试和 BDD 测试都通过后，功能才算完成

## 5. 开始实现

写代码让所有测试通过。

## 6. 运行全部测试

```bash
go test ./... -count=1
```

不同语言替换为相应的测试命令，全绿才能验收。

## 7. 迭代中修正测试

- **验收条件不变，测试有 bug** → 修测试
- **验收条件变了** → 先更新 Issue 卡片，再更新测试
- **新增分支场景** → 追加新用例，不修改已有断言

## 8. 提交 + 关联卡片（checklist）

按顺序执行：

1. **编译验证** — `go build ./... && go vet ./...`
2. **运行测试** — `go test ./... -count=1`
3. **Stage 代码** — `git add <files>`
4. **提交**：

```bash
git commit -m "feat: US-XX #N 功能描述"
```

5. **移到 Done 并关联 commit**：

```bash
SHA=$(git rev-parse HEAD) && \
  python3 scripts/project.py move <project-id> <item-id> "Done" --commit "$SHA"
```

6. **停下来** — 等待用户验收，不要自动开始下一个任务。

## 9. 验收 (Acceptance)

卡片移到 Done 后，**必须等待用户验收通过，才能开始下一个任务**。

1. **用户验收** — 用户根据验收条件验证功能是否正常工作
2. **Bug 跟踪** — 创建独立 Issue（双向关联）：
   - Bug Issue body：`关联: #<user-story-number>`
   - User Story 评论区：`❌ 验收未通过 — 发现 bug #<N>: <描述>`

---

## Bug 修复流程

bug 修复和功能开发是两套独立流程。bug 从创建到验收通过的完整周期如下：

```text
```text
功能开发验收发现 bug
  ↓
gh issue create --label bug（body 注明关联的 user story 编号）
  ↓
将 bug issue 加入 Sprint 看板（同一个 board），移到 In Progress
  ↓
在 user story issue 评论区留言：`❌ 验收未通过 — 发现 bug #<N>: <描述>`
  ↓
修复（必要时写 TDD，不写方案/BDD，除非 BDD 本身有 bug，或需要添加新的验收规则）
  ↓
go test → git commit -m "fix: #<bug-number> 描述"
  ↓
移 Done ─→ 验收
  ↓            ↓
通过         不通过 → 移回 In Progress（不建新 issue）→ 继续修复
```

关键规则：
- **首次发现 bug** 才创建 bug issue
- **验收发现的 bug 必须加入 Sprint 看板**（与 user story 同一个 board），用于跟踪验收进度
- **双向关联**：
  - Bug issue body 必须注明：`关联: #<user-story-number>`
  - User story issue 评论区必须注明：`❌ 验收未通过 — 发现 bug #<N>: <描述>`
  - 一个 user story 可以关联多个 bug，一个 bug 只属于一个 user story
- **验收不通过**直接移回 In Progress，不重复建 issue
- **Bug fix commit 只引用 bug issue 编号，不引用 user story
