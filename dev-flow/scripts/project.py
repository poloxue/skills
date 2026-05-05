"""
Project 管理工具 (增/改/查/状态切换)

支持 GitHub Project V2 的常规操作和 Sprint 初始化。

用法:
  python3 scripts/project.py list <owner>                 # 列出项目
  python3 scripts/project.py get <project-id>              # 查看项目字段+卡片
  python3 scripts/project.py create-draft <project-id> "<title>" [--status <name>]
  python3 scripts/project.py move <project-id> <item-id> <status-name>
  python3 scripts/project.py convert <item-id> <repo-id>   # Draft → Issue
  python3 scripts/project.py setup <project-id> '<items_json>' [--repo-id <repo-id>]

  owner — GitHub 用户名或组织名
  project-id — Project V2 Node ID, 如 PVT_kwHOAFqP2c4BWsLh
  status-name — 列名, 如 "Todo" / "In Progress" / "Done"
  items_json — JSON 数组, 每项: [title, status, priority, estimate, body?]
               body 可选, 传入后写入 Issue/Draft 正文

示例:
  # 列出项目
  python3 scripts/project.py list poloxue

  # 查看项目详情
  python3 scripts/project.py get PVT_kwHOAFqP2c4BWuzy

  # 创建 Draft Issue
  python3 scripts/project.py create-draft PVT_kwHOAFqP2c4BWuzy "实现登录功能"

  # 移动卡片到 In Progress
  python3 scripts/project.py move PVT_kwHOAFqP2c4BWuzy PVTI_xxxx "In Progress"

  # Draft → Issue
  python3 scripts/project.py convert PVTI_xxxx R_kgDOSUjJrw

  # Sprint 初始化 (含正文)
  python3 scripts/project.py setup PVT_kwHOAFqP2c4BWsLh '[
    ["US-01: 登录", "Todo", "P0", 2.0, "用户故事全文..."],
    ["US-02: 注册", "In Progress", "P1", 1.0, ""]
  ]' --repo-id R_kgDOSQnlAQ
"""

import subprocess, json, sys, os, time


def gql(query):
    r = subprocess.run(
        ["gh", "api", "graphql", "-f", f"query={query}"],
        capture_output=True, text=True
    )
    if r.returncode != 0:
        print(f"API 错误: {r.stderr}", file=sys.stderr)
        sys.exit(1)
    return json.loads(r.stdout)


# ── list ──

def cmd_list(args):
    """list <owner>"""
    if len(args) < 1:
        print("用法: project.py list <owner>", file=sys.stderr)
        sys.exit(1)
    q = ('{ user(login: "' + args[0]
         + '") { projectsV2(first: 20, orderBy: {field: UPDATED_AT, direction: DESC})'
         + '{ nodes { id number title url updatedAt } } } }')
    result = gql(q)
    nodes = result["data"]["user"]["projectsV2"]["nodes"]
    if not nodes:
        print("(没有找到项目)")
        return
    for p in nodes:
        print(f"{p['id']}")
        print(f"  #{p['number']}  {p['title']}")
        print(f"  {p['url']}")
        print()


# ── get ──

