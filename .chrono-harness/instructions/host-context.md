本仓是 chrono-harness 的 go 接入样例。源文件、项目、测试和依赖全部显式登记于 .chrono-harness/FILEMAP.json 与 projects.json；目录位置没有推断权威。

本地与 CI 的唯一检测入口见 README.md。当前采用 chrono-ci-check/v3 scoped profile 与显式独立单元；其通过不代表完整七判官、完整工具链输入闭包或本地/CI 环境等价。生产项目每个都有独立测试项目，mix 中的独立脚本也有独立测试。宿主方法由 chrono-instructions 生成，AGENTS.md 是 CLAUDE.md 的相对链接。

单元、测试归属和启动 SDK 仍显式登记在 `.chrono-harness/ci/check.json`、`units.json` 和 `bootstrap.json`。候选使用一个父 workflow：完整 Git DELTA 检测、条件独立单元 job 和 `always()` 汇总；唯一必需状态仍是 `chrono / collection`。本地与 CI 的登记入口是 `.chrono-harness/bin/chrono-harness check`，单元用 `check --unit ID`，汇总用无值的 `check --collect`。输入与汇总 manifest 由 config schema4 登记的 chrono-worktree／chrono-ci 生产者解析，不手写准备 shell；共享 checkout 并发未提供锁。

本仓候选的 scoped 检查与 CI 事件准备显式采用 `.chrono-harness/config.json` 的平台选择器（既有 `.chrono-harness/git/platforms.json` 保留其显式 Git 映射），分别登记 macOS arm64／Linux x86_64 的 Git 执行物、版本、环境和 global 配置输入；未知平台、版本／摘要漂移或已登记缺席的 include 出现均须失败。配置更改由 AI 根据 bootstrap 实测更新并验证；工具不改预期值。仓库本地 Git 配置、Apple Git 的委托工具、OS／网络及完整 SDK 输入闭包仍未认证，平台选择不证明跨平台同判。

当前是待接入的配置／投影候选：distribution.json 仍锁定公开 beta.20，该安装不能执行新短入口与条件父 workflow。须先发布并按真实摘要接入兼容工具，再核本地短检查与原生 push／PR／dev；生成、verify、幂等性通过均不是规范／原生验收。Go 现有 macOS／Linux Git 登记是候选工具身份来源；TS／mix 采用这些显式值，实际宿主 SDK、Git 平台和输入闭包仍待验证。无 Rust 源码构建进入宿主；语言、项目配对、命令、SDK profile、23 个原子根与 zh-CN 指令均保持。成本未知。
