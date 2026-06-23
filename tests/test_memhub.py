"""Smoke tests for the MemHub reference CLI.

Run with: python -m pytest tests/ -q   (or: python -m unittest tests.test_memhub)

These cover the paths added for the "simple + efficient sync" work:
direct-write remember, search, forget (soft-archive), and the structured
three-way merge driver that lets two devices append memory without conflict.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "skills" / "memhub" / "scripts" / "memhub.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("memhub_impl", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["memhub_impl"] = module
    spec.loader.exec_module(module)
    return module


mh = _load_module()


def run_cli(repo: Path, *args: str) -> int:
    return mh.main(["--repo", str(repo), *args])


class DirectWriteTest(unittest.TestCase):
    def test_remember_direct_search_forget(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            mh.init_repo(repo, name="tester")

            # Direct write lands straight in canonical memory.
            out = mh.remember(repo, "用户偏好极简", type_="preference", source_client="agent")
            self.assertIn("identity/preferences.yaml", out)
            prefs = mh.read_yaml(repo / "identity/preferences.yaml", {})
            contents = [p.get("content") for p in prefs.get("preferences", [])]
            self.assertIn("用户偏好极简", contents)

            # Duplicate is skipped.
            out2 = mh.remember(repo, "用户偏好极简", type_="preference", source_client="agent")
            self.assertIn("skipped", out2)

            # --inbox keeps the audit-buffer behavior.
            out3 = mh.remember(repo, "待确认想法", type_="fact", to_inbox=True)
            self.assertIn("inbox", out3)
            self.assertTrue(list((repo / "inbox").glob("*.yaml")))

            # search finds the active entry.
            self.assertIn("用户偏好极简", mh.search(repo, "极简"))

            # forget dry-run does not mutate.
            mh.forget(repo, "极简", apply=False)
            self.assertEqual(
                mh.read_yaml(repo / "identity/preferences.yaml", {})["preferences"][0].get("status"),
                "active",
            )

            # forget --apply soft-archives, removing it from default search.
            mh.forget(repo, "极简", apply=True)
            self.assertIn("No matching memory", mh.search(repo, "极简"))
            self.assertIn("用户偏好极简", mh.search(repo, "极简", include_archived=True))


class MergeDriverTest(unittest.TestCase):
    def test_union_merge_resolves_divergent_appends(self) -> None:
        merged = mh.merge_yaml_docs(
            base={"preferences": []},
            ours={"preferences": [{"id": "a", "content": "A"}]},
            theirs={"preferences": [{"id": "b", "content": "B"}]},
        )
        ids = {p["id"] for p in merged["preferences"]}
        self.assertEqual(ids, {"a", "b"})

    def test_union_dedups_identical_entries(self) -> None:
        merged = mh.merge_yaml_docs(
            base={"items": []},
            ours={"items": [{"id": "x", "content": "same"}]},
            theirs={"items": [{"id": "x", "content": "same"}]},
        )
        self.assertEqual(len(merged["items"]), 1)

    def test_end_to_end_two_device_sync(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            repo_a = base / "a"
            bare = base / "bare.git"
            repo_b = base / "b"

            mh.init_repo(repo_a, name="A")
            subprocess.run(["git", "init", "--bare", str(bare)], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "remote", "add", "origin", str(bare)], cwd=repo_a, check=True)
            subprocess.run(["git", "push", "-u", "origin", "HEAD:main"], cwd=repo_a, check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "clone", str(bare), str(repo_b)], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Both devices append a different preference to the same file.
            mh.remember(repo_a, "A的偏好", type_="preference", source_client="A")
            mh.sync_repo(repo_a)
            mh.remember(repo_b, "B的偏好", type_="preference", source_client="B")
            mh.sync_repo(repo_b)  # must auto-merge, not conflict

            result = mh.search(repo_b, "偏好", include_archived=True)
            self.assertIn("A的偏好", result)
            self.assertIn("B的偏好", result)


if __name__ == "__main__":
    unittest.main()
