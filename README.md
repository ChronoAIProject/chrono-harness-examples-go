# chrono-harness-examples-go

可实际运行的宿主接入样例，用不同语言和目录检验显式登记、DELTA 选测和统一入口。

`engine/rates/` 是 Go 库；`verification/contracts/` 是独立测试 module。两个项目均没有 go.sum，也没有根工作区。

## 运行

需要 Git、Python ≥3.9、rustup 和可下载依赖的网络。工具源码是固定修订 `f53f62e2da07ef087decf078584c7449158565da` 的独立分发包，位于 `.chrono-harness/distribution/`；它不是宿主代码。安装器仅构建登记的工具项目，并校验固定 Go/Node/TypeScript 下载包的摘要，不扫描宿主识别语言。支持 macOS arm64、Linux x86_64。

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
- CI 修改入口是 `.chrono-harness/ci/github.json`；运行 `.chrono-harness/bin/chrono-ci generate --host-root . --config .chrono-harness/ci/github.json`。受管工作流由 `chrono-ci verify` 检查。

## 当前边界

本仓运行现役 `chrono-ci-check/v1` scoped profile，验证实际命令、显式选测、干净快照和退出结果。它不冒充完整七判官治理，不证明工具链输入闭包完整或测试依赖无遗漏。完整 projects 判官在该固定版本仍要求 Cargo manifest/lock/target；这个缺陷正在 chrono-harness 主项目中解耦，本仓的无 manifest 项目就是后续完整接入的验收输入。

CI 从本仓内保留的固定工具分发包构建，无需另一个私有库的访问凭据。Rust 是工具的实现语言，不是宿主的语言要求。成本暂未测量，登记为 unknown。
