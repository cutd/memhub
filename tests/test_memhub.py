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

    def test_remember_after_forget_revives_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            mh.init_repo(repo, name="tester")
            mh.remember(repo, "喜欢喝咖啡", type_="preference", source_client="agent")
            mh.forget(repo, "咖啡", apply=True)
            self.assertIn("No matching memory", mh.search(repo, "咖啡"))
            # Re-remembering the same content must bring it back, not be dropped.
            out = mh.remember(repo, "喜欢喝咖啡", type_="preference", source_client="agent")
            self.assertNotIn("skipped", out)
            self.assertIn("喜欢喝咖啡", mh.search(repo, "咖啡"))
            # And it should not have created a second copy.
            prefs = mh.read_yaml(repo / "identity/preferences.yaml", {})["preferences"]
            same = [p for p in prefs if p.get("content") == "喜欢喝咖啡"]
            self.assertEqual(len(same), 1)
            self.assertEqual(same[0].get("status"), "active")

    def test_forgotten_timeline_event_leaves_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            mh.init_repo(repo, name="tester")
            mh.remember(repo, "发生了X事件", type_="event", source_client="agent")
            self.assertIn("发生了X事件", mh.build_context(repo, pack="full"))
            mh.forget(repo, "X事件", apply=True)
            self.assertNotIn("发生了X事件", mh.build_context(repo, pack="full"))

    def test_search_query_does_not_match_type_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            mh.init_repo(repo, name="tester")
            # A preference whose content does NOT contain the word "preference".
            mh.remember(repo, "深色主题", type_="preference", source_client="agent")
            # Searching the type name must not surface content lacking that word.
            self.assertNotIn("深色主题", mh.search(repo, "preference"))
            # The real --type filter still works.
            self.assertIn("深色主题", mh.search(repo, "深色", type_="preference"))


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


class AutoSyncTest(unittest.TestCase):
    def _wire_remote(self, base: Path) -> tuple[Path, Path, Path]:
        repo_a, bare, repo_b = base / "a", base / "bare.git", base / "b"
        mh.init_repo(repo_a, name="A")
        subprocess.run(["git", "init", "--bare", str(bare)], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "remote", "add", "origin", str(bare)], cwd=repo_a, check=True)
        # Reflect the remote in config so auto_* helpers see it.
        self._set_sync(repo_a, remote=str(bare))
        return repo_a, bare, repo_b

    def _set_sync(self, repo: Path, **fields) -> None:
        cfg = mh.load_config(repo)
        cfg.setdefault("sync", {}).update(fields)
        mh.save_config(repo, cfg)

    def test_throttle_zero_pushes_on_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_a, bare, _ = self._wire_remote(Path(tmp))
            self._set_sync(repo_a, push_throttle_seconds=0, pull_throttle_seconds=0)
            mh.sync_repo(repo_a)  # establish the remote branch
            mh.remember(repo_a, "立即上远端", type_="preference", source_client="A")
            mh.maybe_auto_push(repo_a)
            log = subprocess.run(["git", "log", "--oneline", "main"], cwd=bare,
                                 text=True, capture_output=True).stdout
            self.assertIn("立即上远端", log)

    def test_throttle_window_keeps_write_local(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_a, bare, _ = self._wire_remote(Path(tmp))
            self._set_sync(repo_a, push_throttle_seconds=0, pull_throttle_seconds=0)
            mh.sync_repo(repo_a)
            # Now widen the window; a fresh push just happened, so the next write
            # must stay local.
            self._set_sync(repo_a, push_throttle_seconds=99999)
            mh.remember(repo_a, "窗口内不推", type_="fact", source_client="A")
            pushed = mh.maybe_auto_push(repo_a)
            self.assertEqual(pushed, "")  # throttled
            remote_log = subprocess.run(["git", "log", "--oneline", "main"], cwd=bare,
                                        text=True, capture_output=True).stdout
            self.assertNotIn("窗口内不推", remote_log)
            # But it IS committed locally — memory is never lost.
            local_log = subprocess.run(["git", "log", "--oneline"], cwd=repo_a,
                                       text=True, capture_output=True).stdout
            self.assertIn("窗口内不推", local_log)
            # An explicit sync ignores the throttle and flushes it.
            mh.sync_repo(repo_a)
            remote_log = subprocess.run(["git", "log", "--oneline", "main"], cwd=bare,
                                        text=True, capture_output=True).stdout
            self.assertIn("窗口内不推", remote_log)

    def test_context_auto_pulls_remote_memory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            repo_a, bare, repo_b = self._wire_remote(base)
            self._set_sync(repo_a, push_throttle_seconds=0, pull_throttle_seconds=0)
            mh.sync_repo(repo_a)
            mh.remember(repo_a, "A写的可记事件", type_="event", source_client="A")
            mh.maybe_auto_push(repo_a)

            subprocess.run(["git", "clone", "-b", "main", str(bare), str(repo_b)], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self._set_sync(repo_b, remote=str(bare), pull_throttle_seconds=0)
            # build_context after an auto-pull should see A's memory.
            mh.maybe_auto_pull(repo_b)
            self.assertIn("A写的可记事件", mh.build_context(repo_b, pack="full"))


if __name__ == "__main__":
    unittest.main()