def cmd_get(args):
    """get <project-id>"""
    if len(args) < 1:
        print("用法: project.py get <project-id>", file=sys.stderr)
        sys.exit(1)
    pid = args[0]
    q = ('{ node(id: "' + pid + '") { ... on ProjectV2 { id number title url '
         'fields(first: 30) { nodes { ... on ProjectV2SingleSelectField { id name options { id name } } '
         '... on ProjectV2Field { id name } } } '
         'items(first: 50) { nodes { id '
         'content { ... on DraftIssue { title body } ... on Issue { title number state url } } '
         'fieldValues(first: 20) { nodes { ... on ProjectV2ItemFieldSingleSelectValue { name field { ... on ProjectV2SingleSelectField { name } } } '
         '... on ProjectV2ItemFieldNumberValue { number } } } } } } } }')
    result = gql(q)
    proj = result["data"]["node"]

    print(f"项目: #{proj['number']} {proj['title']}")
    print(f"URL:  {proj['url']}")
    print()

    # 字段
    print("=== 字段 ===")
    for f in proj["fields"]["nodes"]:
        if f and "options" in f:
            opts = ", ".join(o["name"] for o in f["options"])
            print(f"  {f['name']}: [{opts}]")
        elif f:
            print(f"  {f['name']}")
    print()

    # 卡片
    print("=== 卡片 ===")
    for item in proj["items"]["nodes"]:
        content = item.get("content")
        if content and "state" in content:
            title = f"#{content['number']} {content['title']} ({content['state']})"
        elif content:
            title = content.get("title", "(无标题)")
        else:
            title = "(无内容)"

        # 提取 Status/字段值
        vals = {}
        for fv in item["fieldValues"]["nodes"]:
            if fv and "field" in fv and fv["field"]:
                fname = fv["field"]["name"]
                if "name" in fv:
                    vals[fname] = fv["name"]
                elif "number" in fv:
                    vals[fname] = str(fv["number"])
        status = vals.get("Status", "")
        print(f"  {item['id']}")
        print(f"    标题: {title}")
        if status:
            print(f"    状态: {status}")
        if vals:
            extra = " | ".join(f"{k}: {v}" for k, v in vals.items() if k != "Status")
            if extra:
                print(f"    {extra}")
        print()


# ── create-draft ──

def cmd_create_draft(args):
    """create-draft <project-id> <title> [--status <name>]"""
    if len(args) < 2:
        print("用法: project.py create-draft <project-id> <title> [--status <name>]", file=sys.stderr)
        sys.exit(1)
    pid, title = args[0], args[1]
    target_status = None
    for i, a in enumerate(args):
        if a == "--status" and i + 1 < len(args):
            target_status = args[i + 1]

    q = ('mutation { addProjectV2DraftIssue(input: { projectId: "' + pid
         + '", title: "' + title.replace('"', '\\"') + '" }) { projectItem { id } } }')
    item = gql(q)["data"]["addProjectV2DraftIssue"]["projectItem"]
    print(f"Draft 已创建: {item['id']}")

    if target_status:
        # 查找 Status 字段
        q_f = ('{ node(id: "' + pid + '") { ... on ProjectV2 '
               '{ fields(first: 20) { nodes { ... on ProjectV2SingleSelectField { id name options { id name } } } } } } }')
        fields = gql(q_f)["data"]["node"]["fields"]["nodes"]
        status_f = None
        status_o = None
        for f in fields:
            if f and f["name"] == "Status":
                status_f = f["id"]
                for o in f["options"]:
                    if o["name"] == target_status:
                        status_o = o["id"]
                        break
                break
        if status_f and status_o:
            q_m = ('mutation { updateProjectV2ItemFieldValue(input: { projectId: "' + pid
                   + '", itemId: "' + item['id']
                   + '", fieldId: "' + status_f
                   + '", value: { singleSelectOptionId: "' + status_o + '" } }) { projectV2Item { id } } }')
            gql(q_m)
            print(f"  状态 → {target_status}")


# ── move ──

def cmd_move(args):
    """move <project-id> <item-id> <status-name>"""
    if len(args) < 3:
        print("用法: project.py move <project-id> <item-id> <status-name>", file=sys.stderr)
        sys.exit(1)
    pid, iid, target = args[0], args[1], args[2]

    # 查找 Status 字段和目标 option
    q_f = ('{ node(id: "' + pid + '") { ... on ProjectV2 '
           '{ fields(first: 20) { nodes { ... on ProjectV2SingleSelectField { id name options { id name } } } } } } }')
    fields = gql(q_f)["data"]["node"]["fields"]["nodes"]
    status_f = None
    status_o = None
    for f in fields:
        if f and f["name"] == "Status":
            status_f = f["id"]
            for o in f["options"]:
                if o["name"] == target:
                    status_o = o["id"]
                    break
            break
    if not status_f:
        print("错误: 找不到 Status 字段", file=sys.stderr)
        sys.exit(1)
    if not status_o:
        print(f"错误: 找不到状态 '{target}'", file=sys.stderr)
        sys.exit(1)

    q = ('mutation { updateProjectV2ItemFieldValue(input: { projectId: "' + pid
         + '", itemId: "' + iid + '", fieldId: "' + status_f
         + '", value: { singleSelectOptionId: "' + status_o + '" } }) { projectV2Item { id } } }')
    gql(q)
    print(f"已移动到: {target}")


