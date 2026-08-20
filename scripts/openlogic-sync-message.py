#!/usr/bin/env python3
import argparse
import os
from pathlib import Path
import re
import subprocess
import sys


HEX_REVISION = re.compile(r"^[0-9a-fA-F]{7,40}$")
REVISION_LINE = re.compile(
    r"\\setOLPrevision\{\s*([0-9a-fA-F]{7,40})(?:\s+\([^)]*\))?\s*\}"
)
CONVENTIONAL_SUBJECT = re.compile(
    r"^(?P<type>[A-Za-z][A-Za-z0-9-]*)(?:\((?P<scope>[^()\r\n]+)\))?(?P<breaking>!)?:\s*(?P<subject>.+)$"
)
BREAKING_FOOTER = re.compile(r"^BREAKING(?:[ -])CHANGE:\s*(.*)$")
ANSI_ESCAPE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


class SyncMessageError(RuntimeError):
    pass


def git(repo, *args, check=True):
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if check and result.returncode:
        detail = result.stderr.strip() or "git command failed"
        raise SyncMessageError(detail)
    return result


def resolve_revision(repo, revision):
    if not HEX_REVISION.fullmatch(revision):
        raise SyncMessageError(f"invalid OpenLogic revision: {revision!r}")
    result = git(repo, "rev-parse", "--verify", f"{revision}^{{commit}}")
    return result.stdout.strip()


def read_old_revision(path):
    text = Path(path).read_text(encoding="utf-8")
    match = REVISION_LINE.search(text)
    if not match:
        raise SyncMessageError(f"cannot read OpenLogic revision from {path}")
    return match.group(1)


def _absolute_path(path):
    return os.path.normpath(os.path.abspath(os.fspath(path)))


def normalize_fls_inputs(fls_paths, repo):
    repo = _absolute_path(repo)
    inputs = set()
    for fls_path in fls_paths:
        fls_path = Path(fls_path)
        pwd = None
        lines = fls_path.read_text(encoding="utf-8", errors="replace").splitlines()
        for line in lines:
            if line.startswith("PWD "):
                pwd = _absolute_path(line[4:])
                break
        base = pwd or _absolute_path(fls_path.parent)
        for line in lines:
            if not line.startswith("INPUT "):
                continue
            raw = line[6:]
            candidate = _absolute_path(
                raw if os.path.isabs(raw) else os.path.join(base, raw)
            )
            relative = None
            try:
                candidate_relative = os.path.relpath(candidate, repo)
            except ValueError:
                candidate_relative = None
            inside_repo = (
                candidate_relative
                and candidate_relative != os.curdir
                and not candidate_relative.startswith(f"..{os.sep}")
            )
            if inside_repo:
                relative = candidate_relative
            else:
                parts = Path(candidate).parts
                repo_name = Path(repo).name
                if repo_name in parts:
                    index = len(parts) - 1 - parts[::-1].index(repo_name) + 1
                    if index < len(parts):
                        relative = os.path.join(*parts[index:])
            if relative:
                inputs.add(Path(relative).as_posix())
    return inputs


def _name_list(repo, *args):
    output = git(repo, *args).stdout
    return {line for line in output.splitlines() if line}


def deleted_built_tex(repo, old, new, inputs):
    result = git(repo, "diff", "--find-renames", "--name-status", old, new).stdout
    deleted = set()
    for line in result.splitlines():
        fields = line.split("\t")
        status = fields[0]
        old_path = fields[1] if len(fields) > 1 else ""
        new_path = fields[2] if status.startswith("R") and len(fields) > 2 else ""
        if status != "D" and not status.startswith("R"):
            continue
        if not old_path.startswith("locale/zh/") or not old_path.endswith(".tex"):
            continue
        fallback_path = old_path.removeprefix("locale/zh/")
        was_built = old_path in inputs or fallback_path in inputs
        remains_built = bool(new_path and new_path in inputs)
        if was_built and not remains_built:
            deleted.add(old_path)
    return deleted


def relevant_commits(repo, old, new, net_paths):
    commits = git(repo, "rev-list", "--reverse", "--no-merges", f"{old}..{new}").stdout
    selected = []
    for commit in commits.splitlines():
        changed = _name_list(
            repo,
            "diff-tree",
            "--root",
            "--no-commit-id",
            "--name-only",
            "-r",
            commit,
        )
        paths = sorted(changed & net_paths)
        if paths:
            selected.append((commit, paths))
    return selected


