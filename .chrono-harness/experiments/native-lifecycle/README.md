# Native CI event verification

This fixture checks the identities and results of a named native CI route. It does
not implement lifecycle orchestration, full seven-judge governance, or certify dev
delivery. Local tests cover Git behavior; native runs supply their own observed
evidence. All remote operations belong to the caller. Preserve failed/partial
results and complete the checks required by the host's chosen registered route.
Qualification of every provider route or all concurrent merges is not a prerequisite
for ordinary delivery. Unverified provider guarantees remain unverified.

## Ownership and entry points

`policy.json` owns this host's repository, dedicated target, dispatch prefix,
check name, artifact lifetime and Git observation settings. `control.json` supplies
a case label and explicit `pass`/`fail` outcomes for each event. PR and queue jobs read that file from the
checked-out candidate; dispatch may explicitly override the outcome. A real child
exits 23 on `fail`; neither the fixture nor the caller publishes a status manually.

`probe.py` and `probe_test.py` are an independent script/test pair in projects.json
and FILEMAP. Their test belongs to the existing `harness` unit. No new general CI
unit is created. The beta19 installer, unit generator and existing projections
remain their existing producers. The canonical local/CI check remains:

```sh
.chrono-harness/bin/chrono-harness check --config .chrono-harness/ci/check.json --base "$BASE" --candidate "$CANDIDATE" --unit harness
```

The command requires an actual clean committed candidate. The caller must also
run other units selected by the full DELTA: this preparation changes membership
registrations, whose existing edges include `rates-tests`. Bootstrap each selected
profile and collect their original reports using the existing collection contract.

`workflow.json` is a directly registered provider fixture, written as JSON (valid
YAML), not a chrono-ci source. Its only projection is
`.github/workflows/native-lifecycle.yml`. The registered byte-copy entry is:

```sh
python3 -B .chrono-harness/experiments/native-lifecycle/probe.py project --host-root .
```

The test checks projection equality and the explicit provider/action bindings.
Edit the source, then copy it; never edit the projection separately. This finite
copy does not generate other workflows or claim product PR/merge_group support.
Any customization to policy/workflow must keep their bindings consistent and run
the test. Existing action pins are taken from the host's unit provider config.

Local behavior entry (also the registered harness operation):

```sh
python3 -B .chrono-harness/experiments/native-lifecycle/probe_test.py
.chrono-harness/bin/chrono-ci verify --host-root . --config .chrono-harness/ci/units.json
actionlint .github/workflows/native-lifecycle.yml
```

Python >=3.9 and Git with `rev-parse`, `cat-file`, `rev-list`, `merge-base` are
required. Tests additionally use `init`, `hash-object`, `mktree`, `commit-tree`
and `update-ref` in temporary repositories. No host branches/index are changed.
actionlint is optional diagnostic tooling, not a new canonical gate. Runtime cost
is registered as unmeasured. Git executable/version/output are observed; this
experiment does not extend or certify the host's native Git input closure.

## Observation and independent verification

The fixed native job/check name is **`native lifecycle / probe`**. There is no push
trigger. PR and merge_group triggers both filter the exact target
`integration/lifecycle-native-target`; no automatic experiment job targets dev.
Dispatch is rejected outside `feature/lifecycle-native-*`. The workflow copies raw
event bytes and a small transport context before checkout, checks out `github.sha`,
runs `capture`, and uploads even after failure. There is no cancel-on-new-run rule.
Artifacts are `native-lifecycle-RUN-ATTEMPT`, retained 30 days; the caller must
download originals before expiry into fresh paths below
`.chrono-harness/state/native-lifecycle/`. No credentials, result snapshots or
session logs belong in source. Upload failure/cancellation leaves a native evidence
gap, even when the child operation had a result.

`capture` cross-checks the event against transport and actual Git objects, including
PR merge parents and base ancestry. Its zero exit only means the fixture operation
ran successfully. It does not choose an expected identity or attest admission.
`verify` takes the original event/context plus a **separately prepared** expected
JSON object. Do not populate that object from the artifact being verified.