# ── convert ──

def cmd_convert(args):
    """convert <item-id> <repo-id>"""
    if len(args) < 2:
        print("用法: project.py convert <item-id> <repo-id>", file=sys.stderr)
        sys.exit(1)
    q = ('mutation { convertProjectV2DraftIssueItemToIssue(input: { itemId: "' + args[0]
         + '", repositoryId: "' + args[1] + '" }) { clientMutationId } }')
    gql(q)
    print(f"Draft 已转为 Issue (去 Draft 标识)")


# ── setup (原有 Sprint 初始化逻辑) ──

def get_field_id(pid, name):
    q = ('{ node(id: "' + pid + '") { ... on ProjectV2 '
         '{ fields(first: 30) { nodes { ... on ProjectV2Field { id name } '
         '... on ProjectV2SingleSelectField { id name } } } } } }')
    for f in gql(q)["data"]["node"]["fields"]["nodes"]:
        if f and f["name"] == name:
            return f["id"]
    return None


def create_single_select_field(pid, name, options):
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


def create_draft(pid, title, body=""):
    if body:
        body_e = body.replace("\\", "\\\\").replace('"', '\\"')
        q = ('mutation { addProjectV2DraftIssue(input: { projectId: "' + pid
             + '", title: "' + title.replace('"', '\\"') + '", body: "' + body_e
             + '" }) { projectItem { id } } }')
    else:
        q = ('mutation { addProjectV2DraftIssue(input: { projectId: "' + pid
             + '", title: "' + title.replace('"', '\\"') + '" }) { projectItem { id } } }')
    return gql(q)["data"]["addProjectV2DraftIssue"]["projectItem"]["id"]


def set_field(pid, item_id, field_id, value):
    q = ('mutation { updateProjectV2ItemFieldValue(input: { projectId: "' + pid
         + '", itemId: "' + item_id + '", fieldId: "' + field_id
         + '", value: ' + value + ' }) { projectV2Item { id } } }')
    gql(q)


def resolve_body(body_str):
    """处理正文: @file:path 从文件读（读后删除文件），空字符串保持空，其他按原样"""
    if not body_str:
        return ""
    if body_str.startswith("@file:"):
        path = body_str[6:]
        try:
            with open(path) as f:
                content = f.read().strip()
            os.unlink(path)
            return content
        except FileNotFoundError:
            print(f"  警告: 文件不存在 {path}，正文为空", file=sys.stderr)
            return ""
    return body_str


def ensure_labels(repo_owner, repo_name):
    """确保 phase-1 和 P0/P1/P2 label 存在"""
    labels_to_create = {
        "phase-1": "B0B0B0",
        "P0": "B60205",
        "P1": "D93F0B",
        "P2": "FBCA04",
    }
    existing = set()
    r = subprocess.run(
        ["gh", "api", f"repos/{repo_owner}/{repo_name}/labels",
         "--jq", ".[].name"],
        capture_output=True, text=True
    )
    if r.returncode == 0:
        existing = set(r.stdout.strip().split("\n"))

    for name, color in labels_to_create.items():
        if name in existing:
            continue
        subprocess.run(
            ["gh", "api", "-X", "POST",
             f"repos/{repo_owner}/{repo_name}/labels",
             "-f", f"name={name}", "-f", f"color={color}"],
            capture_output=True
        )