def clean_text(value, limit=240):
    value = ANSI_ESCAPE.sub("", value)
    value = " ".join(value.replace("\x00", "�").split())
    value = "".join(char for char in value if char.isprintable())
    return value[:limit].rstrip()


def release_scope(paths):
    if any(path.startswith("locale/zh/") for path in paths):
        return "translation"
    if any(path.startswith("content/") for path in paths):
        return "source"
    return "typesetting"


def commit_details(repo, commit, paths):
    subject = git(repo, "show", "-s", "--format=%s", commit).stdout.rstrip("\r\n")
    body = git(repo, "show", "-s", "--format=%B", commit).stdout
    match = CONVENTIONAL_SUBJECT.fullmatch(subject)
    scope = release_scope(paths)
    original_subject = clean_text(subject) or f"update {scope} input"
    if match:
        commit_type = "feat" if match.group("type").lower() == "feat" else "fix"
        breaking = bool(match.group("breaking"))
        description = clean_text(match.group("subject")) or original_subject
    else:
        commit_type = "fix"
        description = original_subject
        breaking = False
    footers = []
    for line in body.splitlines():
        footer = BREAKING_FOOTER.match(line.strip())
        if footer:
            reason = clean_text(footer.group(1)) or "unspecified"
            if reason not in footers:
                footers.append(reason)
    return {
        "type": commit_type,
        "scope": scope,
        "description": description,
        "breaking": breaking,
        "footers": footers,
    }


def build_message(repo, old_revision, new_revision, fls_paths, source_name="OpenLogic-Zh"):
    repo = Path(repo)
    old = resolve_revision(repo, old_revision)
    new = resolve_revision(repo, new_revision)
    if git(repo, "merge-base", "--is-ancestor", old, new, check=False).returncode != 0:
        raise SyncMessageError(
            f"OpenLogic revision {old} is not an ancestor of {new}; refusing to sync"
        )
    inputs = normalize_fls_inputs(fls_paths, repo)
    if not inputs:
        raise SyncMessageError("build FLS files contain no OpenLogic inputs")
    changed = _name_list(repo, "diff", "--name-only", old, new)
    net_paths = changed & inputs
    deleted = deleted_built_tex(repo, old, new, inputs)
    if deleted:
        raise SyncMessageError(
            "deleted locale/zh TeX input requires review: " + ", ".join(sorted(deleted))
        )
    source_name = clean_text(source_name, 80) or "OpenLogic-Zh"
    short_new = new[:12]
    lines = [
        f"chore(sync): advance {source_name} to {short_new}",
        "",
        f"OpenLogic-Range: {old}..{new}",
        f"OpenLogic-Source: {source_name}",
    ]
    if not net_paths:
        return "\n".join(lines) + "\n"
    selected = relevant_commits(repo, old, new, net_paths)
    if not selected:
        raise SyncMessageError("net OpenLogic input changes have no attributable commit")
    for commit, paths in selected:
        details = commit_details(repo, commit, paths)
        marker = "!" if details["breaking"] else ""
        title = f"{details['type']}({details['scope']}){marker}: {details['description']}"
        lines.extend(["", title, "", f"OpenLogic-Commit: {commit}"])
        for reason in details["footers"]:
            lines.append(f"BREAKING CHANGE: {reason}")
    return "\n".join(lines) + "\n"


def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--old-revision")
    parser.add_argument("--new-revision", required=True)
    parser.add_argument("--fls", required=True, nargs="+", type=Path)
    parser.add_argument("--source-repo-name", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--revision-file", type=Path)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        old = args.old_revision
        if not old and args.revision_file:
            old = read_old_revision(args.revision_file)
        if not old:
            raise SyncMessageError("--old-revision or --revision-file is required")
        message = build_message(
            args.repo,
            old,
            args.new_revision,
            args.fls,
            args.source_repo_name,
        )
        if str(args.output) == "-":
            sys.stdout.write(message)
        else:
            args.output.write_text(message, encoding="utf-8")
    except (OSError, SyncMessageError) as error:
        print(f"openlogic-sync-message: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
