"""
Issue 管理工具

用法:
  python3 scripts/issue.py create <owner/repo> <title> <body_file> [--label <name>]
  python3 scripts/issue.py close <owner/repo> <number>
  python3 scripts/issue.py comment <owner/repo> <number> <body_file>
  python3 scripts/issue.py list <owner/repo> [--state open|closed|all]
"""

import subprocess, json, sys, os

def gh(*args):
    r = subprocess.run(["gh"] + list(args), capture_output=True, text=True)
    if r.returncode != 0:
        print(f"错误: {r.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    return r.stdout.strip()

def cmd_create(args):
    """create <owner/repo> <title> <body_file> [--label <name>]"""
    if len(args) < 3:
        print("用法: issue.py create <owner/repo> <title> <body_file> [--label <name>]", file=sys.stderr)
        sys.exit(1)
    repo, title = args[0], args[1]
    body_file = args[2]
    labels = []
    for i, a in enumerate(args):
        if a == "--label" and i + 1 < len(args):
            labels.append(args[i + 1])

    body = ""
    if body_file:
        try:
            with open(body_file) as f:
                body = f.read().strip()
        except FileNotFoundError:
            pass

    cmd = ["issue", "create", "--repo", repo, "--title", title]
    if body:
        tf = f"/tmp/issue-body-{os.getpid()}.md"
        with open(tf, "w") as f:
            f.write(body)
        cmd += ["--body-file", tf]
    for l in labels:
        cmd += ["--label", l]

    url = gh(*cmd)
    num = url.split("/")[-1]
    print(f"已创建: #{num} {title}")
    print(f"  {url}")
    if body:
        os.unlink(tf)

def cmd_close(args):
    """close <owner/repo> <number>"""
    if len(args) < 2:
        print("用法: issue.py close <owner/repo> <number>", file=sys.stderr)
        sys.exit(1)
    gh("issue", "close", str(args[1]), "--repo", args[0])
    print(f"已关闭: #{args[1]} ({args[0]})")

def cmd_comment(args):
    """comment <owner/repo> <number> <body_file>"""
    if len(args) < 3:
        print("用法: issue.py comment <owner/repo> <number> <body_file>", file=sys.stderr)
        sys.exit(1)
    repo, num, body_file = args[0], args[1], args[2]
    try:
        with open(body_file) as f:
            body = f.read().strip()
    except FileNotFoundError:
        body = ""
    tf = "/tmp/issue-comment-%d.md" % os.getpid()
    with open(tf, "w") as f:
        f.write(body)
    gh("issue", "comment", str(num), "--repo", repo, "--body-file", tf)
    os.unlink(tf)
    print(f"已评论: #{num} ({repo})")

def cmd_list(args):
    """list <owner/repo> [--state open|closed|all]"""
    if len(args) < 1:
        print("用法: issue.py list <owner/repo> [--state open|closed|all]", file=sys.stderr)
        sys.exit(1)
    repo = args[0]
    state = "open"
    for i, a in enumerate(args):
        if a == "--state" and i + 1 < len(args):
            state = args[i + 1]
    jq_expr = ".[] | \"#\\(.number) \\(.state) \\(.title)\""
    r = subprocess.run(["gh", "issue", "list", "--repo", repo, "--state", state, "--limit", "30",
                        "--json", "number,title,state,labels", "--jq", jq_expr],
                       capture_output=True, text=True)
    if r.returncode == 0:
        print(r.stdout.strip())
    else:
        print(f"错误: {r.stderr.strip()}", file=sys.stderr)

CMDS = {
    "create": cmd_create,
    "close": cmd_close,
    "comment": cmd_comment,
    "list": cmd_list,
}

def main():
    if len(sys.argv) < 2 or sys.argv[1] not in CMDS:
        print(__doc__.strip(), file=sys.stderr)
        sys.exit(1)
    CMDS[sys.argv[1]](sys.argv[2:])

if __name__ == "__main__":
    main()
