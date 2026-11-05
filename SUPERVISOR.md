# SUPERVISOR.md — invsqrt（题1）监工报告

**时间戳**：2026-11-05 22:55 UTC（每小时监工；routine 仍在触发）
**结论**：**NOT_APPROVED**（自研最好仍是 lut_U2 = 10.132×；本次在云端复现了公开 62q 电路 = **20.625×**，但还没有超过它的改进）

## 1. 干活的状态
- 远端分支只有 `main`、`claude/supervisor`、`claude/invsqrt-supervisor-work`，**依然没有干活的分支 W**（11-04 21:24Z 撞限额后就没推送过）。
- PR #1 已合并（81c976d）。本次按规则从最新 main 重开 `claude/invsqrt-supervisor-work`（9737da5），开了 **draft PR #2**。
- 上次指示 1（从公开 62q 电路出发）：**本次做了**。2~4（r guard -3、y 步 b2、自写加法器）：没做。

## 2. 已核实的事实（本次亲自重跑）
| 电路 | Q | Toffoli（均值） | C | cost | × 参考 | 结果 | 复核方式 |
|---|---|---|---|---|---|---|---|
| lut_U2（main） | 109 | 1618 | 1880.49 | 204,973.19 | 10.132 | — | 新容器按 README 重建，**字节一致**（sha 27d75c8f）；本次没重跑 verifier（上次已换 salt 全量 PASS） |
| 公开 62q（67482db6，yoyobar + Özer 补丁，Apache-2.0） | 62 | 1327.48 | 1624.07 | **100,692.58** | **20.625** | **PASS**（官方 verifier 全量 200,540,928 shots，默认 salt，worst 0.99932 @ x=161） | 用 `add_repo` 后代理放行了 manwithacat/kickmix-macos 的匿名克隆（上次 403）；自写 `ops2kmx.py` 从 ops.json 重建，**sha 和公开文件字节一致** |
- 倍数 = 2,076,774.23 / verifier `score`（含 41 个旋转的总 cost），不是子项。注意：实测是 20.625×，比记忆里的"约 20.29×"高。
- 硬规则：没向 Kaggle 提交；没推 main；没提交第三方电路文件（只提交了转换脚本，README 写了来源和许可证）；PR #2 只有工具和公开电路的复核结果，没有比赛非公开信息；没有大文件和密钥（invsqrt62 目录 36 KB）。

## 3. 本次在公开 62q 电路上的实验（工具都在 PR #2 的 supervisor_work/invsqrt62/）
- `phase_trace.py`：对全部 3,133,452 个 x 做基态精确追踪（约 4 分钟），**和 verifier 完全对上**（worst 0.99932377 @161，Toffoli 均值 1327.48）。按绝对值算，最小余量 5.86e7（单位 2^-64 圈）在 x=52229。
- 旋转占 C 的 18%（41 个 × 28.8 T ≈ 295 Toffoli 当量）。`angle_lp.py` 用 LP 重新拟合 41 个角度来最大化余量：**没有提升**（×1.0000000），现有角度已经是 minimax 最优。这个方向的上限本来也只有约 1.2%。
- `peephole_scan.py`（找常数、相等或互补的控制位）：只找到在 ≤1.6% 输入上执行的条件 CCZ，合计 <0.1 Toffoli，**没用**。
- `pair_scan.py`（两个 AND 写同一目标且共享控制位，即 yoyobar 的 3→2 技巧）：**剩 0 对**。
- 结论：简单的局部窥孔已经被前人做完了；要超过 20.6×，必须在具体模块上做结构性重综合。

## 4. 问题和可疑点
- 依然没有干活的。用户在 11-05 已收尾，routine 却还在每小时消耗额度。上次已推通知提醒停掉 trig_01J5WjhhzXQyGxvKgokkj1Rb，本次再提醒一次。
- 公开电路的余量只有 0.07%（0.99932）。任何改动只要误差稍差一点就会 FAIL，所以每个改动都必须全量 verify。

