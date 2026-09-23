#!/usr/bin/env python3
"""Compare a Nitrado DayZ mission folder with its GitHub repo, or download it.

The FTP deploy compares the repo against its own state file, never against
the server. Anything done to the server by hand — a file uploaded through
the Nitrado file browser, a file deleted, "Reset Mission-xml to default" —
is invisible to it. `drift` looks at the server itself.

    nitrado.py drift /path/to/mission-repo [--service ID] [--hash]
    nitrado.py pull  /path/to/empty-dir    [--service ID]

Needs NITRADO_TOKEN in the environment: a Nitrado long-life token with the
`service` and `file` scopes. Both commands only read from the server.

Exit status: 0 clean, 1 drift found, 2 could not run.
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

API = "https://api.nitrado.net"
STATE = ".ftp-deploy-sync-state.json"
ACTION = "SamKirkland/FTP-Deploy-Action"
DRIFTIGNORE = ".driftignore"
# The deploy runner's clock and Nitrado's are not the same clock.
CLOCK_SLACK = 120
WALKERS = 4


class Fail(Exception):
    pass


def glob_to_regex(pattern):
    """Translate the action's exclude globs (minimatch subset) to a regex.

    The action matches with `matchBase: true`, so a pattern with no slash
    matches the file name at any depth: `.gitignore` excludes `a/.gitignore`.
    """
    out, i = ("(?:.*/)?" if "/" not in pattern else ""), 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out += "(?:.*/)?"; i += 3
        elif pattern.startswith("**", i):
            out += ".*"; i += 2
        elif pattern[i] == "*":
            out += "[^/]*"; i += 1
        elif pattern[i] == "?":
            out += "[^/]"; i += 1
        else:
            out += re.escape(pattern[i]); i += 1
    return re.compile(out)


def api(path, **params):
    token = os.environ.get("NITRADO_TOKEN")
    if not token:
        raise Fail("NITRADO_TOKEN is not set")
    url = f"{API}{path}" + (f"?{urllib.parse.urlencode(params)}" if params else "")
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            body = json.load(r)
    except urllib.error.HTTPError as e:
        raise Fail(f"Nitrado API {e.code} on {path}")
    except (urllib.error.URLError, OSError, ValueError) as e:
        raise Fail(f"Nitrado API unreachable on {path}: {e}")
    if not isinstance(body, dict) or body.get("status") != "success":
        raise Fail(f"Nitrado API: {body.get('message', body)}")
    return body["data"]


def find_service(service_id):
    if service_id is None:
        dayz = [s for s in api("/services")["services"]
                if "dayz" in str(s.get("details", {}).get("game", "")).lower()]
        if len(dayz) != 1:
            # details.name is Nitrado's product label ("Gameserver - 26 Slots"),
            # which cannot tell two servers apart; the hostname can.
            def label(s):
                try:
                    cfg = api(f"/services/{s['id']}/gameservers")["gameserver"]["settings"]["config"]
                    return f"{cfg.get('mission', '?'):28} {cfg.get('hostname', '')}"
                except (Fail, KeyError, TypeError):
                    return "?"
            lines = "\n".join(f"  {s['id']}  {label(s)}" for s in dayz)
            raise Fail(f"{len(dayz)} DayZ services on this token; pass --service:\n{lines}")
        service_id = dayz[0]["id"]
    gs = api(f"/services/{service_id}/gameservers")["gameserver"]
    mission = gs["settings"]["config"]["mission"]
    root = f"/games/{gs['username']}/ftproot/dayzxb_missions/{mission}"
    return service_id, root, gs


def armed(gs):
    """Nitrado toggles that will change the server at its next restart.

    Both switch themselves off after firing, so they are only visible here in
    the window between being set and the restart.
    """
    out = []
    if str(gs["settings"].get("general", {}).get("resetmission")).lower() == "true":
        out.append("'Reset Mission-xml to default' is ON — the next restart replaces the "
                   "deployed mission files, and the deploy's state file will not know")
    if str(gs["settings"].get("savegame", {}).get("wipe_on_next_restart")).lower() == "true":
        out.append("'Storage wipe' is ON — the next restart erases the world: bases, "
                   "stashes, vehicles and characters")
    return out


def walk(service_id, root):
    """Every file under root: relpath -> {size, modified_at}.

    One list call per directory, and a call takes anywhere from 0.4 to 12
    seconds, so a mission with 40 directories is minutes serially. A few in
    flight at once keeps it under a minute without leaning on the API.
    """
    files, todo, seen = {}, [root], 0
    list_dir = lambda d: api(f"/services/{service_id}/gameservers/file_server/list",
                             dir=d)["entries"]
    with ThreadPoolExecutor(max_workers=WALKERS) as pool:
        while todo:
            batch, todo = todo, []
            for entries in pool.map(list_dir, batch):
                for e in entries:
                    if e["type"] == "dir":
                        todo.append(e["path"])
                    else:
                        files[e["path"][len(root) + 1:]] = {"size": e["size"],
                                                             "modified_at": e["modified_at"]}
            seen += len(batch)
            print(f"  listed {seen} folder(s), {len(files)} file(s)...",
                  file=sys.stderr, flush=True)
    return files


def download(service_id, path):
    url = api(f"/services/{service_id}/gameservers/file_server/download",
              file=path)["token"]["url"]
    try:
        with urllib.request.urlopen(url, timeout=600) as r:
            return r.read()
    except (urllib.error.URLError, OSError) as e:
        raise Fail(f"download failed for {path}: {e}")


def parse_state(raw):
    try:
        state = json.loads(raw)
        state["data"], state["generatedTime"]
        return state
    except (ValueError, TypeError, KeyError) as e:
        raise Fail(f"{STATE} on the server is unreadable ({e!r}); delete it and "
                   "publish a Release to rebuild it")


def repo_files(repo):
    """Tracked files as they are on disk: relpath -> (size, sha256)."""
    out = subprocess.run(["git", "ls-files", "-z"], cwd=repo, capture_output=True)
    if out.returncode:
        raise Fail(f"not a git repo: {repo}")
    files = {}
    for rel in out.stdout.decode().split("\0"):
        p = Path(repo) / rel
        if rel and p.is_file():
            data = p.read_bytes()
            files[rel] = (len(data), hashlib.sha256(data).hexdigest())
    return files


def parse_excludes(text):
    """The `exclude: |` block; blank lines inside it do not end it (YAML)."""
    m = re.search(r"^(\s*)exclude:\s*\|[-+]?\s*\n((?:(?:\1\s+.*|\s*)(?:\n|$))+)", text, re.M)
    if not m:
        return None
    return [l.strip() for l in m.group(2).splitlines()
            if l.strip() and not l.strip().startswith("#")]


def repo_excludes(repo):
    for wf in sorted((Path(repo) / ".github" / "workflows").glob("*.y*ml")):
        text = wf.read_text(encoding="utf-8")
        if ACTION in text:
            found = parse_excludes(text)
            if found is not None:
                return found
    # The action's own defaults, used when the workflow sets no exclude list.
    return ["**/.git*", "**/.git*/**", "**/node_modules/**"]


def read_driftignore_text(text):
    return [l.strip() for l in text.splitlines()
            if l.strip() and not l.strip().startswith("#")]


def repo_driftignore(repo):
    """Paths something other than the deploy writes — a bot, a scheduler.

    Those files differ from the repo by design, so reporting them as drift
    on every run would bury the drift that matters.
    """
    p = Path(repo) / DRIFTIGNORE
    return read_driftignore_text(p.read_text(encoding="utf-8")) if p.is_file() else []


def compare(repo, server, state, excludes, managed=()):
    found = _compare(repo, server, state, excludes)
    pats = [glob_to_regex(m) for m in managed]
    is_managed = lambda p: any(r.fullmatch(p) for r in pats)
    out, seen = [], set()
    for kind, p, detail in found:
        if not is_managed(p):
            out.append((kind, p, detail))
        elif p not in seen:
            seen.add(p)
            out.append(("managed", p, f"listed in {DRIFTIGNORE} ({kind})"))
    return out


def _compare(repo, server, state, excludes):
    pats = [glob_to_regex(e) for e in excludes]
    excluded = lambda p: any(r.fullmatch(p) for r in pats)
    repo = {p: v for p, v in repo.items() if not excluded(p)}
    server_all, server = server, {p: v for p, v in server.items() if p != STATE}
    found = []
    if state is None:
        for p in sorted(set(server) - set(repo)):
            found.append(("stray", p, "on server, not in repo"))
        for p in sorted(set(repo) - set(server)):
            found.append(("missing", p, "in repo, not on server"))
        for p in sorted(set(repo) & set(server)):
            if repo[p][0] != server[p]["size"]:
                found.append(("modified", p, f"size {server[p]['size']} on server, "
                              f"{repo[p][0]} in repo"))
        return found
    # The action drops excluded paths from its record before comparing, so it
    # never deletes them; neither should drift predict that it will.
    known = {e["name"]: e for e in state["data"]
             if e.get("type") == "file" and not excluded(e["name"])}
    # generatedTime is stamped before the upload starts, and the state file is
    # uploaded last, so its own timestamp is when the deploy finished.
    deployed_at = server_all.get(STATE, {}).get("modified_at", state["generatedTime"] / 1000)
    # A Mac checkout is case-insensitive and Nitrado is not, so a rename that
    # only changes case leaves two files on the server.
    by_case = {q.lower(): q for q in repo}
    for p in sorted(set(server) - set(known)):
        twin = by_case.get(p.lower())
        if twin and twin != p:
            found.append(("stray", p, f"differs only by case from the repo's {twin} — "
                          "the server has both, and no deploy will remove this one"))
        else:
            found.append(("stray", p, "on server, never uploaded by the deploy — "
                          "no deploy will ever remove it"))
    for p in sorted(set(known) - set(server)):
        if p in repo:
            found.append(("missing", p, "deploy believes it is on the server; it is not, "
                          "and will not be re-sent until its content changes"))
    for p in sorted(set(known) & set(server)):
        if server[p]["size"] != known[p]["size"]:
            found.append(("modified", p, "changed on the server since the last deploy"))
        elif server[p]["modified_at"] > deployed_at + CLOCK_SLACK:
            found.append(("touched", p, "written on the server after the last deploy; "
                          "same size — rerun with --hash to confirm"))
    for p in sorted(set(repo) - set(known)):
        found.append(("pending-upload", p, "new in repo, not yet released"))
    for p in sorted(set(repo) & set(known)):
        if repo[p][1] != known[p]["hash"]:
            found.append(("pending-upload", p, "changed in repo, not yet released"))
    for p in sorted(set(known) - set(repo)):
        if p in server:
            found.append(("pending-delete", p, "removed from repo; the next release "
                          "deletes it from the server"))
    return found


def cmd_drift(args):
    if not Path(args.repo).is_dir():
        raise Fail(f"not a directory: {args.repo}")
    service_id, root, gs = find_service(args.service)
    repo = repo_files(args.repo)
    server = walk(service_id, root)
    state = parse_state(download(service_id, f"{root}/{STATE}")) if STATE in server else None
    found = compare(repo, server, state, repo_excludes(args.repo),
                    repo_driftignore(args.repo))
    if args.hash and state is None:
        print("--hash skipped: no deploy state to compare against", file=sys.stderr)
    if args.hash and state:
        known = {e["name"]: e["hash"] for e in state["data"] if e["type"] == "file"}
        confirmed = []
        for kind, p, detail in found:
            if kind == "touched":
                digest = hashlib.sha256(download(service_id, f"{root}/{p}")).hexdigest()
                if digest != known[p]:
                    confirmed.append(("modified", p, "content differs from the last deploy"))
                continue
            confirmed.append((kind, p, detail))
        found = confirmed
    print(f"server: {root}  ({len(server)} files)")
    for warning in armed(gs):
        print(f"ARMED           {warning}")
    if state is None:
        print("no deploy state on the server — no deploy has run; comparing by size only")
    for kind, p, detail in found:
        print(f"{kind:15} {p}  — {detail}")
    bad = [f for f in found if f[0] in ("stray", "missing", "modified")]
    print(f"\n{len(bad)} drift finding(s), {len(found) - len(bad)} pending/unconfirmed/managed")
    return 1 if bad or armed(gs) else 0


def cmd_pull(args):
    dest = Path(args.dest)
    if dest.exists() and (not dest.is_dir() or any(dest.iterdir())):
        raise Fail(f"{dest} is not an empty directory — refusing to overwrite")
    service_id, root, _ = find_service(args.service)
    files = walk(service_id, root)
    for rel in sorted(files):
        if rel == STATE:
            continue  # the deploy's bookkeeping, not mission content
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(download(service_id, f"{root}/{rel}"))
        print(f"  {rel}")
    print(f"\n{len(files) - (STATE in files)} file(s) from {root}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="command", required=True)
    d = sub.add_parser("drift", help="compare the server with the repo")
    d.add_argument("repo")
    d.add_argument("--service", type=int)
    d.add_argument("--hash", action="store_true",
                   help="download same-size files written after the last deploy and hash them")
    p = sub.add_parser("pull", help="download the mission folder into an empty directory")
    p.add_argument("dest")
    p.add_argument("--service", type=int)
    args = ap.parse_args()
    try:
        return cmd_drift(args) if args.command == "drift" else cmd_pull(args)
    except Fail as e:
        print(e, file=sys.stderr)
        return 2
    except (KeyError, TypeError) as e:
        print(f"unexpected Nitrado API response: {e!r}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
