本仓是 chrono-harness 的 go 接入样例。源文件、项目、测试和依赖全部显式登记于 .chrono-harness/FILEMAP.json 与 projects.json；目录位置没有推断权威。

本地与 CI 的唯一检测入口见 README.md。当前采用 chrono-ci-check/v3 scoped profile 与显式独立单元；其通过不代表完整七判官、完整工具链输入闭包或本地/CI 环境等价。生产项目每个都有独立测试项目，mix 中的独立脚本也有独立测试。宿主方法由 chrono-instructions 生成，AGENTS.md 是 CLAUDE.md 的相对链接。

单元、测试归属、启动 SDK 与独立 job 显式登记在 `.chrono-harness/ci/check.json`、`units.json` 和 `bootstrap.json`。本地与 CI 都用 `check --unit ID`；收齐同一 DELTA 的原始结果后用 无值的 `check --collect`。共享 checkout 并发未提供锁，使用独立 checkout。

本仓的 scoped 检查与 CI 事件准备显式采用 `.chrono-harness/config.json`，分别登记 macOS arm64／Linux x86_64 的 Git 执行物、版本、环境和 global 配置输入；未知平台、版本／摘要漂移或已登记缺席的 include 出现均须失败。配置更改由 AI 根据 bootstrap 实测更新并验证；工具不改预期值。仓库本地 Git 配置、Apple Git 的委托工具、OS／网络及完整 SDK 输入闭包仍未认证，平台选择不证明跨平台同判。


本轮采用固定测试版 v0.1.4-dev.43435181626.1.g7c20c55c12e26f31c1afefecbc75ef045dd70d6f，源码 eb40976ebd99b7844420fcf49c95c4ee3ab234ca。生成的 install.sh 仅安装显式所选工具，bootstrap.py 调用它后继续安装本仓登记 SDK。根 config.json schema4 选择本地或 CI 输入，普通检查只运行 `.chrono-harness/bin/chrono-harness check`；候选已提交且干净，单元／汇总分别追加 `--unit ID`／无值 `--collect`。

CI 使用当前 provider v4 的同一父 workflow、DELTA detector 和独立条件 job；旧单元 workflow 已由当前父 workflow 覆盖并迁移。修改源后运行 `chrono-ci generate` 与 `verify`；指令源修改后运行 `chrono-instructions generate --host-root .`。指南按当前 manifest 的中文选择生成；业务测试、SDK profile 和显式 Git pin 继续由各自登记负责。

本轮规则、CI 和安装链迁移先完成 feature → integration 的真实 PR 验收，再交付 integration → dev。GitHub 未开放自动合并，尝试使用现有权限启用返回 403；不申请额外权限。等待当前 head 的适用 CI 全部通过后，使用现有合并权限匹配当前 head 合并，不绕过现有保护，再核实际落地提交与 CI。

根 config.json 是已登记的 OS／架构选择器，分别读取 git/macos.json 与 git/linux.json 中的完整 schema4 政策；检查 profile 的 registration_config 与 facts_config 都绑定根入口。两份政策保留原 Git 执行物 pin、global 配置及缺席 include，短命令、CI 与业务 action 同时由所选政策提供。

bootstrap 将自己的完整观察回执同时写入 bootstrap-result.json 和 stdout，供原生 CI 日志保留本轮精确 Git 版本、路径和摘要。AI 从该候选实际回执显式更新漂移的 pin，不使用其他仓库的观察或把预期置空。
