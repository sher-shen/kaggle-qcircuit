> 10/29 下午更新：公开最高已到本地 GM 22.81（拼盘），见 top_public_1029.md；下面 22.37 是上午数字

# 10/29 竞争格局（独立 agent 审核 + 抽查核实）

来源：github.com/acco-cyber/Quantum-Circuit 的 STATUS.md / RUNLOG.md（一个每小时自动跑的多赛题 agent 队，同时打量子、Smart Buildings、NTL）

- 公榜 10/28–29 前三 ≈ 26.14 / 25.53 / 25.34；10/27 时第 92/1171 名是 19.58，约 25 队卡在同一平台 19.579
- **抄公开 notebook 就能到 ≈22.37**[三方旧数据，与 top_public 的 889q/43.8 万 Toffoli 对不上]（invsqrt 76q + DQI 883q/658 Toffoli ≈56× + 化学 heliosli/somejoint 重拟合 ≈9.6×）→ 地板很高，跟正方形题一样
- dfthcsos **不是蓝海**：公开 notebook 已到 ≈9.6×，卡在误差和 λ（1-范数）约束上，要再进步得换 1-范数更低的分解
- 也有队只做 invsqrt + dqi、dfthcsos 留 1.0×（github.com/zjukop3/google-quantum-circuit-compilation-2026-support）
- 算力不是门槛：验证单核 CPU 就能跑，官方不要求 LLM API
- 结论：单题奖对手是全榜强队；中期里程碑基本被公开 notebook 锁死
