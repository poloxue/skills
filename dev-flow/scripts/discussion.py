"""
Discussion 管理工具 (增/改/查/开关)

支持 plan repo 的 Discussion CRUD 和状态切换，自动处理 category fallback。

用法:
  python3 scripts/discussion.py list <owner/repo> [--category <slug>]
  python3 scripts/discussion.py get <discussion-id>
  python3 scripts/discussion.py create <owner/repo> <category> "<title>" [body_file]
  python3 scripts/discussion.py update <discussion-id> [body_file] [--title "新标题"]
  python3 scripts/discussion.py close <discussion-id>
  python3 scripts/discussion.py reopen <discussion-id>

category 参数:
  ideas / requirements / tech-spec  (自动 fallback)

示例:
  # 列出 Discussions
  python3 scripts/discussion.py list poloxue/ghpm
  python3 scripts/discussion.py list poloxue/ghpm --category ideas

  # 查看详情
  python3 scripts/discussion.py get D_kwDOSUjJr84AmKi1

  # 创建
  echo "正文" | python3 scripts/discussion.py create poloxue/ghpm ideas "想法标题"
  python3 scripts/discussion.py create poloxue/ghpm requirements "需求" /path/to/prd.md

  # 更新
  python3 scripts/discussion.py update D_kwDOSUjJr84AmKi1 new-body.md
  cat new.md | python3 scripts/discussion.py update D_kwAC8W9- --title "新标题"

  # 开关
  python3 scripts/discussion.py close D_kwDOSUjJr84AmKi1
  python3 scripts/discussion.py reopen D_kwDOSUjJr84AmKi1
"""

import subprocess, json, sys, tempfile, os

FALLBACKS = {
    "ideas": ["Ideas"],
    "requirements": ["Requirements", "Show and tell"],
    "tech-spec": ["Tech Spec", "General"],
}


def gql(query):
    r = subprocess.run(
        ["gh", "api", "graphql", "-f", f"query={query}"],
        capture_output=True, text=True
    )
    return json.loads(r.stdout)


