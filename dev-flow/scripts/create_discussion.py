"""
Create a GitHub Discussion in a plan repo, with category fallback.

根据 SKILL.md 中的 Discussion Category 选择规则自动 fallback:

  | 用途       | 首选         | Fallback      |
  |------------|-------------|---------------|
  | Ideas      | Ideas       | — (一定存在)   |
  | Requirements | Requirements | Show and tell |
  | Tech Spec  | Tech Spec   | General       |

用法:
  python3 scripts/create_discussion.py <owner/repo> <category_slug> "<title>" [body_file]

参数:
  owner/repo     — 如 poloxue/ghpm
  category_slug  — ideas / requirements / tech-spec
  title          — Discussion 标题 (用引号包裹)
  body_file      — (可选) 正文文件路径。不传则从 stdin 读取

示例:
  # 从文件读取正文
  python3 scripts/create_discussion.py poloxue/ghpm tech-spec "标题" /path/to/body.md

  # 从管道输入正文
  echo "正文内容" | python3 scripts/create_discussion.py poloxue/ghpm ideas "想法标题"

前置条件:
  - gh CLI 已登录, token 有 repo 权限
  - 仓库已启用 Discussions

输出:
  成功时打印 Discussion URL, 退出码 0
  失败时打印错误信息到 stderr, 退出码非 0
"""

import subprocess, json, sys

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
    # 转义 body 中的特殊字符以适应 GraphQL string
    body_escaped = body.replace("\\", "\\\\").replace('"', '\\"')
    q = ('mutation { createDiscussion(input: { repositoryId: "' + repo_id
         + '", categoryId: "' + category_id
         + '", title: "' + title.replace("\\", "\\\\").replace('"', '\\"')
         + '", body: "' + body_escaped + '" }) { discussion { id url } } }')
    result = gql(q)
    return result["data"]["createDiscussion"]["discussion"]


def get_repo_id(owner, repo):
    q = ('{ repository(owner: "' + owner + '", name: "' + repo + '") { id } }')
    return gql(q)["data"]["repository"]["id"]


def main():
    if len(sys.argv) < 3:
        print(__doc__, file=sys.stderr)
        sys.exit(1)

    repo_full = sys.argv[1]
    cat_slug = sys.argv[2].lower()
    title = sys.argv[3] if len(sys.argv) > 3 else ""
    body_file = sys.argv[4] if len(sys.argv) > 4 else None

    if "/" not in repo_full:
        print(f"错误: 仓库格式须为 owner/repo, 收到: {repo_full}", file=sys.stderr)
        sys.exit(1)

    owner, repo = repo_full.split("/", 1)

    # 读取正文
    if body_file:
        try:
            with open(body_file) as f:
                body = f.read().strip()
        except FileNotFoundError:
            print(f"错误: 文件不存在: {body_file}", file=sys.stderr)
            sys.exit(1)
    else:
        body = sys.stdin.read().strip()

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
        # name -> slug (GitHub 自动生成)
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
