#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "openlogic_sync_message", ROOT / "scripts" / "openlogic-sync-message.py"
)
sync = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sync)


class OpenLogicFixture:
    def __init__(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "OpenLogic-Zh"
        self.root.mkdir()
        self.build = Path(self.temp.name) / "build"
        self.build.mkdir()
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "user.name", "Sync Message Test")
        self.git("config", "commit.gpgsign", "false")
        self.write("locale/zh/content/used.tex", "原始 used\n")
        self.write("locale/zh/content/unused.tex", "原始 unused\n")
        self.write("content/used.tex", "source used\n")
        self.write("README.md", "fixture\n")
        self.git("add", ".")
        self.git("commit", "-q", "-m", "base")
        self.old = self.rev()

    def close(self):
        self.temp.cleanup()

    def git(self, *args, check=True):
        return subprocess.run(
            ["git", *args],
            cwd=self.root,
            check=check,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def rev(self):
        return self.git("rev-parse", "HEAD").stdout.strip()

    def write(self, path, text):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    def commit(self, subject, body=None):
        self.git("add", ".")
        args = ["commit", "-q", "-m", subject]
        if body is not None:
            args.extend(["-m", body])
        self.git(*args)
        return self.rev()

    def fls(self, *paths, forms=False):
        lines = [f"PWD {self.build}"]
        for index, path in enumerate(paths):
            absolute = self.root / path
            if forms and index == 0:
                value = os_path_relative(self.build, absolute)
            elif forms and index == 1:
                value = str(absolute)
            else:
                value = os_path_relative(self.build, absolute)
            lines.append(f"INPUT {value}")
        target = self.build / f"build-{len(list(self.build.glob('build-*.fls')))}.fls"
        target.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return target


def os_path_relative(base, target):
    import os

    return os.path.relpath(target, base)


class SyncMessageTests(unittest.TestCase):
    def setUp(self):
        self.fixture = OpenLogicFixture()

    def tearDown(self):
        self.fixture.close()

    def message(self, new, *fls):
        return sync.build_message(
            self.fixture.root,
            self.fixture.old,
            new,
            fls or [self.fixture.fls("locale/zh/content/used.tex")],
        )

    def test_multiple_content_commits_preserve_semantics_and_provenance(self):
        self.fixture.write("locale/zh/content/used.tex", "第一版 used\n")
        first = self.fixture.commit("fix(zh): clarify the used section")
        self.fixture.write("locale/zh/content/used.tex", "新 used\n")
        second = self.fixture.commit(
            "feat(zh)!: expand the used section",
            "BREAKING-CHANGE: the section now has a new structure",
        )
        self.fixture.write("README.md", "internal\n")
        internal = self.fixture.commit("ci(zh): refresh checks")
        output = self.message(
            internal,
            self.fixture.fls("locale/zh/content/used.tex", forms=True),
        )
        self.assertIn("OpenLogic-Range:", output)
        self.assertIn(f"fix(translation): clarify the used section", output)
        self.assertIn(f"feat(translation)!: expand the used section", output)
        self.assertIn(f"OpenLogic-Commit: {first}", output)
        self.assertIn(f"OpenLogic-Commit: {second}", output)
        self.assertNotIn(f"OpenLogic-Commit: {internal}", output)
        self.assertIn("BREAKING CHANGE: the section now has a new structure", output)

    def test_internal_only_range_is_chore(self):
        self.fixture.write("README.md", "internal\n")
        new = self.fixture.commit("ci(zh): refresh checks")
        output = self.message(new)
        self.assertTrue(output.startswith("chore(sync):"))
        self.assertIn("chore(sync): advance OpenLogic-Zh", output)
        self.assertNotIn("fix(translation)", output)

    def test_old_revision_must_be_ancestor(self):
        base = self.fixture.old
        self.fixture.git("checkout", "-q", "-b", "old-branch")
        self.fixture.write("locale/zh/content/used.tex", "old branch\n")
        old = self.fixture.commit("fix(zh): old branch")
        self.fixture.git("checkout", "-q", "-b", "new-branch", base)
        self.fixture.write("locale/zh/content/used.tex", "other branch\n")
        new = self.fixture.commit("fix(zh): other branch")
        self.fixture.old = old
        with self.assertRaises(sync.SyncMessageError):
            self.message(new)

    def test_net_unchanged_range_is_chore(self):
        self.fixture.write("locale/zh/content/used.tex", "temporary\n")
        self.fixture.commit("fix(zh): temporary change")
        self.fixture.write("locale/zh/content/used.tex", "原始 used\n")
        new = self.fixture.commit("revert: restore the used section")
        output = self.message(new)
        self.assertIn("chore(sync): advance OpenLogic-Zh", output)
        self.assertNotIn("fix(translation)", output)

    def test_fls_filters_unbuilt_files_and_normalizes_paths(self):
        self.fixture.write("locale/zh/content/used.tex", "changed used\n")
        used = self.fixture.commit("fix(zh): change the used input")
        self.fixture.write("locale/zh/content/unused.tex", "changed unused\n")
        unused = self.fixture.commit("fix(zh): change an unused input")
        fls = self.fixture.fls(
            "locale/zh/content/used.tex",
            "locale/zh/content/used.tex",
            forms=True,
        )
        output = self.message(unused, fls)
        self.assertIn(f"OpenLogic-Commit: {used}", output)
        self.assertNotIn(f"OpenLogic-Commit: {unused}", output)

    def test_non_release_type_that_changes_book_input_becomes_fix(self):
        self.fixture.write("locale/zh/content/used.tex", "文档型正文改动\n")
        new = self.fixture.commit("docs(zh): clarify the used section")
        output = self.message(new)
        self.assertIn("fix(translation): clarify the used section", output)
        self.assertNotIn("docs(", output)

    def test_source_input_has_source_scope(self):
        self.fixture.write("content/used.tex", "changed source\n")
        new = self.fixture.commit("fix(modal): clarify the source section")
        output = self.message(new, self.fixture.fls("content/used.tex"))
        self.assertIn("fix(source): clarify the source section", output)

    def test_fls_from_another_runner_workspace_is_normalized(self):
        self.fixture.write("locale/zh/content/used.tex", "portable path\n")
        new = self.fixture.commit("fix(zh): normalize runner paths")
        fls = self.fixture.build / "portable.fls"
        fls.write_text(
            "PWD /runner/work/boxes-and-diamonds-zh/boxes-and-diamonds-zh\n"
            "INPUT ../OpenLogic-Zh/locale/zh/content/used.tex\n",
            encoding="utf-8",
        )
        output = self.message(new, fls)
        self.assertIn(f"OpenLogic-Commit: {new}", output)

    def test_deleted_locale_tex_fails_closed(self):
        self.fixture.write("locale/zh/content/removed.tex", "will disappear\n")
        self.fixture.write("content/removed.tex", "fallback\n")
        self.fixture.commit("feat(zh): add removable input")
        self.fixture.old = self.fixture.rev()
        self.fixture.git("rm", "-q", "locale/zh/content/removed.tex")
        new = self.fixture.commit("fix(zh): remove obsolete input")
        fls = self.fixture.fls("content/removed.tex")
        with self.assertRaises(sync.SyncMessageError):
            self.message(new, fls)

    def test_deleted_unbuilt_locale_tex_is_ignored(self):
        self.fixture.write("locale/zh/content/removed.tex", "unused\n")
        self.fixture.commit("feat(zh): add unused localized input")
        self.fixture.old = self.fixture.rev()
        self.fixture.git("rm", "-q", "locale/zh/content/removed.tex")
        new = self.fixture.commit("fix(zh): remove unused localized input")
        output = self.message(new)
        self.assertTrue(output.startswith("chore(sync):"))

    def test_malformed_subject_is_safe_and_releasable(self):
        self.fixture.write("locale/zh/content/used.tex", "unsafe subject\n")
        new = self.fixture.commit("???\x1b[31m inject", "body")
        output = self.message(new)
        self.assertIn("fix(translation): ??? inject", output)
        self.assertNotIn("\x1b", output)
        self.assertNotIn("\nfix:", output)

    def test_both_breaking_footer_spellings_are_canonicalized(self):
        self.fixture.write("locale/zh/content/used.tex", "breaking\n")
        new = self.fixture.commit(
            "fix(zh): preserve compatibility",
            "BREAKING CHANGE: first reason\nBREAKING-CHANGE: second reason",
        )
        output = self.message(new)
        self.assertIn("BREAKING CHANGE: first reason", output)
        self.assertIn("BREAKING CHANGE: second reason", output)


if __name__ == "__main__":
    unittest.main()
