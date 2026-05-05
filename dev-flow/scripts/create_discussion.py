"""
Create / Update a GitHub Discussion in a plan repo, with category fallback.

根据 SKILL.md 中的 Discussion Category 选择规则自动 fallback:

  | 用途       | 首选         | Fallback      |
  |------------|-------------|---------------|
  | Ideas      | Ideas       | — (一定存在)   |
  | Requirements | Requirements | Show and tell |
  | Tech Spec  | Tech Spec   | General       |

用法:
  创建: python3 scripts/create_discussion.py <owner/repo> <category_slug> "<title>" [body_file]
  更新: python3 scripts/create_discussion.py --update <discussion_id> [body_file] [--title "新标题"]

参数:
  owner/repo     — 如 poloxue/ghpm
  category_slug  — ideas / requirements / tech-spec
  title          — Discussion 标题 (用引号包裹)
  body_file      — (可选) 正文文件路径。不传则从 stdin 读取
  --update       — 更新已有 Discussion 的正文（和可选的标题）
  --title        — (更新模式) 同时更新标题

示例:
  # 创建: 从文件读取正文
  python3 scripts/create_discussion.py poloxue/ghpm tech-spec "标题" /path/to/body.md

  # 创建: 从管道输入正文
  echo "正文内容" | python3 scripts/create_discussion.py poloxue/ghpm ideas "想法标题"

  # 更新: 用文件内容更新 Discussion 正文
  python3 scripts/create_discussion.py --update D_kwAC8W9- /path/to/body.md

  # 更新: 从 stdin 更新正文，同时改标题
  cat body.md | python3 scripts/create_discussion.py --update D_kwAC8W9- --title "新标题"

前置条件:
  - gh CLI 已登录, token 有 repo 权限
  - 仓库已启用 Discussions

输出:
  成功时打印 Discussion URL, 退出码 0
  失败时打印错误信息到 stderr, 退出码非 0
"""

import subprocess, json, sys, tempfile, os

FALLBACKS = {
    "ideas":        ["Ideas"],
    "requirements": ["Requirements", "Show and tell"],
    "tech-spec":    ["Tech Spec", "General"],
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
    return json.loads(r.stdout)


def escape_gql_string(s):
    """转义 GraphQL 常规字符串中的特殊字符"""
    return s.replace("\\", "\\\\").replace('"', '\\"')


def get_categories(owner, repo):
    """查询仓库所有 discussion category"""
    q = ('{ repository(owner: "' + owner + '", name: "' + repo
         + '") { discussionCategories(first: 20) { nodes { id name slug } } } }')
    result = gql(q)
    return result.get("data", {}).get("repository", {}).get("discussionCategories", {}).get("nodes", [])


def find_category(categories, slug):
    """按 slug 查找 category"""
    for c in categories:
        if c["slug"] == slug:
            return c
    return None


def create_discussion(repo_id, category_id, title, body):
    """创建 Discussion"""
    body_escaped = escape_gql_string(body)
    title_escaped = escape_gql_string(title)
    q = ('mutation { createDiscussion(input: { repositoryId: "' + repo_id
         + '", categoryId: "' + category_id
         + '", title: "' + title_escaped
         + '", body: "' + body_escaped + '" }) { discussion { id url } } }')
    result = gql(q)
    return result["data"]["createDiscussion"]["discussion"]


def update_discussion(discussion_id, body, title=None):
    """更新已有 Discussion 的正文和可选标题。
    用 GraphQL block string (\"\"\") 避免特殊字符转义问题。"""
    # 转义 block string 中唯一需要处理的字符
    body_safe = body.replace('"""', '\\"""')
    lines = [
        "mutation {",
        "  updateDiscussion(input: {",
        f'    discussionId: "{discussion_id}"',
        '    body: """' + body_safe + '"""',
    ]
    if title:
        title_safe = escape_gql_string(title)
        lines.append(f'    title: "{title_safe}"')
    lines.append("  }) {")
    lines.append("    discussion {")
    lines.append("      id")
    lines.append("      url")
    lines.append("    }")
    lines.append("  }")
    lines.append("}")
    q = "\n".join(lines)
    result = gql_file(q)
    return result["data"]["updateDiscussion"]["discussion"]


def get_repo_id(owner, repo):
    q = ('{ repository(owner: "' + owner + '", name: "' + repo + '") { id } }')
    return gql(q)["data"]["repository"]["id"]


def read_body(body_file):
    """从文件或 stdin 读取正文"""
    if body_file:
        try:
            with open(body_file) as f:
                return f.read().strip()
        except FileNotFoundError:
            print(f"错误: 文件不存在: {body_file}", file=sys.stderr)
            sys.exit(1)
    else:
        return sys.stdin.read().strip()


def main():
    args = sys.argv[1:]

    # --update 模式
    if args and args[0] == "--update":
        if len(args) < 2:
            print("错误: --update 需要 discussion_id 参数", file=sys.stderr)
            sys.exit(1)
        discussion_id = args[1]
        body_file = args[2] if len(args) > 2 and not args[2].startswith("--") else None
        new_title = None
        for i, a in enumerate(args):
            if a == "--title" and i + 1 < len(args):
                new_title = args[i + 1]

        body = read_body(body_file)
        if not body:
            print("错误: 正文不能为空", file=sys.stderr)
            sys.exit(1)

        result = update_discussion(discussion_id, body, new_title)
        print("Discussion 已更新:")
        print(f"  URL: {result['url']}")
        return

    # 创建模式
    if len(args) < 3:
        print(__doc__, file=sys.stderr)
        sys.exit(1)

    repo_full = args[0]
    cat_slug = args[1].lower()
    title = args[2]
    body_file = args[3] if len(args) > 3 else None

    if "/" not in repo_full:
        print(f"错误: 仓库格式须为 owner/repo, 收到: {repo_full}", file=sys.stderr)
        sys.exit(1)

    owner, repo = repo_full.split("/", 1)
    body = read_body(body_file)

    if not title:
        print("错误: 标题不能为空", file=sys.stderr)
        sys.exit(1)

    if not body:
        print("错误: 正文不能为空", file=sys.stderr)
        sys.exit(1)

    # 获取 category 列表
    categories = get_categories(owner, repo)
    if not categories:
        print(f"错误: 无法获取 {repo_full} 的 Discussion 分类列表", file=sys.stderr)
        sys.exit(1)

    # 按 fallback 规则找 category
    candidates = FALLBACKS.get(cat_slug, [cat_slug])
    selected = None
    for name in candidates:
        slug = name.lower().replace(" ", "-").replace("--", "-")
        selected = find_category(categories, slug)
        if selected:
            break

    if not selected:
        print(f"错误: 找不到匹配的分类 '{cat_slug}', 可用分类: "
              f"{[c['name'] for c in categories]}", file=sys.stderr)
        sys.exit(1)

    # 唯一性判断: 如果 slug 是 fallback, 在标题加前缀
    used_fallback = selected["name"] != candidates[0]
    if used_fallback:
        prefix_map = {
            "requirements": "[Requirements] ",
            "tech-spec":    "[Tech Spec] ",
        }
        prefix = prefix_map.get(cat_slug, "")
        if prefix and not title.startswith(prefix):
            title = prefix + title

    # 创建
    repo_id = get_repo_id(owner, repo)
    result = create_discussion(repo_id, selected["id"], title, body)

    print("Discussion 已创建:")
    print(f"  URL: {result['url']}")
    if used_fallback:
        print(f"  分类: {candidates[0]} (不存在) → {selected['name']} (fallback)")
    else:
        print(f"  分类: {selected['name']}")


if __name__ == "__main__":
    main()
