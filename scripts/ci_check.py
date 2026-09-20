#!/usr/bin/env python3
"""Repo checks for the dayz plugin, run by CI and safe to run locally.

There is no pytest suite here — the product is skills and validators, so what
is worth checking is that the plugin metadata is coherent, every skill is
well-formed, and every validator still runs. A syntax error in a validator or
a skill missing its frontmatter are the realistic regressions.

    python3 scripts/ci_check.py

Exit status: 0 all checks passed, 1 something failed.
"""

import json
import py_compile
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
failures = []
checks = 0


def check(label, ok, detail=""):
    global checks
    checks += 1
    if ok:
        print(f"  ok    {label}")
    else:
        print(f"  FAIL  {label}{': ' + detail if detail else ''}")
        failures.append(label)


def frontmatter(path):
    """Return the YAML frontmatter block of a SKILL.md, or None."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    return text[4:end] if end != -1 else None


print("plugin metadata")
manifest = ROOT / ".claude-plugin" / "plugin.json"
try:
    meta = json.loads(manifest.read_text(encoding="utf-8"))
    check("plugin.json parses", True)
    for field in ("name", "description", "version"):
        check(f"plugin.json has {field}", field in meta)
except Exception as exc:  # noqa: BLE001 - report any malformed manifest
    meta = {}
    check("plugin.json parses", False, str(exc))

print("\nskills")
skill_dirs = sorted(p for p in (ROOT / "skills").iterdir() if p.is_dir())
check("at least one skill", bool(skill_dirs))
for skill in skill_dirs:
    md = skill / "SKILL.md"
    if not md.is_file():
        check(f"{skill.name}/SKILL.md exists", False)
        continue
    fm = frontmatter(md)
    check(f"{skill.name}: frontmatter present", fm is not None)
    if fm is None:
        continue
    check(f"{skill.name}: declares name", "\nname:" in "\n" + fm)
    check(f"{skill.name}: declares description", "\ndescription:" in "\n" + fm)
    # The directory is how the skill is addressed; a mismatch is a silent break.
    declared = next((l.split(":", 1)[1].strip()
                     for l in fm.splitlines() if l.startswith("name:")), None)
    check(f"{skill.name}: name matches directory", declared == skill.name,
          f"frontmatter says {declared!r}")

print("\npython sources compile")
sources = sorted(set((ROOT / "skills").rglob("*.py")) | set((ROOT / "scripts").rglob("*.py")))
check("found python sources", bool(sources))
for src in sources:
    try:
        py_compile.compile(str(src), doraise=True, cfile=str(src) + "c")
        check(f"compiles: {src.relative_to(ROOT)}", True)
    except py_compile.PyCompileError as exc:
        check(f"compiles: {src.relative_to(ROOT)}", False, str(exc))
    finally:
        Path(str(src) + "c").unlink(missing_ok=True)

print("\nvalidators run")
for validator in sorted((ROOT / "skills").glob("*/scripts/validate.py")):
    proc = subprocess.run([sys.executable, str(validator), "--help"],
                          capture_output=True, text=True)
    check(f"--help: {validator.relative_to(ROOT)}", proc.returncode == 0,
          proc.stderr.strip()[:200])
    # Exit 2 is the documented "could not run" path; anything else means the
    # argument handling regressed rather than the file being genuinely absent.
    proc = subprocess.run([sys.executable, str(validator), "does-not-exist.xml"],
                          capture_output=True, text=True)
    check(f"missing-file exits 2: {validator.relative_to(ROOT)}",
          proc.returncode == 2, f"exit {proc.returncode}")

print(f"\n{checks - len(failures)}/{checks} checks passed")
if failures:
    print("failed: " + ", ".join(failures))
sys.exit(1 if failures else 0)
