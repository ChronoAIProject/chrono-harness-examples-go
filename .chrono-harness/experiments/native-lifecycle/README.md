# Native lifecycle provider qualification

This fixture answers whether GitHub can admit only the intended checked candidate
against the intended current base. It does not implement lifecycle orchestration,
full seven-judge governance, or certify dev delivery. All remote operations below
belong to the caller. Local tests are synthetic Git behavior tests, not native
qualification. Preserve every failed/partial operation and stop the affected route
when a prerequisite is missing; continue independent full-input/activation work.

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

1. **Prepare and preserve.** Re-read the actual dev tip before caller commit/push.
   If the preparation base moved, rebuild on fresh integration with semantic
   reconciliation; never recycle the old green. Commit this preparation, run the
   full selected canonical DELTA and keep original reports. Verify that the target
   and every proposed experiment branch name are absent; an existing name is not
   permission to overwrite it. Push the tested fixture to the new dedicated target
   and create each case from its fixed current tip, under unique
   `feature/lifecycle-native-CASE-NN` names. Never force-push or delete old work.

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

4. **Install a dedicated strict rule.** Create one new branch-only ruleset after a
   real check established the source app ID. No bypass actors, no human approval
   requirement, no wildcard/default/dev target. Initial direct-route qualification
   deliberately requires status checks without a PR-only rule so a *checked*
   fast-forward empty advancement can be attempted; this is not a production dev
   policy. Force pushes and branch deletion are forbidden. If pre-existing rules
   are stronger, retain them and stop any arm they make unavailable.

   ```sh
   jq -n --argjson app "$APP_ID" '{name:"native-lifecycle-provider-qualification",target:"branch",enforcement:"active",bypass_actors:[],conditions:{ref_name:{include:["refs/heads/integration/lifecycle-native-target"],exclude:[]}},rules:[{type:"non_fast_forward"},{type:"deletion"},{type:"required_status_checks",parameters:{required_status_checks:[{context:"native lifecycle / probe",integration_id:$app}],strict_required_status_checks_policy:true,do_not_enforce_on_create:false}}]}' > "$E/strict-rule.json"
   gh api --method POST "repos/$R/rulesets" --input "$E/strict-rule.json" > "$E/ruleset-created.json"
   gh api "repos/$R/rulesets/$RULESET_ID" > "$E/ruleset-active.json"
   gh api "repos/$R/rules/branches/integration%2Flifecycle-native-target" > "$E/effective-active.json"
   ```

   Require the returned rules to match the payload including app ID and strictness;
   a successful POST wrapper is insufficient. Do not replace a rejected app-bound
   rule with an any-source check. Keep all original configuration for restoration.

5. **Pass/fail and eligibility controls.** Under the active rule create distinct
   fresh pass/fail PRs (fail has `control.outcomes.pull_request=fail`); preserve the exact failed
   attempt and its exit-23 artifact. Submit a merge request for the failed PR and
   require provider rejection plus unchanged target and `merged=false`, even while
   another head or another check name is green. Then exercise the real eligible
   success case. Retain the full native body/exit for each attempt:

   ```sh
   jq -n --arg sha "$H" '{sha:$sha,merge_method:"merge"}' > "$E/merge.json"
   gh api --method PUT "repos/$R/pulls/$PR/merge" --input "$E/merge.json" > "$E/merge-result.json"
   gh api "repos/$R/pulls/$PR" > "$E/pr-after.json"
   git ls-remote origin "refs/heads/$TARGET"
   ```

   A successful merge must report `merged=true` and an actual merge SHA. Fetch it,
   check first parent B, inclusion of H, and tree equality with tested M. Verify the
   target contains the landing SHA, allowing a separately recorded subsequent
   target advance. Any tree/base mismatch fails qualification; never call CLOSED
   or `gh` exit zero a landing. Query a new target snapshot after the attempt.

   For dispatch comparison, bind a dedicated ref H, then POST a payload
   `{"ref":"feature/lifecycle-native-CASE-NN","inputs":{"candidate":"H",
   "base":"B","base_ref":"refs/heads/integration/lifecycle-native-target",
   "outcome":"pass"},"return_run_details":true}` to
   `/repos/$R/actions/workflows/native-lifecycle.yml/dispatches`. Repeat with fail
   on another fixed case/ref. Current API schema supports return_run_details;
   capture the actual HTTP response and run ID, falling back only to explicit
   identity-qualified run lookup if the response lacks details. Do not infer from
   docs whether a dispatch check is required-check eligible. Observe actual server
   admission, check app/head and failed-check rejection. Use a dedicated PR whose
   PR control is failed, or a checked fast-forward proposal, to distinguish dispatch
   eligibility from the presence of an eligible PR green. Dispatch alone is never
   proof of PR coverage. Preserve rejected/unavailable arms as unresolved.