def gql_file(query):
    """用文件方式执行 GraphQL (处理特殊字符多的 body)"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".graphql", delete=False) as f:
        f.write(query)
        tmp = f.name
    r = subprocess.run(
        ["gh", "api", "graphql", "-F", f"query=@{tmp}"],
        capture_output=True, text=True
    )
    os.unlink(tmp)
    if r.returncode != 0:
        print(f"API 错误: {r.stderr}", file=sys.stderr)
        sys.exit(1)
    return json.loads(r.stdout)


def esc(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


def read_body(body_file):
    if body_file:
        try:
            with open(body_file) as f:
                return f.read().strip()
        except FileNotFoundError:
            print(f"错误: 文件不存在: {body_file}", file=sys.stderr)
            sys.exit(1)
    else:
        return sys.stdin.read().strip()


# ── list ──

def cmd_list(args):
    """list <owner/repo>"""
    if len(args) < 1:
        print("用法: discussion.py list <owner/repo> [--category <slug>]", file=sys.stderr)
        sys.exit(1)
    repo_full = args[0]
    owner, repo = repo_full.split("/", 1)
    cat_filter = ""
    for i, a in enumerate(args):
        if a == "--category" and i + 1 < len(args):
            cat_filter = args[i + 1]

    q = ('{ repository(owner: "' + owner + '", name: "' + repo
         + '") { discussions(first: 50, orderBy: {field: CREATED_AT, direction: DESC})'
         + '{ nodes { id title url createdAt isAnswered category { name slug }'
         + ' author { login } comments { totalCount } } } } }')
    result = gql(q)
    nodes = result["data"]["repository"]["discussions"]["nodes"]
    for d in nodes:
        if cat_filter and d["category"]["slug"] != cat_filter:
            continue
        print(f"{d['id']}")
        print(f"  标题: {d['title']}")
        print(f"  分类: {d['category']['name']}")
        print(f"  作者: {d['author']['login']}  |  回复: {d['comments']['totalCount']}")
        print(f"  URL:  {d['url']}")
        print()


# ── get ──

def cmd_get(args):
    """get <discussion-id>"""
    if len(args) < 1:
        print("用法: discussion.py get <discussion-id>", file=sys.stderr)
        sys.exit(1)
    did = args[0]
    q = ('{ node(id: "' + did + '") { ... on Discussion { id title url body '
         'isAnswered closed category { name } '
         'comments(first: 50) { nodes { id body author { login } createdAt'
         ' replyTo { id } } } } } }')
    result = gql(q)
    d = result["data"]["node"]
    print(f"标题: {d['title']}")
    print(f"分类: {d['category']['name']}  |  已关闭: {d['closed']}")
    print(f"URL:  {d['url']}")
    print()
    print(d["body"])
    print()
    print("--- 评论 ---")
    for c in d["comments"]["nodes"]:
        prefix = "  > " if c.get("replyTo") else "  "
        print(f"{prefix}{c['author']['login']} ({c['createdAt'][:10]}):")
        print(f"{prefix}{c['body'][:200]}")
        print()


# ── create ──

def cmd_create(args):
    """create <owner/repo> <category> <title> [body_file]"""
    if len(args) < 2:
        print("用法: discussion.py create <owner/repo> <category> <title> [body_file]", file=sys.stderr)
        sys.exit(1)
    repo_full, cat_slug = args[0], args[1].lower()
    title = args[2]
    body_file = args[3] if len(args) > 3 else None
    owner, repo = repo_full.split("/", 1)
    body = read_body(body_file)

    if not title or not body:
        print("错误: 标题和正文不能为空", file=sys.stderr)
        sys.exit(1)

    # 查 category
    q = ('{ repository(owner: "' + owner + '", name: "' + repo
         + '") { discussionCategories(first: 20) { nodes { id name slug } } } }')
    cats = gql(q)["data"]["repository"]["discussionCategories"]["nodes"]

    candidates = FALLBACKS.get(cat_slug, [cat_slug])
    selected = None
    for name in candidates:
        slug = name.lower().replace(" ", "-").replace("--", "-")
        for c in cats:
            if c["slug"] == slug:
                selected = c
                break
        if selected:
            break
    if not selected:
        print(f"错误: 找不到分类 '{cat_slug}', 可用: {[c['name'] for c in cats]}", file=sys.stderr)
        sys.exit(1)

    used_fallback = selected["name"] != candidates[0]
    if used_fallback:
        prefixes = {"requirements": "[Requirements] ", "tech-spec": "[Tech Spec] "}
        prefix = prefixes.get(cat_slug, "")
        if prefix and not title.startswith(prefix):
            title = prefix + title

    q_repo = ('{ repository(owner: "' + owner + '", name: "' + repo + '") { id } }')
    repo_id = gql(q_repo)["data"]["repository"]["id"]

    q_mut = ('mutation { createDiscussion(input: { repositoryId: "' + repo_id
             + '", categoryId: "' + selected['id']
             + '", title: "' + esc(title)
             + '", body: "' + esc(body) + '" }) { discussion { id url } } }')
    result = gql(q_mut)["data"]["createDiscussion"]["discussion"]

    print(f"已创建: {result['url']}")
    if used_fallback:
        print(f"  分类: {candidates[0]} (不存在) → {selected['name']} (fallback)")


# ── update ──

def cmd_update(args):
    """update <discussion-id> [body_file] [--title]"""
    did = args[0]
    rest = args[1:]
    body_file = rest[0] if rest and not rest[0].startswith("--") else None
    new_title = None
    for i, a in enumerate(rest):
        if a == "--title" and i + 1 < len(rest):
            new_title = rest[i + 1]

    body = read_body(body_file) if body_file or not sys.stdin.isatty() else None
    if not body and not new_title:
        print("错误: 至少提供正文或 --title", file=sys.stderr)
        sys.exit(1)

    lines = ["mutation {", "  updateDiscussion(input: {", f'    discussionId: "{did}"']
    if body:
        lines.append('    body: """' + body.replace('"""', '\\"""') + '"""')
    if new_title:
        lines.append(f'    title: "{esc(new_title)}"')
    lines += ["  }) {", "    discussion { id url }", "  }", "}"]
    result = gql_file("\n".join(lines))["data"]["updateDiscussion"]["discussion"]
    print(f"已更新: {result['url']}")


# ── close ──

def cmd_close(args):
    if len(args) < 1:
        print("用法: discussion.py close <discussion-id>", file=sys.stderr)
        sys.exit(1)
    q = 'mutation { closeDiscussion(input: { discussionId: "' + args[0] + '" }) { discussion { id url } } }'
    result = gql(q)["data"]["closeDiscussion"]["discussion"]
    print(f"已关闭: {result['url']}")


# ── reopen ──

def cmd_reopen(args):
    if len(args) < 1:
        print("用法: discussion.py reopen <discussion-id>", file=sys.stderr)
        sys.exit(1)
    q = 'mutation { reopenDiscussion(input: { discussionId: "' + args[0] + '" }) { discussion { id url } } }'
    result = gql(q)["data"]["reopenDiscussion"]["discussion"]
    print(f"已重新打开: {result['url']}")


CMDS = {
    "list": cmd_list,
    "get": cmd_get,
    "create": cmd_create,
    "update": cmd_update,
    "close": cmd_close,
    "reopen": cmd_reopen,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in CMDS:
        print(__doc__, file=sys.stderr)
        sys.exit(1)
    CMDS[sys.argv[1]](sys.argv[2:])


if __name__ == "__main__":
    main()