def add_labels_to_issue(repo_owner, repo_name, issue_number, labels):
    """给 Issue 加 labels"""
    labels_str = ",".join(labels)
    subprocess.run(
        ["gh", "issue", "edit", str(issue_number),
         "--repo", f"{repo_owner}/{repo_name}",
         "--add-label", labels_str],
        capture_output=True
    )


def get_issue_number_for_item(item_id):
    """通过 ProjectV2Item 查询对应的 Issue number"""
    q = ('{ node(id: "' + item_id + '") { ... on ProjectV2Item '
         '{ content { ... on Issue { number } } } } }')
    result = gql(q)
    content = result["data"]["node"].get("content")
    if content and "number" in content:
        return content["number"]
    return None


def cmd_setup(args):
    """setup <project-id> '<items_json>' [--repo-id <repo-id>]"""
    if len(args) < 2:
        print("用法: project.py setup <project-id> '<items_json>' [--repo-id <id>]", file=sys.stderr)
        sys.exit(1)
    pid = args[0]
    items = json.loads(args[1])
    repo_id = None
    for i, a in enumerate(args):
        if a == "--repo-id" and i + 1 < len(args):
            repo_id = args[i + 1]

    status_id = get_field_id(pid, "Status")
    if not status_id:
        print("错误: 找不到 Status 字段 (Project 默认应自带)")
        sys.exit(1)

    print("=== 字段 ===")
    pri_id = create_single_select_field(pid, "Priority",
        [{"n": "P0", "c": "RED"}, {"n": "P1", "c": "YELLOW"},
         {"n": "P2", "c": "GREEN"}])
    est_id = create_number_field(pid, "Estimate")

    status_opts = get_options(status_id)
    pri_opts = get_options(pri_id)

    # 解析 repo owner/name 用于 label 管理
    repo_owner = repo_name = None
    if repo_id:
        q = ('{ node(id: "' + repo_id + '") { ... on Repository { owner { login } name } } }')
        r = gql(q)
        repo_owner = r["data"]["node"]["owner"]["login"]
        repo_name = r["data"]["node"]["name"]
        ensure_labels(repo_owner, repo_name)

    print("=== Items ===")
    for item in items:
        # 兼容 4 元素 (旧格式) 和 5 元素 (标题/状态/优先级/估算/正文)
        if len(item) >= 5:
            title, status, priority, estimate, body_str = item[:5]
            body = resolve_body(body_str)
        else:
            title, status, priority, estimate = item
            body = ""
        iid = create_draft(pid, title, body)
        set_field(pid, iid, status_id,
                  '{singleSelectOptionId: "' + status_opts[status] + '"}')
        set_field(pid, iid, pri_id,
                  '{singleSelectOptionId: "' + pri_opts[priority] + '"}')
        set_field(pid, iid, est_id, '{number: ' + str(estimate) + '}')

        if repo_id:
            q_conv = ('mutation { convertProjectV2DraftIssueItemToIssue(input: '
                      '{ itemId: "' + iid + '", repositoryId: "' + repo_id + '" }) '
                      '{ clientMutationId } }')
            gql(q_conv)

            # 查询 issue number 加 label
            num = None
            for _ in range(5):  # 短轮询等转换完成
                num = get_issue_number_for_item(iid)
                if num:
                    break
                time.sleep(0.3)
            if num:
                add_labels_to_issue(repo_owner, repo_name, num,
                                    [priority, "phase-1"])

            print(f"  {title}: {status} {priority} {estimate}h (issue #{num})")
        else:
            print(f"  {title}: {status} {priority} {estimate}h (draft)")


CMDS = {
    "list": cmd_list,
    "get": cmd_get,
    "create-draft": cmd_create_draft,
    "move": cmd_move,
    "convert": cmd_convert,
    "setup": cmd_setup,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in CMDS:
        print(__doc__, file=sys.stderr)
        sys.exit(1)
    CMDS[sys.argv[1]](sys.argv[2:])


if __name__ == "__main__":
    main()