6. **Head and base movement.** Prebind H, then fast-forward its case branch to H2
   with a new case label. Submit the old `sha:H` merge payload and require explicit
   head-mismatch rejection; retain both heads and both attempts. For base movement,
   first finish a pass on B/H/M, then advance the target using a separately checked
   change through the active rule. Immediately attempt the old checked PR and
   require rejection until evidence binds the new B2. Old green or a new synthetic
   merge tree with the same contents does not discharge the original base binding.

   Repeat the base control with an **empty target advancement**: on a fresh
   dedicated branch from B create an empty commit E (`git commit --allow-empty`),
   verify `E^{tree} == B^{tree}` and `E != B`, obtain the actual required check on E,
   then attempt ordinary fast-forward `git push origin E:refs/heads/$TARGET` under
   the unchanged active rule. Use dispatch only if its eligibility was established;
   otherwise try a native empty PR if GitHub admits it. Rejection/unavailability is
   an evidence gap, not permission to bypass checks or weaken rules. Preserve the
   exact accepted target SHA before retrying the stale-base merge. If empty
   advancement cannot be exercised, the strict route remains unqualified.

   **Direct merge has no expected-base argument in the inspected API schema.**
   Fetch-then-merge is not atomic. A few rejection observations cannot prove a
   universal exact-base guarantee. If native admission permits a stale bound base,
   or the route lacks a demonstrated provider mechanism for that binding, stop
   qualifying direct merge and proceed to the queue arm. Preserve any unexpected
   experiment landing and its mismatch; never retroactively label it validated.

7. **Qualify the real provider queue.** Public organization ownership is a documented
   entitlement premise, not a measured capability. Strengthen only the new
   experiment ruleset with `merge_queue`; keep its original required check, app,
   strictness and bypass settings. Use the original create payload as input, not
   a response object containing read-only API fields:

   ```sh
   jq '.rules += [{type:"merge_queue",parameters:{check_response_timeout_minutes:10,grouping_strategy:"ALLGREEN",max_entries_to_build:1,max_entries_to_merge:1,merge_method:"MERGE",min_entries_to_merge:1,min_entries_to_merge_wait_minutes:0}}]' "$E/strict-rule.json" > "$E/queue-rule.json"
   gh api --method PUT "repos/$R/rulesets/$RULESET_ID" --input "$E/queue-rule.json" > "$E/queue-rule-result.json"
   gh api "repos/$R/rules/branches/integration%2Flifecycle-native-target" > "$E/queue-effective.json"
   jq -n --arg sha "$H" '{sha:$sha,merge_action:"merge_queue"}' > "$E/enqueue.json"
   gh api --method PUT "repos/$R/pulls/$PR/merge-async" --input "$E/enqueue.json" > "$E/enqueue-result.json"
   gh api "repos/$R/pulls/$PR/merge-async/$UUID" > "$E/enqueue-terminal.json"
   ```

   `202`/pending and `enqueued` are not merged. For an async request, retain UUID,
   expected SHA and action, query only that UUID with a bounded 30-second cadence
   (10-minute infrastructure deadline), and preserve every error/response. A 409
   may identify a different pending request: do not adopt it without matching all
   inputs. Async results expire after 24 hours. Once enqueued, use actual native
   Actions run notification/watch plus PR/target queries for eventual landing;
   the enqueue result itself never changes into a queue landing verdict.

   Require a real `merge_group/checks_requested` run on this target, queue ref G,
   exact group candidate/base and successful required check. Before artifact
   review, independently query/fetch that queue ref and current target, freeze G,
   B and trees, then apply `verify` and the same run/job/check/suite association.
   If the queue moved before collection, retain the old result and bind a new run;
   never silently replace its expected identity. Exercise head move rejection with
   a stale `sha` enqueue request as well. A first single-entry queue green cannot
   establish concurrent-base behavior: queue two independent PRs (for example a
   case-label edit to `control.json` and a separate wording edit to this registered
   README, both with pass controls), require the
   second group's new base to contain the first landing, and reject reuse of its
   pre-advance result. Repeat the empty-tree advancement arm through a queue PR if
   GitHub admits an empty PR; if not, retain that precise limitation. A PR carrying
   the fail control must never land. For a **group-only** failure, set
   `control.outcomes.pull_request=pass` and `control.outcomes.merge_group=fail` on
   a fresh candidate. Its real PR check can pass and admit it to the queue, where
   the real group child must exit 23 and prevent landing. Do not fabricate a
   successful check to enter the queue.

   Finally fetch each landed SHA and require tested group-tree equality and the
   exact group-base mapping. Record any provider commit-SHA rewriting with its
   tree/parent proof. Missing queue settings, event, check association, rejection
   or landing evidence stops the affected route. Do not replace the queue with a
   custom scheduler, or silently fall back to unchecked direct merge.