## 5. 下一步指示（按优先级，都还没做）
1. **coeff_lookup（177 Toffoli）重综合**：这一段是 256 地址的查表，9a8627 版是 172 AND，62q 版为了省 1 比特多花了 5 个。在 62 比特约束下找 ≤172 AND 的写法（例如把 5 个临时积的 HMR 擦除提前，让出比特给原地构造）。用 `phase_trace.py` 先查全部 x 的相位和比特是否干净，再全量 verify。目标 −5 Toffoli ≈ +0.3%。
2. **arith_c（282 静态 / 248 均值）和 arith_b（198）里的测量条件块**：用 trace 统计每个 PUSH_CONDITION 块的执行概率和其中的 Toffoli 数，找"高概率执行的条件修正"，看能否改成无条件的 Clifford 修正或合并相邻块。
3. **unnormalize（101 静态 / 67 均值）**：照 Özer 的 CSWAP→CX+HMR 补丁，在其余 CSWAP 里找 `c·(u⊕v)` 已经存在于空闲线上的情况（扩展 `peephole_scan.py`：在 CSWAP 处检查有没有某条活线恰好等于 c∧(u⊕v) 或 u⊕v）。
4. **降到 61 比特**：`phase_trace.py` 加上活跃比特统计，找出峰值宽度出现的位置（stages 说 coeff_lookup 平台期有 39 条 scratch）。每省 1 比特 ≈ −1.6% cost，相当于约 26 Toffoli，是最值钱的方向。
5. 自研 109q 架构（r guard -3 等）只值约 +2.5%，而且远低于 20.6×，**放弃**。

## 历史
- 2026-11-05 01:35 UTC：没有干活的分支；复核 sv_B（1.181× PASS，一致）；监工接手，做了 LUT+二次方案 lut_C 4.417× 和 lut_D 4.763×（全量 PASS），lut_E 4.792×（全量 PASS），开了 draft PR #1；NOT_APPROVED。
- 2026-11-05 02:45 UTC：依然没有干活的分支；独立全量复核 lut_E（4.792×，一致）；监工继续接手，做了 signed-digit + 窗口 Horner（H 8.452×）、clamp（I 8.598×）、二分归一化（J 8.962×）、零顶移位（K **9.060×**），全部全量 PASS，推到 claude/invsqrt-supervisor-work，并更新 PR #1；NOT_APPROVED。
- 2026-11-05 03:35 UTC：依然没有干活的分支；换 salt 独立全量复核 K（一致）；监工继续接手，做了 droptop（L **9.158×**，113 q，全量 PASS）；maxq 限比特和 lutpoly5（M∈[1,2)）都没有变好；判断现在的架构已接近局部最优，下一步要改结构（自写加法器、高位提前打相位、c2 分组）；NOT_APPROVED。
- 2026-11-05 04:35 UTC：依然没有干活的分支；换 salt 独立全量复核 L（一致）；监工继续接手，做了 droprot（9.19×）和每段系数整数搜索（lut_N **9.457×**，112 q，全量 PASS）；发现 lutpoly5 的 rangeq bug（不是精度问题，放弃该方向）；fy=28 证明不可行；NOT_APPROVED。
- 2026-11-05 05:35 UTC：依然没有干活的分支；换 salt 独立全量复核 N（一致）；监工继续接手，做了 smallfirst（P 9.554×）和单加法器进位折叠（Q **9.755×**，112 q，全量 PASS）；算账否定了"s 高位用 AND+旋转"方向；NOT_APPROVED。
- 2026-11-05 06:45 UTC：依然没有干活的分支；换 salt 独立全量复核 Q（一致）；监工继续接手，做了 Horner 行舍入（carry-in）+ 粗 guard 0,-3,-5（T **9.867×**，111 q，全量 PASS）；算账否定了"a0/P 分开打相位"和"查表粗细分段"；NOT_APPROVED。
- 2026-11-05 07:50 UTC：依然没有干活的分支；换 salt 独立全量复核 T（一致）；监工继续接手，把行舍入推广到 fy=28（U 10.115×，110 q）并扫 maxq（U2 **10.132×**，109 q），全量 PASS；可达 x_norm 搜索无收益；判断精度方向已到头；NOT_APPROVED。
- 2026-11-05 21:40 UTC：依然没有干活的分支；PR #1 已被用户合并；新容器里重建 U2 字节一致，换 salt sv2105 全量复核 PASS（10.132×，一致）；k=8/10、deg3、fy29、粗 guard 扫描都没有达标的改进（0,-3,-4 省 52 Toffoli 但差 0.53 bit）；云端拿不到公开 62q 电路；推送了提醒用户停掉还在触发的监工 routine；NOT_APPROVED。
- 2026-11-05 22:55 UTC：依然没有干活的分支；U2 重建字节一致；**公开 62q 电路首次在云端拿到并重建（sha 67482db6 一致），官方 verifier 全量 PASS = 20.625×**；角度 LP、窥孔扫描、AND 对扫描都没有收益；从 main 重开 claude/invsqrt-supervisor-work 并开 draft PR #2（只有工具和复核）；NOT_APPROVED。
