"""Finite GitHub provider experiment. No API writes, polling or lifecycle decisions."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys


HERE = Path(__file__).resolve().parent
CONTEXT_FIELDS = {"event", "repository", "ref", "candidate", "run_id", "run_attempt",
                  "workflow_ref", "workflow_sha"}
EXPECTED_FIELDS = CONTEXT_FIELDS | {"base", "base_ref", "head", "candidate_tree", "base_tree"}
OID = re.compile(r"[0-9a-f]{40}\Z")


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON field: " + key)
        result[key] = value
    return result


def read_json(path):
    value = json.loads(path.read_bytes(), object_pairs_hook=unique)
    if not isinstance(value, dict):
        raise ValueError("JSON object required: " + str(path))
    return value


class Processes:
    def __init__(self, repo, output, policy, result):
        self.repo, self.output, self.policy, self.result = repo, output, policy, result
        # This is an observation environment, not the host's certified Git binding.
        self.env = {"PATH": os.environ["PATH"], "LC_ALL": "C", "GIT_CONFIG_NOSYSTEM": "1",
                    "GIT_CONFIG_GLOBAL": os.devnull, "GIT_NO_REPLACE_OBJECTS": "1",
                    "GIT_TERMINAL_PROMPT": "0"}
        self.git_program = shutil.which(policy["git_program"], path=self.env["PATH"])
        if self.git_program is None:
            raise ValueError("registered experiment Git program unavailable")

    def run(self, argv):
        number = len(self.result["processes"])
        record = {"argv": argv, "cwd": str(self.repo), "exit_code": None,
                  "stdout": str(number) + ".stdout.bin", "stderr": str(number) + ".stderr.bin"}
        self.result["processes"].append(record)
        try:
            child = subprocess.run(argv, cwd=self.repo, env=self.env, capture_output=True,
                                   timeout=self.policy["process_timeout_seconds"])
            stdout, stderr = child.stdout, child.stderr
            record["exit_code"] = child.returncode
        except subprocess.TimeoutExpired as error:
            stdout, stderr = error.stdout or b"", error.stderr or b""
            record["infrastructure_error"] = "process timeout; functional result unknown"
        except OSError as error:
            stdout, stderr = b"", b""
            record["infrastructure_error"] = str(error)
        (self.output / record["stdout"]).write_bytes(stdout)
        (self.output / record["stderr"]).write_bytes(stderr)
        if "infrastructure_error" in record:
            raise ValueError(record["infrastructure_error"])
        return record["exit_code"], stdout

    def git(self, *argv, allow_failure=False):
        code, stdout = self.run([self.git_program, *argv])
        if code and not allow_failure:
            raise ValueError("Git operation failed (original bytes retained): " + " ".join(argv))
        return code, stdout.decode("ascii").strip()


def identities(event, context, policy):
    if set(context) != CONTEXT_FIELDS:
        raise ValueError("context fields differ from explicit contract")
    for key in CONTEXT_FIELDS:
        if not isinstance(context[key], str) or not context[key]:
            raise ValueError("context string required: " + key)
    if context["repository"] != policy["repository"] or event["repository"]["full_name"] != policy["repository"]:
        raise ValueError("repository differs from experiment policy")
    for key in ("run_id", "run_attempt"):
        if not re.fullmatch(r"[1-9][0-9]*", context[key]):
            raise ValueError("positive decimal required: " + key)
    prefix = policy["repository"] + "/" + policy["workflow_path"] + "@"
    if not context["workflow_ref"].startswith(prefix):
        raise ValueError("workflow reference differs from experiment policy")
    name = context["event"]
    if name == "pull_request":
        if event["action"] not in ("opened", "synchronize", "reopened"):
            raise ValueError("unsupported pull_request action")
        pr = event["pull_request"]
        if event["number"] != pr["number"] or context["ref"] != "refs/pull/" + str(event["number"]) + "/merge":
            raise ValueError("pull_request ref/number mismatch")
        if any(pr[side]["repo"]["full_name"] != policy["repository"] for side in ("base", "head")):
            raise ValueError("experiment requires same-repository PR")
        # Actions GITHUB_SHA binds the tested merge candidate. PR merge metadata
        # is asynchronous and may be null or describe another test merge; keep
        # its raw bytes, but bind acceptance to Git parents and independent expect.
        merge_metadata = pr["merge_commit_sha"]
        if merge_metadata is not None and (not isinstance(merge_metadata, str) or not OID.fullmatch(merge_metadata)):
            raise ValueError("event merge metadata must be null or a full Git SHA-1")
        base, base_ref, head = pr["base"]["sha"], "refs/heads/" + pr["base"]["ref"], pr["head"]["sha"]
    elif name == "merge_group":
        if event["action"] != "checks_requested":
            raise ValueError("unsupported merge_group action")
        group = event["merge_group"]
        if group["head_sha"] != context["candidate"] or group["head_ref"] != context["ref"]:
            raise ValueError("merge_group candidate/ref differs from transport")
        base, base_ref, head = group["base_sha"], group["base_ref"], None
    elif name == "workflow_dispatch":
        if not context["ref"].startswith(policy["dispatch_ref_prefix"]):
            raise ValueError("dispatch ref outside dedicated experiment prefix")
        # GitHub dispatch payload ref may be the short branch name.
        event_ref = event["ref"]
        if not event_ref.startswith("refs/"):
            event_ref = "refs/heads/" + event_ref
        if event_ref != context["ref"] or event["inputs"]["candidate"] != context["candidate"]:
            raise ValueError("dispatch ref/candidate differs from transport")
        base, base_ref, head = event["inputs"]["base"], event["inputs"]["base_ref"], None
    else:
        raise ValueError("unsupported event: " + name)
    if base_ref != policy["target_ref"]:
        raise ValueError("base ref outside dedicated experiment target")
    observed = dict(context, base=base, base_ref=base_ref, head=head)
    for key in ("candidate", "base", "workflow_sha", "head"):
        if key == "head" and observed[key] is None:
            continue
        if not isinstance(observed[key], str) or not OID.fullmatch(observed[key]):
            raise ValueError("full Git SHA-1 required: " + key)
    return observed


def measure_git(processes, observed, result, capture):
    measured = result["git"]
    measured["version"] = processes.git("--version")[1]
    if processes.git("rev-parse", "--is-shallow-repository")[1] != "false":
        raise ValueError("complete Git ancestry required; shallow repository")
    for key in ("candidate", "base", "head", "workflow_sha"):
        value = observed[key]
        if value is not None and processes.git("cat-file", "-t", value)[1] != "commit":
            raise ValueError(key + " is not a commit object")
    for key in ("candidate", "base"):
        measured[key + "_tree"] = processes.git("rev-parse", observed[key] + "^{tree}")[1]
    measured["parents"] = processes.git("rev-list", "--parents", "-n", "1", observed["candidate"])[1].split()[1:]
    code, _ = processes.git("merge-base", "--is-ancestor", observed["base"], observed["candidate"], allow_failure=True)
    measured["base_ancestor_exit"] = code
    if code != 0:
        result["errors"].append("base is not an ancestor of candidate" if code == 1 else "ancestry command failed")
    if observed["event"] == "pull_request" and measured["parents"] != [observed["base"], observed["head"]]:
        result["errors"].append("PR merge parents differ from bound base/head")
    if capture:
        measured["checkout_head"] = processes.git("rev-parse", "HEAD")[1]
        if measured["checkout_head"] != observed["candidate"]:
            result["errors"].append("checkout HEAD differs from candidate")


def run(args):
    # New output directory is mandatory: retries never erase original observations.
    args.output.mkdir(parents=True, exist_ok=False)
    result = {"scope": "provider observation and local identity checks only",
              "producer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "errors": [], "git": {}, "processes": [], "controlled_exit": None}
    exit_code = 1
    try:
        inputs = {"event": args.event, "context": args.context, "policy": args.policy}
        if args.mode == "verify":
            inputs["expect"] = args.expect
        else:
            inputs["control"] = args.control or args.repo_dir / read_json(args.policy)["control_path"]
        # Copy all original bytes before parsing the event or running an operation.
        for key, source in inputs.items():
            (args.output / (key + ".json")).write_bytes(source.read_bytes())
        policy = read_json(args.output / "policy.json")
        event, context = read_json(args.output / "event.json"), read_json(args.output / "context.json")
        observed = identities(event, context, policy)
        result["observed"] = observed
        if args.mode == "verify":
            expected = read_json(args.output / "expect.json")
            if set(expected) != EXPECTED_FIELDS:
                raise ValueError("expectation fields must be explicit and complete")
            for key, actual in observed.items():
                if expected[key] != actual:
                    result["errors"].append("expected " + key + " differs from observation")
        processes = Processes(args.repo_dir, args.output, policy, result)
        measure_git(processes, observed, result, args.mode == "capture")
        if args.mode == "verify":
            for key in ("candidate_tree", "base_tree"):
                if expected[key] != result["git"][key]:
                    result["errors"].append("expected " + key + " differs from Git object")
        if not result["errors"]:
            exit_code = 0
            if args.mode == "capture":
                control = read_json(args.output / "control.json")
                if not isinstance(control["case"], str) or not control["case"]:
                    raise ValueError("nonempty control case required")
                if set(control["outcomes"]) != {"pull_request", "merge_group", "workflow_dispatch"}:
                    raise ValueError("explicit outcome required for each experimental event")
                outcome = event["inputs"]["outcome"] if observed["event"] == "workflow_dispatch" else control["outcomes"][observed["event"]]
                if outcome not in ("pass", "fail"):
                    raise ValueError("control outcome must be pass or fail")
                result["control_case"], result["control_outcome"] = control["case"], outcome
                # A real child failure becomes the native job failure; never write a status API.
                child_code = "import sys;sys.stdout.buffer.write(b'native control\\x00\\xff\\n');sys.stderr.buffer.write(b'controlled failure\\n' if sys.argv[1]=='fail' else b'');sys.exit(23 if sys.argv[1]=='fail' else 0)"
                exit_code, _ = processes.run([sys.executable, "-c", child_code, outcome])
                result["controlled_exit"] = exit_code
    except (OSError, ValueError, KeyError, TypeError) as error:
        result["errors"].append(str(error))
        exit_code = 1
    result["exit_code"] = exit_code
    (args.output / "measurement.json").write_text(json.dumps(result, indent=2) + "\n")
    if result["errors"]:
        print("; ".join(result["errors"]), file=sys.stderr)
    return exit_code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    project = sub.add_parser("project", help="byte-copy this registered fixture; not a CI generator")
    project.add_argument("--host-root", type=Path, required=True)
    for mode in ("capture", "verify"):
        command = sub.add_parser(mode)
        command.add_argument("--repo-dir", type=Path, required=True)
        command.add_argument("--event", type=Path, required=True)
        command.add_argument("--context", type=Path, required=True)
        command.add_argument("--policy", type=Path, default=HERE / "policy.json")
        command.add_argument("--output", type=Path, required=True)
        if mode == "verify":
            command.add_argument("--expect", type=Path, required=True)
        else:
            command.add_argument("--control", type=Path)
    args = parser.parse_args()
    if args.mode == "project":
        policy = read_json(HERE / "policy.json")
        (args.host_root / policy["workflow_path"]).write_bytes((args.host_root / policy["workflow_source"]).read_bytes())
        return 0
    args.repo_dir, args.output = args.repo_dir.resolve(), args.output.resolve()
    return run(args)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