For `pull_request`, the tested candidate is the Actions transport `GITHUB_SHA`
(`github.sha`) on `GITHUB_REF=refs/pull/NUMBER/merge`, as specified by
[GitHub's PR event contract](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#pull_request).
The payload's `pull_request.merge_commit_sha` is advisory mergeability metadata,
not a second candidate authority. GitHub [computes mergeability in the background](https://docs.github.com/en/rest/pulls/pulls#get-a-pull-request);
its [PR schema](https://github.com/github/rest-api-description/blob/main/descriptions/api.github.com/api.github.com.json)
requires the field but permits null. The fixture accepts null or a well-formed
SHA differing from the transport, preserving the original field unchanged in the
copied event. Missing or malformed metadata still rejects. A differing SHA never
replaces the transport candidate, base/head or independent expectations.

Acceptance still requires the transport candidate's actual ordered Git parents
to equal the event base/head, complete ancestry and commit objects; `capture`
also requires checkout HEAD to equal that candidate. `verify` binds these values,
trees, repository, event/ref, run/attempt and workflow identity to the independent
expectations below. A local regression pass does not repair an earlier native
failure: after committing and checking the correction, the caller must run a
fresh native source/case and retain the original failed artifacts.

```json
{
  "event": "pull_request",
  "repository": "ChronoAIProject/chrono-harness-examples-go",
  "ref": "refs/pull/NUMBER/merge",
  "candidate": "FULL_MERGE_CANDIDATE_SHA",
  "base": "FULL_PREBOUND_TARGET_SHA",
  "base_ref": "refs/heads/integration/lifecycle-native-target",
  "head": "FULL_PR_HEAD_SHA",
  "run_id": "RUN_ID_AS_STRING",
  "run_attempt": "ATTEMPT_AS_STRING",
  "workflow_ref": "ChronoAIProject/chrono-harness-examples-go/.github/workflows/native-lifecycle.yml@refs/pull/NUMBER/merge",
  "workflow_sha": "FULL_WORKFLOW_SOURCE_SHA",
  "candidate_tree": "FULL_EXPECTED_CANDIDATE_TREE_SHA",
  "base_tree": "FULL_EXPECTED_BASE_TREE_SHA"
}
```

For dispatch, set event/ref/candidate/workflow identity to the requested source ref
and commit, and `head` to null. For merge_group, use the independently fetched
queue ref/commit and prebound queue base, with `head` null. Use the exact provider
run/attempt selected through the API before opening its artifacts. For this
non-reusable workflow, precommit the expected workflow revision at the event ref;
if the actual source revision differs, retain the mismatch and investigate rather
than copying it back as the expectation. Fetch the fixed candidate, base and
workflow objects into an authorized local object repository. Keep the fetched
identities and trees fixed even if their remote refs later move.

```sh
python3 -B .chrono-harness/experiments/native-lifecycle/probe.py verify \
  --repo-dir "$OBJECT_REPO" --event "$ARTIFACT/event.json" \
  --context "$ARTIFACT/context.json" --expect "$E/expected.json" \
  --output "$E/verification-01"
```

All fields are mandatory. Wrong event, repository, refs, head/base/candidate, run,
attempt, workflow or trees must reject. The verifier requires complete Git ancestry
and commit objects; PR candidate parents must be the exact base and head, in order.
An empty base advance still changes the bound base SHA and cannot be accepted as
the old base just because its tree is equal. Every invocation uses a new output
directory and retains input bytes, Git/child stdout/stderr bytes, argv and exit codes.
Process timeout is an infrastructure gap, not a functional fail control.

Native run/check API association and final landing remain caller checks. The
verifier does not infer required-check eligibility from the event name or pretend
the run's check head and the tested merge candidate are always the same object.

## Caller-owned native sequence

Use ordinary caller Git/gh tools and host-tracked sessions. The snippets are
individual actions, not a new runtime. Set `R=ChronoAIProject/chrono-harness-examples-go`,
`TARGET=integration/lifecycle-native-target`, and `E` to a fresh run-local directory.
Use `-H 'X-GitHub-Api-Version: 2026-03-10'` on REST calls. Retain each request payload,
stdout/body, stderr/HTTP diagnostic and real exit status, including expected
rejections. Do not let a shell's `set -e` discard the failure evidence. `--paginate
--slurp` below means retain all pages and reject partial collection.

1. **Prepare and preserve.** Observe the current dev tip and the candidate before
   commit/push. Judge branch expiry using the host's registered freshness limits;
   a dev advance alone does not make a branch expired. Revalidate whenever the
   base, candidate tree or other required evidence bindings change. Reconstruct
   from current dev when expiry, actual conflicts or changed requirements require
   it, retaining useful work and original failures. Commit the prepared fixture,
   run the selected canonical DELTA and retain its reports. Verify any new branch
   name is absent; an existing name is not permission to overwrite it. Push to the
   dedicated target and create each necessary case from its fixed current tip.

2. **Read settings before changing them.** Save the repository's default branch,
   Actions policy and all rules affecting the dedicated target. Preserve 404s as
   observations; do not convert arbitrary API failure to absence.

   ```sh
   gh api "repos/$R" > "$E/repository.json"
   gh api "repos/$R/actions/permissions" > "$E/actions-permissions.json"
   gh api --paginate --slurp "repos/$R/rulesets?includes_parents=true&per_page=100" > "$E/rulesets-before.json"
   gh api "repos/$R/rules/branches/integration%2Flifecycle-native-target" > "$E/effective-before.json"
   gh api "repos/$R/branches/integration%2Flifecycle-native-target/protection" > "$E/protection-before.json"
   ```

   GET every returned applicable ruleset by ID and retain its full configuration.
   Do not modify existing rules, dev, the default branch, or Actions policy to make
   an experiment run. A missing permission/entitlement is a preserved prerequisite
   failure. The official dispatch docs require the workflow on the default branch
   (and describe dispatch by ref after a workflow has run). This fixture's branch
   availability alone does not prove dispatch availability. Start with the eligible
   experiment PR route; attempt dispatch as a comparison and preserve its actual
   acceptance/rejection. Do not install onto dev or change the default branch just
   to satisfy dispatch. If native registration remains unavailable, defer that arm.

3. **First real pass and identity discovery.** On a new case branch change
   `control.json`'s case to `pass-01`, keeping all three outcomes `pass`, commit and push.
   Prepare `create-pr.json` with `title`, `head` (that branch), `base` (TARGET), and
   `body` describing the experiment. Caller creates only an experiment-target PR:

   ```sh
   gh api --method POST "repos/$R/pulls" --input "$E/create-pr.json" > "$E/pr-created.json"
   gh api "repos/$R/pulls/$PR" > "$E/pr-before.json"
   gh api --paginate --slurp "repos/$R/actions/workflows/native-lifecycle.yml/runs?event=pull_request&per_page=100" > "$E/runs.json"
   git ls-remote origin "refs/pull/$PR/merge" "refs/heads/$TARGET"
   ```

   Select exactly the new PR/head/event/source workflow run, not the newest green.
   Bind PR ID, head H, base B, synthetic candidate M and trees before artifact review.
   Retrieve the chosen run and attempt, jobs, exact job check_run_url and suite:

   ```sh
   gh api "repos/$R/actions/runs/$RUN/attempts/$ATTEMPT" > "$E/run.json"
   gh api --paginate --slurp "repos/$R/actions/runs/$RUN/attempts/$ATTEMPT/jobs?per_page=100" > "$E/jobs.json"
   gh api "$CHECK_RUN_URL" > "$E/check.json"
   gh api "repos/$R/check-suites/$SUITE" > "$E/suite.json"
   gh api --paginate --slurp "repos/$R/actions/runs/$RUN/artifacts?per_page=100" > "$E/artifacts.json"
   gh run download "$RUN" --repo "$R" --name "native-lifecycle-$RUN-$ATTEMPT" --dir "$E/artifact"
   ```

   Validate run.repository, event, path/workflow_id, run_attempt, head_sha, PR
   association, completion and conclusion. Require exactly one job with the fixed
   name, matching run_id/run_attempt/head_sha, completed success, a check_run_url
   whose ID matches its check, and matching suite ID and head SHA. Record the actual
   `.app.id`/`.app.slug` from that check; require GitHub Actions and use its observed
   numeric ID below. Observe whether the check is attached to H or M and retain the
   explicit H/M/tree mapping. Precommit that mapping for a second fresh positive
   case: first-run discovery alone does not qualify it. Download exact attempt
   artifacts and run the independent verifier. Also retain checks/statuses on both
   H and M using `GET /repos/$R/commits/$OID/check-runs?filter=all&per_page=100` and
   `GET /repos/$R/commits/$OID/statuses?per_page=100` with pagination. Unrelated
   generated harness greens are observations, never substitutes for this check.

4. **Use the chosen registered delivery route.** Complete that route's required
   checks against the current candidate and base. Judge/stability changes require
   successful integration evidence bound to those inputs. A changed binding
   invalidates reuse of its old report; it does not by itself require a new branch
   or reimplementation. Never manufacture successful checks or bypass a failure.
   Use the provider's expected-head option when submitting the current candidate,
   then verify actual landing SHA, tested tree, base mapping and target containment.
   Retain mismatches as failures and repair them instead of certifying the landing.

   The repaired PR event capture and independent verification are useful evidence
   for that specific event and identity mapping. They do not prove server-side
   atomicity or a universal exact-base guarantee under concurrent updates. Testing
   empty-base advances, alternate dispatch eligibility or concurrent queue routes
   is needed only for an explicitly adopted contract that demands those stronger
   guarantees. It is not a mandatory matrix for the ordinary delivery path.

5. **Retain useful results.** Keep the registered fixture and regression tests,
   fixed identities, original native artifacts and actual verification outcomes.
   Preserve existing repository rules. Only modify an experiment-specific rule
   when the chosen route actually requires it and caller authorization covers the
   change; the fixture creates no such rule automatically.

## SPEC 10 and the next implementation decision

The immutable product SPEC section 10 already assigns fresh creation/reconstruction,
failure intents, recovery, metadata rebind and remote retirement to worktree. This
host binds those installed beta19 commands in `.chrono-harness/worktree.json`.
The AI still owns intent carry/retire decisions, genuine conflict resolution,
requirement reconciliation and re-registration. The workflow judge owns freshness
and integration acceptance; CI owns transport; GitHub owns admission. Existing
`crates/ci/src/full.rs` accepts full workflow_dispatch only. This fixture cannot
turn that into product PR/merge_group support by declaration.

The registered operational sequence is:

1. Preserve old branch/index/work and original failed/partial reports. Establish
   that interrupted operations stopped; use the applicable registered recovery
   primitive without rewriting the original outcome.
2. Observe current dev and the registered freshness limits. For a new rule/stability
   task use fresh integration; reconstruct an existing task only when expiry,
   conflicts or requirement changes call for it. Supply reconstruct's fixed old
   base/candidate and complete carry/retire plan. Reconcile changed/retired requirements and actual conflicts with current
   source; do not merge an old branch merely to appear fresh. Recover the retained
   conflict result against the actual resolved index and keep the old work.
3. Re-register the reconciled inputs, commit the resulting candidate and run the
   canonical complete DELTA plus required integration tests. Produce new exact
   base/tree/registry/tool/environment/effective-input evidence. Old greens and
   integration reports are not reusable after their inputs change.
4. If and only if the native experiment identifies a concrete missing product
   transport, extend the natural `ci` / dedicated `ci-tests` pair finitely to supply
   that event's full context and bindings. No product crate is selected now. Actual full-host activation requires its declared input bindings and applicable
   checks; it does not require proof that every possible hidden input is absent.
5. Caller opens the PR, associates exact required checks and submits the registered
   delivery route. A changed base/candidate or merge-tree mismatch requires
   reconciliation and the affected checks; branch reconstruction follows the
   registered freshness/conflict criteria. Confirm actual dev landing SHA/tree and base
   mapping plus required postconditions. A PR, CLOSED, green unrelated check or
   successful launcher never substitutes for landing evidence.

## Primary references

These are provider contracts to inspect, not evidence that this repository supports
them. Re-query current APIs when the caller executes the experiment.

- [REST rules](https://docs.github.com/en/rest/repos/rules): branch condition,
  required checks with integration ID, strict policy, merge_queue parameters.
- [REST pulls](https://docs.github.com/en/rest/pulls/pulls): synchronous merge `sha`,
  async `merge_action`, UUID results and the difference between enqueued and merged.
- [REST workflow dispatch](https://docs.github.com/en/rest/actions/workflows#create-a-workflow-dispatch-event).
- [Official OpenAPI schema](https://github.com/github/rest-api-description/blob/main/descriptions/api.github.com/api.github.com.json).
- [Workflow events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows):
  dispatch availability, PR merge candidate, merge_group and branch filters.
- [Available rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets):
  strict checks and expected source; no inferred dispatch exclusion.
- [Managing merge queues](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue):
  public organization entitlement and current-base group checks.
