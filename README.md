# chrono-harness-examples-go

可实际运行的宿主接入样例，用不同语言和目录检验显式登记、DELTA 选测和统一入口。

`engine/rates/` 是 Go 库；`verification/contracts/` 是独立测试 module。两个项目均没有 go.sum，也没有根工作区。

## 运行

需要 Git、Python ≥3.9、curl 和可下载固定发布/SDK 的网络。harness 使用 [chrono-harness v0.1.0-beta.4](https://github.com/ChronoAIProject/chrono-harness/releases/tag/v0.1.0-beta.4) 的预构建二进制；`.chrono-harness/distribution.json` 锁定发布清单、平台与摘要，生成的 `install.py` 执行统一安装。宿主不保留 harness 源码包，不需要 Rust。宿主 Go/Node/TypeScript SDK 独立登记在 bootstrap.json，支持 macOS arm64、Linux x86_64。

```sh
python3 .chrono-harness/bootstrap.py .
.chrono-harness/bin/chrono-harness check --config .chrono-harness/ci/check.json --base <完整基线SHA> --candidate <完整候选SHA>
```

候选必须是当前干净提交。首个无父提交使用 `--initial --candidate <SHA>`，代替 `--base`。报告由工具写入 `.chrono-harness/state/check.json`。CI 的检测步骤使用完全相同的 harness argv；平台和 SDK 读数由 bootstrap-result.json 记录，指令相同不宣称环境完全等价。

## 登记与验收

- `engine/rates/rate.go` → `test:rates-tests`。
- README.md 修改 → 不运行产品测试；未登记文件 → 失败；实际测试非零 → harness 非零。
- 项目配对、命令参数和依赖均在 `.chrono-harness/` 登记；不从扩展名、import、module 或目录推断选测。
- `CLAUDE.md` 由原子规则生成；`AGENTS.md` 是其相对符号链接。修改指令源后运行 `.chrono-harness/bin/chrono-instructions generate --host-root .`。
- CI 修改入口是 `.chrono-harness/ci/github.json`；运行 `.chrono-harness/bin/chrono-ci generate --host-root . --config .chrono-harness/ci/github.json`。受管工作流由 `chrono-ci verify` 检查。`push_baselines` 显式登记 integration 分支的所有 push 以 origin/dev 为基线，后续修复推送仍覆盖整个分支差异；dev 保持事件的 before/after。

## 当前边界

本仓运行现役 `chrono-ci-check/v1` scoped profile，验证实际命令、显式选测、干净快照和退出结果。它不冒充完整七判官治理，不证明工具链输入闭包完整或测试依赖无遗漏。该版本的通用 projects 判官已允许省略 manifest/lock/root 并接受任意显式 action；语言专属检查由可选适配器承载。本仓完整治理的接入仍未完成。

本地与 CI 通过相同 bootstrap 从公开 Release 校验安装；不需要跨仓凭据。安装结果见 `.chrono-harness/state/distribution.json`，语言 SDK 版本另见 `bootstrap-result.json`。成本暂未测量，登记为 unknown。

[主库与示例索引](https://github.com/ChronoAIProject/chrono-harness/blob/dev/docs/examples.md) 列出 Go、TS 和混合语言宿主。
