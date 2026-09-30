"""Behavior tests using real, isolated Git objects; no network or host Git writes."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
PROBE = HERE / "probe.py"
HOST = HERE.parents[2]


class ProbeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="native lifecycle 中文 ")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo = self.root / "objects"
        self.repo.mkdir()
        self.env = {"PATH": os.environ["PATH"], "GIT_CONFIG_NOSYSTEM": "1",
                    "GIT_CONFIG_GLOBAL": os.devnull,
                    "GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
                    "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
                    "GIT_AUTHOR_DATE": "2026-01-01T00:00:00Z",
                    "GIT_COMMITTER_DATE": "2026-01-01T00:00:00Z"}
        self.git("init", "--quiet")
        self.base_tree = self.git("mktree", data=b"")
        blob = self.git("hash-object", "-w", "--stdin", data=b"candidate\n")
        self.tree = self.git("mktree", data=("100644 blob " + blob + "\tchange\n").encode())
        self.base = self.commit(self.base_tree, "base")
        self.head = self.commit(self.tree, "head", self.base)
        self.merge = self.commit(self.tree, "merge", self.base, self.head)
        self.other = self.commit(self.base_tree, "unrelated root")
        self.git("update-ref", "HEAD", self.merge)
        self.policy = json.loads((HERE / "policy.json").read_text())
        self.event = {"action": "opened", "number": 7,
                      "repository": {"full_name": self.policy["repository"]},
                      "pull_request": {"number": 7, "merge_commit_sha": self.merge,
                                       "base": {"ref": "integration/lifecycle-native-target", "sha": self.base,
                                                "repo": {"full_name": self.policy["repository"]}},
                                       "head": {"sha": self.head,
                                                "repo": {"full_name": self.policy["repository"]}}}}
        self.context = {"event": "pull_request", "repository": self.policy["repository"],
                        "ref": "refs/pull/7/merge", "candidate": self.merge,
                        "run_id": "100", "run_attempt": "1",
                        "workflow_ref": self.policy["repository"] + "/" + self.policy["workflow_path"] + "@refs/pull/7/merge",
                        "workflow_sha": self.merge}
        self.expected = dict(self.context, base=self.base, base_ref=self.policy["target_ref"],
                             head=self.head, candidate_tree=self.tree, base_tree=self.base_tree)
        self.control = {"case": "fixture", "outcomes": {
            "pull_request": "pass", "merge_group": "pass", "workflow_dispatch": "pass"}}
        self.serial = 0

    def git(self, *args, data=None):
        return subprocess.run(["git", "-C", str(self.repo), *args], input=data,
                              env=self.env, check=True, capture_output=True).stdout.decode().strip()

    def commit(self, tree, message, *parents):
        return self.git("commit-tree", tree, *[v for p in parents for v in ("-p", p)],
                        data=message.encode())

    def run_probe(self, mode="verify", event_bytes=None):
        self.serial += 1
        case = self.root / str(self.serial)
        case.mkdir()
        for name, value in [("event", self.event), ("context", self.context),
                            ("expect", self.expected), ("control", self.control)]:
            (case / (name + ".json")).write_text(json.dumps(value, indent=2) + "\n")
        if event_bytes is not None:
            (case / "event.json").write_bytes(event_bytes)
        argv = [sys.executable, "-B", str(PROBE), mode, "--repo-dir", str(self.repo),
                "--event", str(case / "event.json"), "--context", str(case / "context.json"),
                "--output", str(case / "out")]
        if mode == "verify":
            argv += ["--expect", str(case / "expect.json")]
        else:
            argv += ["--control", str(case / "control.json")]
        child = subprocess.run(argv, cwd=self.root, env=self.env, capture_output=True)
        result = json.loads((case / "out" / "measurement.json").read_text())
        return child, result, case

    def test_pr_positive_preserves_bytes_and_measures_git(self):
        raw = json.dumps(self.event, indent=3).encode() + b"\n\n"
        child, result, case = self.run_probe(event_bytes=raw)
        self.assertEqual(child.returncode, 0, child.stderr)
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["git"]["candidate_tree"], self.tree)
        self.assertEqual(result["git"]["parents"], [self.base, self.head])
        self.assertEqual((case / "out/event.json").read_bytes(), raw)

    def test_independent_expected_identities_reject_mismatch(self):
        wrong = {"candidate": self.head, "base": self.other, "head": self.other,
                 "event": "workflow_dispatch", "repository": "wrong/repo",
                 "ref": "refs/heads/dev", "base_ref": "refs/heads/dev",
                 "run_id": "101", "run_attempt": "2", "workflow_sha": self.head,
                 "workflow_ref": "wrong/workflow@ref", "candidate_tree": self.base_tree,
                 "base_tree": self.tree}
        original = self.expected.copy()
        for key, value in wrong.items():
            with self.subTest(key=key):
                self.expected = dict(original, **{key: value})
                child, result, _ = self.run_probe()
                self.assertEqual(child.returncode, 1)
                self.assertTrue(any("expected " + key in e for e in result["errors"]), result)

    def test_wrong_payload_candidate_base_event_and_target_reject(self):
        original = copy.deepcopy(self.event)
        for field in ["candidate", "base", "event", "target"]:
            with self.subTest(field=field):
                self.event = copy.deepcopy(original)
                if field == "candidate":
                    self.event["pull_request"]["merge_commit_sha"] = self.head
                elif field == "base":
                    self.event["pull_request"]["base"]["sha"] = self.other
                elif field == "target":
                    self.event["pull_request"]["base"]["ref"] = "dev"
                else:
                    self.event["action"] = "closed"
                child, result, _ = self.run_probe()
                self.assertEqual(child.returncode, 1)
                self.assertTrue(result["errors"])

    def test_merge_group_positive_and_nonancestor_base_reject(self):
        self.event = {"action": "checks_requested", "repository": self.event["repository"],
                      "merge_group": {"head_sha": self.merge, "base_sha": self.base,
                                      "base_ref": self.policy["target_ref"],
                                      "head_ref": "refs/heads/gh-readonly-queue/integration/lifecycle-native-target/pr-7"}}
        self.context.update(event="merge_group", ref=self.event["merge_group"]["head_ref"])
        self.expected.update(self.context, head=None)
        child, result, _ = self.run_probe()
        self.assertEqual(child.returncode, 0, result)
        self.event["merge_group"]["base_sha"] = self.other
        self.expected["base"] = self.other
        child, result, _ = self.run_probe()
        self.assertEqual(child.returncode, 1)
        self.assertIn("base is not an ancestor of candidate", result["errors"])

    def test_dispatch_positive_and_bound_ref_reject(self):
        self.context.update(event="workflow_dispatch", ref=self.policy["dispatch_ref_prefix"] + "pass")
        self.event = {"repository": self.event["repository"], "ref": self.context["ref"],
                      "inputs": {"candidate": self.merge, "base": self.base,
                                 "base_ref": self.policy["target_ref"], "outcome": "pass"}}
        self.expected.update(self.context, head=None)
        child, result, _ = self.run_probe()
        self.assertEqual(child.returncode, 0, result)
        self.context["ref"] = "refs/heads/dev"
        child, result, _ = self.run_probe()
        self.assertEqual(child.returncode, 1)
        self.assertTrue(any("dispatch ref" in e for e in result["errors"]))

    def test_controlled_failure_keeps_original_subprocess_result(self):
        self.control["outcomes"]["pull_request"] = "fail"
        child, result, case = self.run_probe("capture")
        self.assertEqual(child.returncode, 23, result)
        operation = result["processes"][-1]
        self.assertEqual(operation["exit_code"], 23)
        self.assertEqual((case / "out" / operation["stdout"]).read_bytes(), b"native control\x00\xff\n")
        self.assertEqual((case / "out" / operation["stderr"]).read_bytes(), b"controlled failure\n")
        self.assertEqual(result["controlled_exit"], 23)

    def test_capture_pass_and_checkout_mismatch(self):
        child, result, _ = self.run_probe("capture")
        self.assertEqual(child.returncode, 0, result)
        self.git("update-ref", "HEAD", self.head)
        child, result, _ = self.run_probe("capture")
        self.assertEqual(child.returncode, 1)
        self.assertIn("checkout HEAD differs from candidate", result["errors"])

    def test_group_only_failure_can_follow_a_real_pr_pass(self):
        self.control["outcomes"]["merge_group"] = "fail"
        child, result, _ = self.run_probe("capture")
        self.assertEqual(child.returncode, 0, result)
        self.event = {"action": "checks_requested", "repository": self.event["repository"],
                      "merge_group": {"head_sha": self.merge, "base_sha": self.base,
                                      "base_ref": self.policy["target_ref"],
                                      "head_ref": "refs/heads/gh-readonly-queue/integration/lifecycle-native-target/pr-7"}}
        self.context.update(event="merge_group", ref=self.event["merge_group"]["head_ref"])
        child, result, _ = self.run_probe("capture")
        self.assertEqual(child.returncode, 23, result)
        self.assertEqual(result["control_outcome"], "fail")

    def test_empty_base_advance_does_not_reuse_old_bound_base(self):
        advanced = self.commit(self.base_tree, "empty target advance", self.base)
        candidate = self.commit(self.tree, "new merge", advanced, self.head)
        self.event["pull_request"]["base"]["sha"] = advanced
        self.event["pull_request"]["merge_commit_sha"] = candidate
        self.context.update(candidate=candidate, workflow_sha=candidate)
        self.expected.update(candidate=candidate, workflow_sha=candidate)
        child, result, _ = self.run_probe()
        self.assertEqual(child.returncode, 1)
        self.assertEqual(result["git"]["base_tree"], self.expected["base_tree"])
        self.assertEqual(result["errors"], ["expected base differs from observation"])
        self.expected["base"] = advanced
        child, result, _ = self.run_probe()
        self.assertEqual(child.returncode, 0, result)

    def test_malformed_event_preserved_and_missing_expectation_rejects(self):
        child, result, case = self.run_probe(event_bytes=b"{bad\xff\n")
        self.assertEqual(child.returncode, 1)
        self.assertEqual((case / "out/event.json").read_bytes(), b"{bad\xff\n")
        del self.expected["base"]
        child, result, _ = self.run_probe()
        self.assertEqual(child.returncode, 1)
        self.assertTrue(any("expectation fields" in e for e in result["errors"]))

    def test_old_output_not_overwritten(self):
        child, _, case = self.run_probe()
        original = (case / "out/measurement.json").read_bytes()
        again = subprocess.run(child.args, cwd=self.root, env=self.env, capture_output=True)
        self.assertNotEqual(again.returncode, 0)
        self.assertEqual((case / "out/measurement.json").read_bytes(), original)


class FixtureTests(unittest.TestCase):
    def test_projection_and_transport_bindings(self):
        policy = json.loads((HERE / "policy.json").read_text())
        source = (HOST / policy["workflow_source"]).read_bytes()
        self.assertEqual(source, (HOST / policy["workflow_path"]).read_bytes())
        workflow = json.loads(source)
        target = policy["target_ref"].removeprefix("refs/heads/")
        self.assertEqual(set(workflow["on"]), {"pull_request", "merge_group", "workflow_dispatch"})
        self.assertEqual(workflow["on"]["pull_request"]["branches"], [target])
        self.assertEqual(workflow["on"]["merge_group"]["branches"], [target])
        self.assertEqual(workflow["jobs"]["probe"]["name"], policy["check_name"])
        self.assertEqual(workflow["permissions"], {"contents": "read"})
        steps = workflow["jobs"]["probe"]["steps"]
        bindings = json.loads((HOST / ".chrono-harness/ci/units.json").read_text())["collection"]
        self.assertEqual(steps[1]["uses"], bindings["checkout_action"])
        self.assertEqual(steps[1]["with"]["ref"], "${{ github.sha }}")
        self.assertEqual(steps[-1]["uses"], bindings["upload_artifact_action"])
        self.assertEqual(steps[-1]["if"], "${{ always() }}")
        self.assertEqual(steps[-1]["with"]["retention-days"], policy["retention_days"])


if __name__ == "__main__":
    unittest.main()
