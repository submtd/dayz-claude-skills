#!/usr/bin/env python3
"""Audit a DayZ mission repo's GitHub-to-Nitrado deploy.

The deploy fails silently in two places: a tag with no published Release
ships nothing, and a Release whose workflow run failed looks shipped on the
Releases page. This script finds both, and lints the deploy workflow for the
settings that wipe a server or upload the .git directory to it.

    audit.py /path/to/mission-repo

Release checks need the `gh` CLI, authenticated, run against the repo's
GitHub remote. Without it only the workflow lint runs.

Exit status: 0 clean (warnings/notes allowed), 1 errors found, 2 could not run.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ACTION = "SamKirkland/FTP-Deploy-Action"
DEFAULT_STATE = ".ftp-deploy-sync-state.json"
# Uploading these to the game server is a leak or a waste, never intended.
REQUIRED_EXCLUDES = (".git/**", ".github/**")
ADVISED_EXCLUDES = ("**/*.md",)


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


def workflow_input(text, key):
    m = re.search(rf"^\s*{re.escape(key)}:\s*(.+?)\s*(?:#.*)?$", text, re.M)
    return m.group(1).strip().strip("'\"") if m else None


def workflow_excludes(text):
    m = re.search(r"^(\s*)exclude:\s*\|\s*\n((?:\1\s+.*\n?)+)", text, re.M)
    if not m:
        return None
    return [l.strip() for l in m.group(2).splitlines()
            if l.strip() and not l.strip().startswith("#")]


def lint_workflow(text):
    found = []
    if not re.search(r"release:\s*\n\s*types:\s*\[\s*published\s*\]", text):
        found.append(("error", "deploy is not triggered by `release: types: [published]` "
                      "— publishing a Release will not deploy"))
    if re.search(r"^\s*push:", text, re.M):
        found.append(("warn", "workflow also runs on push — every commit to main deploys"))
    clean = workflow_input(text, "dangerous-clean-slate")
    if clean is not None and clean.lower() != "false":
        found.append(("error", f"dangerous-clean-slate is {clean} — every deploy wipes the "
                      "mission folder, including files not in the repo"))
    state = workflow_input(text, "state-name")
    if state and state != DEFAULT_STATE:
        found.append(("note", f"state-name is {state}; changing it orphans the old state "
                      "file and forces one full upload"))
    local = workflow_input(text, "local-dir")
    if local and local not in ("./", "."):
        found.append(("note", f"local-dir is {local}; the skill assumes the repo root is "
                      "the mission folder"))
    server = workflow_input(text, "server-dir")
    if server and "${{" not in server and not server.endswith("/"):
        found.append(("error", f"server-dir {server} must end with /"))
    excludes = workflow_excludes(text)
    if excludes is None:
        found.append(("warn", "no exclude list — the action's defaults apply; state the "
                      "list explicitly so docs and tooling never reach the server"))
    else:
        for want in REQUIRED_EXCLUDES:
            if want not in excludes:
                found.append(("error", f"exclude list is missing {want} — it would be "
                              "uploaded to the game server"))
        for want in ADVISED_EXCLUDES:
            if want not in excludes:
                found.append(("warn", f"exclude list is missing {want}"))
    return found


def audit_releases(tags, releases, runs, ancestors):
    """ancestors[(a, b)] is True when tag a's commit is an ancestor of tag b's."""
    found = []
    released = {r["tagName"]: r for r in releases}
    latest_run = {}
    for run in runs:  # gh lists newest first; keep the first seen per tag
        latest_run.setdefault(run["headBranch"], run)
    deployed = [t for t in tags if t in released and not released[t]["isDraft"]
                and latest_run.get(t, {}).get("conclusion") == "success"]
    for tag in tags:
        rel = released.get(tag)
        if rel is None:
            carrier = next((d for d in deployed if ancestors.get((tag, d))), None)
            if carrier:
                found.append(("note", f"{tag}: tag has no Release, but {carrier} "
                              "deployed after it and carried the change"))
            else:
                found.append(("error", f"{tag}: tag has no Release — never deployed"))
        elif rel["isDraft"]:
            found.append(("warn", f"{tag}: Release is a draft — drafts do not deploy"))
        elif tag not in latest_run:
            found.append(("warn", f"{tag}: no deploy run found (runs older than the "
                          "retention window are not listed)"))
        elif latest_run[tag].get("conclusion") != "success":
            found.append(("error", f"{tag}: latest deploy run concluded "
                          f"{latest_run[tag].get('conclusion') or latest_run[tag].get('status')}"))
    return found


def run(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("repo", help="path to the mission repo (the deployed tree)")
    args = ap.parse_args()
    repo = Path(args.repo)
    if not (repo / ".git").exists():
        print(f"not a git repo: {repo}", file=sys.stderr)
        return 2

    findings = []
    workflows = [p for p in sorted((repo / ".github" / "workflows").glob("*.y*ml"))
                 if ACTION in p.read_text(encoding="utf-8")]
    if not workflows:
        findings.append(("error", f"no workflow uses {ACTION} — nothing deploys"))
    for wf in workflows:
        findings += [(l, f"{wf.name}: {m}") for l, m in lint_workflow(wf.read_text(encoding="utf-8"))]

    if shutil.which("gh") is None:
        findings.append(("warn", "gh not installed — release checks skipped"))
    else:
        tags = run(["git", "tag", "--sort=v:refname"], repo).stdout.split()
        rel = run(["gh", "release", "list", "-L", "1000", "--json", "tagName,isDraft"], repo)
        runs = run(["gh", "run", "list", "-L", "1000", "--event", "release",
                    "--json", "headBranch,conclusion,status"], repo)
        if rel.returncode or runs.returncode:
            findings.append(("warn", "gh could not read releases/runs — release checks "
                             f"skipped ({(rel.stderr or runs.stderr).strip()[:120]})"))
        else:
            releases, runlist = json.loads(rel.stdout), json.loads(runs.stdout)
            ancestors = {}
            for t in tags:
                if t in {r["tagName"] for r in releases}:
                    continue
                for d in tags:
                    ancestors[(t, d)] = run(["git", "merge-base", "--is-ancestor", t, d],
                                            repo).returncode == 0 and t != d
            findings += audit_releases(tags, releases, runlist, ancestors)

    for level in ("error", "warn", "note"):
        for l, m in findings:
            if l == level:
                print(f"{level.upper():5}  {m}")
    errors = sum(1 for l, _ in findings if l == "error")
    print(f"\n{errors} error(s), {len(findings) - errors} warning(s)/note(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
