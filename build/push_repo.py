# -*- coding: utf-8 -*-
"""Push grimm-fiabe site + audio to new GitHub repo and enable Pages.
Run AFTER audio generation completes. Token read from mcp.json (not hardcoded).
"""
import json, os, subprocess, sys, ssl, urllib.request

ROOT = r"D:/workbuddy工作区/2026-08-23-21-28-02/grimm-fiabe"
REPO = "realrentao/fiabe-di-grimm"
API = "https://api.github.com"


def tok():
    d = json.load(open(r"C:\Users\迪丽希斯\.workbuddy\mcp.json", encoding="utf-8"))
    g = d["mcpServers"]["github"]["env"]
    return g.get("GITHUB_PERSONAL_ACCESS_TOKEN", "")


def sh(cmd):
    print("+", cmd if isinstance(cmd, str) else " ".join(cmd))
    r = subprocess.run(cmd, cwd=ROOT, shell=isinstance(cmd, str),
                       capture_output=True, text=True)
    if r.stdout.strip():
        print(r.stdout.strip()[:2000])
    if r.returncode != 0:
        print("!!! STDERR:", r.stderr.strip()[:2000])
        sys.exit(1)
    return r


def enable_pages(token):
    data = json.dumps({"source": {"branch": "main", "path": "/"}}).encode()
    req = urllib.request.Request(
        f"{API}/repos/{REPO}/pages", data=data,
        headers={"Authorization": f"token {token}", "Accept": "application/vnd.github+json",
                 "User-Agent": "w"}, method="POST")
    try:
        with urllib.request.urlopen(req, context=ssl.create_default_context(), timeout=60) as r:
            j = json.loads(r.read().decode())
            print("PAGES:", j.get("html_url") or j)
    except Exception as e:
        print("PAGES enable note:", e)


def main():
    t = tok()
    if not t:
        print("NO TOKEN"); sys.exit(1)
    sh(["git", "init", "-q"])
    sh(["git", "config", "user.email", "bot@workbuddy.local"])
    sh(["git", "config", "user.name", "WorkBuddy"])
    sh(["git", "add", "-A"])
    # commit (allow if nothing changed)
    c = subprocess.run(["git", "commit", "-q", "-m", "Fiabe di Grimm — sito di lettura bilingue IT/ZH + audio"],
                       cwd=ROOT, capture_output=True, text=True)
    print(c.stdout.strip()[-500:] or c.stderr.strip()[-500:] or "(committed)")
    url = f"https://{t}@github.com/{REPO}.git"
    sh(["git", "push", "-f", url, "HEAD:main"])
    print("PUSHED to main")
    enable_pages(t)
    print("DONE -> https://" + REPO.replace("realrentao/", "realrentao.github.io/"))


if __name__ == "__main__":
    main()
