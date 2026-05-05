# 开发手册

## 流程

```
移卡片 In Progress → BDD → TDD → 实现 → 测试 → 代码审查 → 提交 + 关联 + 移 Done
```

## 1. 领取卡片 → 移 In Progress

```bash
python3 scripts/project.py move <project-id> <item-id> "In Progress"
```

## 2. 写方案到 Issue 评论（必做，不跳过）

移卡片到 In Progress 后，**必须先写方案，才能进入下一步**。不管任务多简单都必须写，至少两三行说明改动范围和涉及文件。

| 场景 | 方案存放位置 | 关联方式 |
|------|------------|---------|
| 简单改动（几行代码） | issue 评论，说明改什么文件和怎么改 | — |
| 单个复杂 issue | issue 评论，写明方案 + 改动范围 | — |
| 跨多个 issue 的改动 | Discussion，每个关联 issue 评论贴链接 | 参考分类规则 |

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

## 7. 迭代中修正测试

- **验收条件不变，测试有 bug** → 修测试
- **验收条件变了** → 先更新 Issue 卡片，再更新测试
- **新增分支场景** → 追加新用例，不修改已有断言

## 8. 代码审查

所有测试通过后，**按 Issue 的 AC 逐条审查代码**，检查以下方面：

- **功能完整性** — 每个 AC 是否都有对应的代码实现？
- **边界情况** — 空列表、加载失败、未登录等场景是否处理了？
- **BDD 覆盖** — 测试用例是否覆盖所有 AC？有无遗漏场景？
- **逻辑缺陷** — 明显缺少的判断、错误处理、数据竞争？

发现的问题修完再走下一步（不新增 Issue，在当前卡片内修复）。

## 9. 提交 + 关联卡片（checklist）

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

## 10. 参考

脚本用法和已知坑见 [references.md](references.md)。

### 提交规范

- **Feature commit** — 引用 user story 的 Issue 编号：`feat: US-XX #N 描述`
- **Bug fix commit** — 引用 bug 的独立 Issue 编号：`fix: #N 描述`（不引用 user story）
