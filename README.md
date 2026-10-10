# chrono-harness-examples-go

可实际运行的宿主接入样例，用不同语言和目录检验显式登记、DELTA 选测和统一入口。

`engine/rates/` 是 Go 库；`verification/contracts/` 是独立测试 module。两个项目均没有 go.sum，也没有根工作区。

## 运行

需要 Git、Python ≥3.9、curl 和可下载固定发布/SDK 的网络。harness 使用 [chrono-harness v0.1.0-beta.20](https://github.com/ChronoAIProject/chrono-harness/releases/tag/v0.1.0-beta.20) 的预构建二进制；`.chrono-harness/distribution.json` 锁定发布清单、平台与摘要，生成的 `install.py` 执行统一安装。宿主不保留 harness 源码包，不需要 Rust。宿主 Go/Node/TypeScript SDK 独立登记在 bootstrap.json，支持 macOS arm64、Linux x86_64。

```sh
python3 .chrono-harness/bootstrap.py . --profile rates
.chrono-harness/bin/chrono-harness check --unit rates
```

候选必须是当前干净提交。上述短命令属于待安装兼容公开版本的配置候选；当前 beta.20 锁不兼容。输入生产者从登记的工作流目标解析本地固定端点，CI 从完整事件端点解析；不手写 shell 准备或日常 SHA 参数。报告仍由工具维护，同命令不宣称环境完全等价。

每个 profile 明确选择 Git 版本探测。`bootstrap-result.json` 的 `tools` 记录所选
probe 的实际调用路径、解析目标、执行物前后摘要，以及原始输出、摘要和退出码；
探测失败或执行物改变时保留失败结果并退出非零。调用别名保留，不因采集身份而改用
目标文件名。这里的 `passed` 只表示启动与所选探测成功，不是 harness 检查或完整
输入闭包的判词。这些读数供 AI 显式更新工具登记，程序不自动更新预期版本、改写配置或赋予政策准入。

## 条件独立 job 与汇总候选

这是配置／投影准备，尚未接入兼容公开运行时。`.chrono-harness/distribution.json` 保留 beta.20 的真实版本与摘要；不要用该安装执行新的短命令或发布此 workflow。兼容公开版本安装、本地检查、原生事件与 PR 落地由后续接入完成；生成和静态 verify 不证明这些结果。

`.chrono-harness/ci/units.json` 是宿主唯一 CI 源。一个父 workflow 保留 dev／integration push 和 dev PR：`detect` 读取完整 Git 树差异，条件 job 各自保留原 runner、bootstrap profile、timeout、checkout、上传和重跑；无关 job 在申请 runner 前跳过。汇总 `aggregate` 使用 `always()`，唯一必需状态仍为 **chrono / collection**。实际 dev ruleset 已要求该状态；E1 没有修改远端规则。

| 单元 ID | 完整测试计划 | 父 workflow job |
|---|---|---|
| `rates` | `test:rates-tests` | `unit_rates` |
| `harness` | `test:bootstrap-tests` | `unit_harness` |

安装兼容公开版本后，在宿主根使用同一个登记短入口：

```sh
python3 .chrono-harness/bootstrap.py . --profile all
.chrono-harness/bin/chrono-harness check
.chrono-harness/bin/chrono-harness check --unit rates
.chrono-harness/bin/chrono-harness check --collect
```

选单元时 bootstrap 使用同名 profile；汇总与检测用既有 `collection` profile，均不安装业务 SDK。config schema4 登记 chrono-worktree 本地生产者与 chrono-ci 原生生产者，后者拥有检测、事件输入与报告获取；`--collect` 不接 manifest 参数，不执行缺失的业务操作。需要但跳过、失败、缺失、陈旧或错配的单元均拒绝；未选单元无需假报告。单元分别在独立 checkout 执行，当前工作目录并发没有锁保证。

PR 使用事件 base/head；dev push 使用完整 before/after（含多次提交），integration push 保留显式 `origin/dev` 基线规则，检测只观察一次并固定给后续 job。无 workflow paths 过滤、API 文件列表截断或 HEAD^ 兜底。文档 DELTA 可以无需业务操作，但仍走结构与汇总检查。

上传根显式缩为每个单元的 `.chrono-harness/state/units/ID/` 和汇总的 `.chrono-harness/state/collection/`，包含隐藏原始证据；检测证据在 `.chrono-harness/state/detection/`。既有 context 和报告路径保留。旧的单元 workflow 地址保留在 provider 作为迁移身份，文件通过显式 previous／next migrate 退役并从 FILEMAP 与 required_inputs 移除。其它文件不退役。现有 1 MiB manifest、64 MiB 单元报告与业务操作时限保持，实际成本未知。

宿主自定义入口保持显式：config.json 是平台映射，短入口、输入生产者、工具和环境由 git/macos.json 与 git/linux.json 的原生政策分别拥有；业务命令和独立测试配对仍由 projects.json 拥有，选测边与计划由 FILEMAP 拥有，SDK 由 bootstrap.json 拥有。两个平台的 Git 值取自现有 Go 声明；TS／mix 的真实平台执行验证待完成。更新时保留这些宿主值，通过 units.json 生成／verify；公开版本号和摘要只能在兼容资产实际发布后更新。

## 登记与验收

- `engine/rates/rate.go` → `test:rates-tests`。
- README.md 修改 → 不运行产品测试；未登记文件 → 失败；实际测试非零 → harness 非零。
- 项目配对、命令参数和依赖均在 `.chrono-harness/` 登记；不从扩展名、import、module 或目录推断选测。
- `CLAUDE.md` 由原子规则生成；`AGENTS.md` 是其相对符号链接。修改指令源后运行 `.chrono-harness/bin/chrono-instructions generate --host-root .`。
- CI 修改入口是 `.chrono-harness/ci/units.json`；运行 `.chrono-harness/bin/chrono-ci generate --host-root . --config .chrono-harness/ci/units.json`。受管工作流由 `chrono-ci verify` 检查。`push_baselines` 显式登记 integration 分支的所有 push 以 origin/dev 为基线，后续修复推送仍覆盖整个分支差异；dev 保持事件的 before/after。

Git 未跟踪清单排除显式登记生成目录的内容，避免 SDK 与状态产物耗尽清单输出上限。未登记的忽略文件、相邻路径、被跟踪修改，以及替代目录的文件／符号链接仍须检查；它不自动发现归属或依赖。

## 当前边界

本仓运行现役 `chrono-ci-check/v3` scoped profile，验证实际命令、显式选测、干净快照和退出结果。它不冒充完整七判官治理，不证明工具链输入闭包完整或测试依赖无遗漏。该版本的通用 projects 判官已允许省略 manifest/lock/root 并接受任意显式 action；语言专属检查由可选适配器承载。本仓完整治理的接入仍未完成。

本地与 CI 通过相同 bootstrap 从公开 Release 校验安装；不需要跨仓凭据。安装结果见 `.chrono-harness/state/distribution.json`，语言 SDK 版本另见 `bootstrap-result.json`。成本暂未测量，登记为 unknown。

[主库与示例索引](https://github.com/ChronoAIProject/chrono-harness/blob/dev/docs/examples.md) 列出 Go、TS 和混合语言宿主。

## Registered worktrees

The pinned release also installs `chrono-worktree`. The host policy is
`.chrono-harness/worktree.json`; shared registries explicitly declare `dev`,
`feature/`, `integration/`, file ownership and artifacts. Project and FILEMAP
registrations have one owner; directory names and languages do not select work.

The host retains its v2 worktree policy. Its use with the staged schema4
host declarations still needs compatible public binaries. Successful creation
or reconstruction publishes the finalized original report and
`.chrono-harness/state/origin.json` in the new destination. Both branch kinds use
the `integration` check role; local context and collection manifest paths are
`.chrono-harness/state/local/context.json` and
`.chrono-harness/state/collection/manifest.json`. The source and fetched target
`dev` must carry the same committed policy before starting a lane. Existing lanes
without an origin receipt need reconstruction from an adopted source; no origin
evidence is synthesized. The staged scoped short entry does not activate full governance.

```sh
.chrono-harness/bin/chrono-worktree start --host-root . --config .chrono-harness/worktree.json --kind feature --name change --path ../my-change
```

The destination must not exist. `reconstruct` uses the same arguments plus
`--plan .chrono-harness/state/reconstruction.json`, with explicit fixed base and
candidate OIDs and a complete carry/retire path list. See the
[worktree contract](https://github.com/ChronoAIProject/chrono-harness/blob/v0.1.0-beta.20/docs/worktree.md).
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
[maintenance contract](https://github.com/ChronoAIProject/chrono-harness/blob/v0.1.0-beta.20/docs/worktree.md#registered-recovery-and-cleanup)
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
See the pinned [interruption contracts](https://github.com/ChronoAIProject/chrono-harness/blob/v0.1.0-beta.20/docs/worktree.md#interrupted-checkout-recovery).
These commands do not reconstruct a lost index, make concurrent writers atomic,
or certify full governance or deterministic parity.

## 显式 Git 配置

候选检查配置的 `policy.facts_config`、`registration_config` 和 CI provider v4 的
`facts_config` 都指向 `.chrono-harness/config.json`。既有 git/platforms.json
保留相同的显式映射；原生政策位于 git/macos.json 与 git/linux.json，均为 schema4。选择器明确列出 macOS arm64 与 Linux x86_64
各自的执行物路径、SHA-256、版本、环境和文件输入；不探测后自动接受新工具。
两个平台仍执行同一条 `chrono-harness check` 命令。

Git 子进程只使用登记环境，禁用系统全局配置，选择宿主登记的 `global.config`；
它明确 include 当前应缺席的 `local.config`。判官在 Git 调用前后检查全局配置摘要
及 include 缺席状态，变化会报错。修改这些约束时，AI 显式更新文件、摘要和 FILEMAP
依赖，再运行规范检查。更新平台工具身份时，先读 bootstrap 的实际探测证据，修改
对应平台注册值并验证；安装和探测不会改写预期值。

当前 macOS 的 `/usr/bin/git` 可以委托 Apple 开发工具；仓库本地 Git 配置、委托工具、
库、OS 和网络输入还没有完整登记。本节只声明已绑定的执行物、环境和文件，不认证
完整闭包或跨平台同判。报告包含 Git 过程原始输出，宿主将判官报告上限显式设为
16 MiB；这不是所有宿主适用的容量值。合同见固定版本的
[Git facts](https://github.com/ChronoAIProject/chrono-harness/blob/v0.1.0-beta.20/docs/git-facts.md)。

## CI projections and remote retirement

The pinned binaries also provide explicit release-workflow generation and full-context CI transport. This host retains its registered scoped profile; installing binaries does not activate full governance. See the pinned [release CI](https://github.com/ChronoAIProject/chrono-harness/blob/v0.1.0-beta.20/docs/release-ci.md) and [full context CI](https://github.com/ChronoAIProject/chrono-harness/blob/v0.1.0-beta.20/docs/full-ci.md) contracts.

`chrono-worktree cleanup-remote` consumes an explicit state plan with the expected remote URL, work-branch OID and retained target commit. It performs exact leased deletion, verifies absence and preserves original failures; this is not an atomic remote transaction or a PR/merge verdict. See [remote retirement](https://github.com/ChronoAIProject/chrono-harness/blob/v0.1.0-beta.20/docs/worktree.md#remote-branch-retirement).

## Literal checkout and metadata recovery

The pinned binaries compare registered Git-tree/index identities with physical bytes, file types and owner executable bits. Git configuration cannot silently normalize changed inputs for this comparison; checkouts must materialize the registered exact bytes.

`chrono-worktree inspect-rebind` and `rebind` use an explicit branch, HEAD, chosen index tree, backup and donor to repair missing or damaged linked-checkout metadata while preserving observed work. They do not infer the lost historical index or original outcome. The pinned `resume-rebind` entry can continue from an original intent and explicit partial-result observations; conflicting state still requires AI reconciliation. See [metadata rebind](https://github.com/ChronoAIProject/chrono-harness/blob/v0.1.0-beta.20/docs/worktree.md#explicit-metadata-rebind) and [literal identity](https://github.com/ChronoAIProject/chrono-harness/blob/v0.1.0-beta.20/docs/git-facts.md#literal-checkout-identity).

The pinned `chrono-ci migrate` command supports explicit owned workflow transitions and preserves host configuration. For ordinary binary upgrades the existing provider, SDK profiles and generated workflows stay unchanged; use `verify` and the same unit checks. See [host customization and updates](https://github.com/ChronoAIProject/chrono-harness/blob/v0.1.0-beta.20/docs/ci-units.md#host-customization-and-updates).
