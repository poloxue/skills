"""
Sprint Project Board 初始化脚本

在已有 Project board 上创建 Sprint 迭代项。默认创建 draft item;
传入 --repo-id 后自动 Convert to issue (去 Draft 标识)。

用法:
  python3 scripts/setup_sprint.py <project_id> '<items_json>' [--repo-id <repo_id>]

参数:
  project_id — GitHub Project V2 Node ID, 如 PVT_kwHOAFqP2c4BWsLh
  items_json — JSON 数组, 每项: [title, status, priority, estimate]
  --repo-id  — (可选) plan repo 的 Node ID。传入后自动将 draft 转为 issue

示例:
  # 只创建 draft items
  python3 scripts/setup_sprint.py PVT_kwHOAFqP2c4BWsLh '[
    ["US-01: 实现登录", "Todo", "P0", 2.0],
    ["US-02: 注册功能", "Todo", "P1", 1.0]
  ]'

  # 创建后自动转 issue (去 Draft 标识)
  python3 scripts/setup_sprint.py PVT_kwHOAFqP2c4BWsLh '[...]' --repo-id R_kgDOSQnlAQ

前置条件:
  - gh CLI 已登录, token 有 project 权限
  - 先用浏览器手动创建 Project board, 从 URL 或 API 获取 project_id
  - 通过 Claude Code 执行时需要 Bash(gh *) 权限

已知坑 (已踩过, 避免重复试错):
  1. "Status" 是 Project V2 默认字段, 自动存在, 不能手动创建
  2. singleSelectOptions 中的每个 option 必须有 description 字段 (空字符串也行)
  3. createProjectV2Field 的返回字段名是 projectV2Field, 不是 field
  4. convertProjectV2DraftIssueItemToIssue 的返回字段名是 clientMutationId, 不是 issue
  5. DraftIssue 的 content.__typename == "DraftIssue" (不是 null), 判断时注意
  6. 中文/特殊字符不需要额外转义 (只要避开双引号)
  7. Python subprocess 比 shell 拼接安全, 推荐使用
"""

import subprocess, json, sys


def gql(query):
    r = subprocess.run(
        ["gh", "api", "graphql", "-f", f"query={query}"],
        capture_output=True, text=True
    )
    return json.loads(r.stdout)


def get_field_id(pid, name):
    """按名称查找已有字段"""
    q = ('{ node(id: "' + pid + '") { ... on ProjectV2 '
         '{ fields(first: 30) { nodes { ... on ProjectV2Field { id name } '
         '... on ProjectV2SingleSelectField { id name } } } } } }')
    for f in gql(q)["data"]["node"]["fields"]["nodes"]:
        if f and f["name"] == name:
            return f["id"]
    return None


def create_single_select_field(pid, name, options):
    """创建单选字段, 跳过已存在的"""
    existing = get_field_id(pid, name)
    if existing:
        print(f"  {name}: 已存在, 跳过")
        return existing

    opts = ",".join(
        '{name: "%s", color: %s, description: ""}' % (o["n"], o["c"])
        for o in options
    )
    q = ('mutation { createProjectV2Field(input: { projectId: "' + pid
         + '", dataType: SINGLE_SELECT, name: "' + name
         + '", singleSelectOptions: [' + opts + '] }) '
         '{ projectV2Field { ... on ProjectV2SingleSelectField { id } } } }')
    fid = gql(q)["data"]["createProjectV2Field"]["projectV2Field"]["id"]
    print(f"  {name}: {fid}")
    return fid


def create_number_field(pid, name):
    """创建数字字段, 跳过已存在的"""
    existing = get_field_id(pid, name)
    if existing:
        print(f"  {name}: 已存在, 跳过")
        return existing

    q = ('mutation { createProjectV2Field(input: { projectId: "' + pid
         + '", dataType: NUMBER, name: "' + name + '" }) '
         '{ projectV2Field { ... on ProjectV2Field { id } } } }')
    fid = gql(q)["data"]["createProjectV2Field"]["projectV2Field"]["id"]
    print(f"  {name}: {fid}")
    return fid


def get_options(field_id):
    q = ('query { node(id: "' + field_id
         + '") { ... on ProjectV2SingleSelectField { options { id name } } } }')
    return {o["name"]: o["id"] for o in gql(q)["data"]["node"]["options"]}


def create_draft(pid, title):
    q = ('mutation { addProjectV2DraftIssue(input: { projectId: "' + pid
         + '", title: "' + title + '" }) { projectItem { id } } }')
    return gql(q)["data"]["addProjectV2DraftIssue"]["projectItem"]["id"]


def set_field(pid, item_id, field_id, value):
    q = ('mutation { updateProjectV2ItemFieldValue(input: { projectId: "' + pid
         + '", itemId: "' + item_id + '", fieldId: "' + field_id
         + '", value: ' + value + ' }) { projectV2Item { id } } }')
    gql(q)


def convert_to_issue(item_id, repo_id):
    """Draft → Issue, 去除 Draft 标识"""
    q = ('mutation { convertProjectV2DraftIssueItemToIssue(input: '
         '{ itemId: "' + item_id + '", repositoryId: "' + repo_id + '" }) '
         '{ clientMutationId } }')
    gql(q)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Setup Sprint Project Board")
    parser.add_argument("project_id", help="Project V2 Node ID")
    parser.add_argument("items_json", help="JSON array of items")
    parser.add_argument("--repo-id", help="Plan repo Node ID (convert drafts to issues)")
    args = parser.parse_args()

    pid = args.project_id
    repo_id = args.repo_id
    items = json.loads(args.items_json)

    # 查找 Status 默认字段 (每个 Project board 自动带一个)
    status_id = get_field_id(pid, "Status")
    if not status_id:
        print("错误: 找不到 Status 字段 (Project 默认应自带)")
        sys.exit(1)

    # 创建自定义字段
    print("=== 字段 ===")
    pri_id = create_single_select_field(pid, "Priority",
        [{"n": "P0", "c": "RED"}, {"n": "P1", "c": "YELLOW"},
         {"n": "P2", "c": "GREEN"}])
    est_id = create_number_field(pid, "Estimate")

    status_opts = get_options(status_id)
    pri_opts = get_options(pri_id)

    # 创建 draft items 并设字段
    print("=== Items ===")
    for title, status, priority, estimate in items:
        iid = create_draft(pid, title)
        set_field(pid, iid, status_id,
                  '{singleSelectOptionId: "' + status_opts[status] + '"}')
        set_field(pid, iid, pri_id,
                  '{singleSelectOptionId: "' + pri_opts[priority] + '"}')
        set_field(pid, iid, est_id, '{number: ' + str(estimate) + '}')

        if repo_id:
            convert_to_issue(iid, repo_id)
            print(f"  {title}: {status} {priority} {estimate}h (issue)")
        else:
            print(f"  {title}: {status} {priority} {estimate}h (draft)")


if __name__ == "__main__":
    main()