8. **Hand back and restore deliberately.** Preserve source branches, PRs, original
   config, raw runs and failure artifacts. Before future restoration re-read the
   exact new ruleset ID/name/condition/body; remove only that caller-created
   experiment rule (`DELETE /repos/$R/rulesets/$RULESET_ID`) when its experiment
   lifecycle is complete and caller-authorized. Verify original effective settings
   remain intact. Never delete old branches or rewrite original results. This
   document does not authorize the implementation worker to run any native write.

## SPEC 10 and the next implementation decision

The immutable product SPEC section 10 already assigns fresh creation/reconstruction,
failure intents, recovery, metadata rebind and remote retirement to worktree. This
host binds those installed beta19 commands in `.chrono-harness/worktree.json`.
The AI still owns intent carry/retire decisions, genuine conflict resolution,
requirement reconciliation and re-registration. The workflow judge owns freshness
and integration acceptance; CI owns transport; GitHub owns admission. Existing
`crates/ci/src/full.rs` accepts full workflow_dispatch only. This fixture cannot
turn that into product PR/merge_group support by declaration.

After qualification, the smallest ordered sequence remains:

1. Preserve old branch/index/work and original failed/partial reports. Establish
   that interrupted operations stopped; use the applicable registered recovery
   primitive without rewriting the original outcome.
2. Fetch latest dev, start a **new** named fresh integration for rule/stability
   changes. Supply reconstruct's fixed old base/candidate and complete carry/retire
   plan. Reconcile changed/retired requirements and actual conflicts with current
   source; do not merge an old branch merely to appear fresh. Recover the retained
   conflict result against the actual resolved index and keep the old work.
3. Re-register the reconciled inputs, commit the resulting candidate and run the
   canonical complete DELTA plus required integration tests. Produce new exact
   base/tree/registry/tool/environment/effective-input evidence. Old greens and
   integration reports are not reusable after their inputs change.
4. If and only if the native experiment identifies a concrete missing product
   transport, extend the natural `ci` / dedicated `ci-tests` pair finitely to supply
   that event's full context and bindings. No product crate is selected now. Full
   input closure and actual full-host activation remain separate prerequisites.
5. Caller opens the PR, associates exact required checks and submits the qualified
   admission route. A changed base/candidate or merge-tree mismatch returns to fresh
   reconciliation and exact checks. Confirm actual dev landing SHA/tree and base
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
