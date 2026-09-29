本仓是 chrono-harness 的 go 接入样例。源文件、项目、测试和依赖全部显式登记于 .chrono-harness/FILEMAP.json 与 projects.json；目录位置没有推断权威。

本地与 CI 的唯一检测入口见 README.md。当前采用 chrono-ci-check/v3 scoped profile 与显式独立单元；其通过不代表完整七判官、完整工具链输入闭包或本地/CI 环境等价。生产项目每个都有独立测试项目，mix 中的独立脚本也有独立测试。宿主方法由 chrono-instructions 生成，AGENTS.md 是 CLAUDE.md 的相对链接。

单元、测试归属、启动 SDK 与独立 workflow 显式登记在 `.chrono-harness/ci/check.json`、`units.json` 和 `bootstrap.json`。本地与 CI 都用 `check --unit ID`；收齐同一 DELTA 的原始结果后用 `check --collect MANIFEST`。共享 checkout 并发未提供锁，使用独立 checkout。
