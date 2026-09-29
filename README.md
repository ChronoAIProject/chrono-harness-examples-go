# chrono-harness-examples-go

可实际运行的宿主接入样例，用不同语言和目录检验显式登记、DELTA 选测和统一入口。

`engine/rates/` 是 Go 库；`verification/contracts/` 是独立测试 module。两个项目均没有 go.sum，也没有根工作区。

## 运行

需要 Git、Python ≥3.9、curl 和可下载固定发布/SDK 的网络。harness 使用 [chrono-harness v0.1.0-beta.14](https://github.com/ChronoAIProject/chrono-harness/releases/tag/v0.1.0-beta.14) 的预构建二进制；`.chrono-harness/distribution.json` 锁定发布清单、平台与摘要，生成的 `install.py` 执行统一安装。宿主不保留 harness 源码包，不需要 Rust。宿主 Go/Node/TypeScript SDK 独立登记在 bootstrap.json，支持 macOS arm64、Linux x86_64。

```sh
python3 .chrono-harness/bootstrap.py . --profile rates
.chrono-harness/bin/chrono-harness check --config .chrono-harness/ci/check.json --base <完整基线SHA> --candidate <完整候选SHA> --unit rates
```

候选必须是当前干净提交。首个无父提交使用 `--initial --candidate <SHA>`，代替 `--base`。单元报告由工具写入 `.chrono-harness/state/units/<单元ID>/check.json`。CI 的检测步骤使用完全相同的 harness argv；平台和 SDK 读数由 bootstrap-result.json 记录，指令相同不宣称环境完全等价。

## 独立 workflow 与汇总

每个登记单元各有独立 workflow、checkout、检查状态与重跑入口；全部工作流由同一配置生成。启动 SDK 由 `bootstrap.json` 的同名 profile 显式选择，不按语言或目录推断。上面的命令以一个单元为例，把 `--profile` 与 `--unit` 换成同一个登记 ID 即可。

| 单元 ID | 完整测试计划 | Workflow |
|---|---|---|
| `rates` | `test:rates-tests` | `.github/workflows/chrono-ci-rates.yml` |
| `harness` | `test:bootstrap-tests` | `.github/workflows/chrono-ci-harness.yml` |

`chrono / collection` 等待并下载同一候选、事件和基线的各单元原始结果，然后用与本地相同的命令判定完整性：

```sh
python3 .chrono-harness/bootstrap.py . --profile collection
.chrono-harness/bin/chrono-harness check --config .chrono-harness/ci/check.json --base <完整基线SHA> --candidate <完整候选SHA> --collect .chrono-harness/state/collection/manifest.json
```

本地在独立 checkout 并发运行单元，复制原始报告并显式登记 manifest 的单元、路径、报告摘要与 runner/judge 摘要；完整格式见 [CI 单元合同](https://github.com/ChronoAIProject/chrono-harness/blob/v0.1.0-beta.14/docs/ci-units.md)。汇总不重跑业务测试；缺失、重复、陈旧或失败结果不能通过。无 DELTA 的单元标明无需运行产品测试，不代表其它单元通过。

一个单元失败不取消其它 workflow。修复并重跑该单元后，再重跑 collection；其它单元保持原 run。自动收集限 push/PR，手动 dispatch 组合使用显式 manifest。各单元准备输入期间若 integration 基线移动导致不一致，汇总明确失败，不复用错配结果。

## 登记与验收

- `engine/rates/rate.go` → `test:rates-tests`。
- README.md 修改 → 不运行产品测试；未登记文件 → 失败；实际测试非零 → harness 非零。
- 项目配对、命令参数和依赖均在 `.chrono-harness/` 登记；不从扩展名、import、module 或目录推断选测。
- `CLAUDE.md` 由原子规则生成；`AGENTS.md` 是其相对符号链接。修改指令源后运行 `.chrono-harness/bin/chrono-instructions generate --host-root .`。
- CI 修改入口是 `.chrono-harness/ci/units.json`；运行 `.chrono-harness/bin/chrono-ci generate --host-root . --config .chrono-harness/ci/units.json`。受管工作流由 `chrono-ci verify` 检查。`push_baselines` 显式登记 integration 分支的所有 push 以 origin/dev 为基线，后续修复推送仍覆盖整个分支差异；dev 保持事件的 before/after。

## 当前边界

本仓运行现役 `chrono-ci-check/v3` scoped profile，验证实际命令、显式选测、干净快照和退出结果。它不冒充完整七判官治理，不证明工具链输入闭包完整或测试依赖无遗漏。该版本的通用 projects 判官已允许省略 manifest/lock/root 并接受任意显式 action；语言专属检查由可选适配器承载。本仓完整治理的接入仍未完成。

本地与 CI 通过相同 bootstrap 从公开 Release 校验安装；不需要跨仓凭据。安装结果见 `.chrono-harness/state/distribution.json`，语言 SDK 版本另见 `bootstrap-result.json`。成本暂未测量，登记为 unknown。

[主库与示例索引](https://github.com/ChronoAIProject/chrono-harness/blob/dev/docs/examples.md) 列出 Go、TS 和混合语言宿主。

## Registered worktrees

The pinned release also installs `chrono-worktree`. The host policy is
`.chrono-harness/worktree.json`; shared registries explicitly declare `dev`,
`feature/`, `integration/`, file ownership and artifacts. Project and FILEMAP
registrations have one owner; directory names and languages do not select work.

```sh
.chrono-harness/bin/chrono-worktree start --host-root . --config .chrono-harness/worktree.json --kind feature --name change --path ../my-change
```

The destination must not exist. `reconstruct` uses the same arguments plus
`--plan .chrono-harness/state/reconstruction.json`, with explicit fixed base and
candidate OIDs and a complete carry/retire path list. See the
[worktree contract](https://github.com/ChronoAIProject/chrono-harness/blob/v0.1.0-beta.14/docs/worktree.md).
Creation/reconstruction records actual Git results and preserves old work;
reconstruction stages changes and requires a new commit and the canonical check.
PR creation and merge remain caller-owned. Shared full-governance
registries are proposed; worktree use does not activate them or establish full
input closure, freshness certification or deterministic local/CI parity.

## Registered maintenance

The same installed `chrono-worktree` consumes explicit maintenance plans under
`.chrono-harness/state/` with the registered `.chrono-harness/worktree.json`:

```sh
.chrono-harness/bin/chrono-worktree recover --host-root . --config .chrono-harness/worktree.json --plan .chrono-harness/state/recover.json
.chrono-harness/bin/chrono-worktree cleanup --host-root . --config .chrono-harness/worktree.json --plan .chrono-harness/state/cleanup.json
.chrono-harness/bin/chrono-worktree cleanup-fetch --host-root . --config .chrono-harness/worktree.json --plan .chrono-harness/state/cleanup-fetch.json
```

Recovery validates the original failure, reconciled HEAD/index and owned lock;
staged changes still need a candidate commit and the canonical check. Cleanup
requires an explicit retained branch/commit and selected disposable artifacts.
Fetch-ref cleanup requires its original failed receipt and a fixed local branch
preserving the expected commit. Reports retain failures and distinguish verified
removal from unverified partial effects. See the pinned
[maintenance contract](https://github.com/ChronoAIProject/chrono-harness/blob/v0.1.0-beta.14/docs/worktree.md#registered-recovery-and-cleanup)
for complete plan formats. Lost recovery identity, damaged Git metadata and
PR/merge orchestration remain separate obligations.


## Interrupted operations

The installed tool writes separate immutable intents before checkout/lock effects
and before fetching. After establishing that the original process stopped, supply
an explicit intent digest and original-result presence/digest to:

```sh
.chrono-harness/bin/chrono-worktree recover-interrupted --host-root . --config .chrono-harness/worktree.json --plan .chrono-harness/state/interrupted-checkout.json
.chrono-harness/bin/chrono-worktree cleanup-fetch-interrupted --host-root . --config .chrono-harness/worktree.json --plan .chrono-harness/state/interrupted-fetch.json
```

Checkout recovery also requires the reconciled HEAD/index tree. Fetch cleanup
requires the expected current OID and a local branch retaining it; an already
absent ref needs an explicit retry plan. Both preserve the original bytes and
keep the original outcome unknown; terminal reports use ordinary maintenance.
See the pinned [interruption contracts](https://github.com/ChronoAIProject/chrono-harness/blob/v0.1.0-beta.14/docs/worktree.md#interrupted-checkout-recovery).
These commands do not reconstruct a lost index, make concurrent writers atomic,
or certify full governance or deterministic parity.

The pinned release also provides optional explicitly bound Git readers. This host keeps its registered scoped profile; adopting new binaries does not implicitly change the Git-binding or governance policy. See the pinned [Git facts contract](https://github.com/ChronoAIProject/chrono-harness/blob/v0.1.0-beta.14/docs/git-facts.md).

## CI projections and remote retirement

The pinned beta.14 binaries also provide explicit release-workflow generation and full-context CI transport. This host retains its registered scoped profile; installing binaries does not activate full governance. See the pinned [release CI](https://github.com/ChronoAIProject/chrono-harness/blob/v0.1.0-beta.14/docs/release-ci.md) and [full context CI](https://github.com/ChronoAIProject/chrono-harness/blob/v0.1.0-beta.14/docs/full-ci.md) contracts.

`chrono-worktree cleanup-remote` consumes an explicit state plan with the expected remote URL, work-branch OID and retained target commit. It performs exact leased deletion, verifies absence and preserves original failures; this is not an atomic remote transaction or a PR/merge verdict. See [remote retirement](https://github.com/ChronoAIProject/chrono-harness/blob/v0.1.0-beta.14/docs/worktree.md#remote-branch-retirement).

## Literal checkout and metadata recovery

The pinned binaries compare registered Git-tree/index identities with physical bytes, file types and owner executable bits. Git configuration cannot silently normalize changed inputs for this comparison; checkouts must materialize the registered exact bytes.

`chrono-worktree inspect-rebind` and `rebind` use an explicit branch, HEAD, chosen index tree, backup and donor to repair missing or damaged linked-checkout metadata while preserving observed work. They do not infer the lost historical index or original outcome, and interrupted rebind continuation remains outside this contract. See [metadata rebind](https://github.com/ChronoAIProject/chrono-harness/blob/v0.1.0-beta.14/docs/worktree.md#explicit-metadata-rebind) and [literal identity](https://github.com/ChronoAIProject/chrono-harness/blob/v0.1.0-beta.14/docs/git-facts.md#literal-checkout-identity).

The pinned `chrono-ci migrate` command supports explicit owned workflow transitions and preserves host configuration. For ordinary binary upgrades the existing provider, SDK profiles and generated workflows stay unchanged; use `verify` and the same unit checks. See [host customization and updates](https://github.com/ChronoAIProject/chrono-harness/blob/v0.1.0-beta.14/docs/ci-units.md#host-customization-and-updates).
