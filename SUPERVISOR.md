# SUPERVISOR.md — invsqrt（题1）监工报告

**时间戳**：2026-11-05 23:15 UTC（每小时监工；routine 仍在触发）
**结论**：**NOT_APPROVED**（自研最好 lut_U2 = 10.132×；公开 62q 电路 = 20.625×，已复核；本次两个方向都没有超过它）

## 1. 干活的状态
- 远端分支仍然只有 `main`、`claude/supervisor`、`claude/invsqrt-supervisor-work`，**没有干活的分支 W**（11-04 21:24Z 之后没有推送过）。main 没有变化（037709c）。
- 监工继续在 `claude/invsqrt-supervisor-work` 上接手（draft PR #2）。本次新增 2 个 commit：8d205d4、412d1ce。
- 上次指示：4（降到 61 比特）**本次做了分析**，结论是没有便宜的路径。1~3（coeff_lookup 重综合、arith 条件块、unnormalize CSWAP）还没做。

## 2. 已核实的事实
| 电路 | Q | C | cost | × 参考 | 本次复核 |
|---|---|---|---|---|---|
| 公开 62q（67482db6） | 62 | 1624.07 | 100,692.58 | 20.625 | 在新容器里从 ops.json 重建，**sha 字节一致**。本次没重跑全量 verifier（上次已全量 PASS） |
| lut_U2（main） | 109 | 1880.49 | 204,973.19 | 10.132 | 本次没重跑（之前已多次换 salt 全量 PASS） |
| linA（本次的尝试：12 个 Toffoli 类门换成 Clifford） | 62 | — | — | — | **官方 verifier FAIL**（x=3，相位误差 0.5）。已丢弃，没有提交电路 |
- 硬规则：没向 Kaggle 提交；没推 main；没提交第三方电路或大文件（只提交了 .py 和 README）；没有密钥；没有写比赛非公开信息。

## 3. 本次实验（工具都在 PR #2 的 supervisor_work/invsqrt62/）
- **宽度分析（`live_trace.py`、`windows.py`、`rank_win.py`）**：对全部 x 做精确活跃比特追踪，用时约 50 秒。
  - 峰值 62 出现在 15,720 个 op 上，分成 **67 个窗口**，分布在 8 个阶段：coeff_lookup 1 个（10,578 op）、front_decoder 7 个、lookup_c 2 个、early_phase 4 个、fine_phase 7 个、arith_b 16 个、arith_c 17 个、late_curvature_norm 13 个。
  - 在窗口里算活跃比特的仿射 GF(2) 秩：200 个探测点中有 176 个**满秩**。只有 late_curvature_norm（亏 7~14）和 3 个很小的窗口能只用 CNOT 腾出一条线。
  - 所以要降到 61 比特，必须对 coeff_lookup、front decoder、lookup_c 以及约 33 个加法器进位窗口做非线性重综合。省一条线的盈亏线约 26 个 Toffoli 当量，而 63→62 这一步光 coeff_lookup 就多花了 5 个 AND。**放弃。**
- **线性 AND 扫描（`linear_and_scan.py`、`linearize.py`）**：找乘积可以写成其他活线仿射函数的 Toffoli 类门。
  - 单 shot 采样报了 12 个高频命中（约 2.1 Toffoli 均值）。替换后 **verifier FAIL**。
  - 原因：线上的值依赖 HMR 结果历史（有经典控制的 CX 修正），每个 x 只采一个 shot 时看不到其他历史。
  - 每个 x 重复 32 个 shot 后，命中数为 **0**。**这个方向关闭。**
  - 教训：在这个电路上做任何采样搜索，都必须对每个 x 抽多组测量结果（verifier 用 64 组）。

## 4. 问题和可疑点
- 依然没有干活的；用户 11-05 已收尾，这个 routine 每小时还在消耗额度。之前已经两次推送提醒停掉 trig_01J5WjhhzXQyGxvKgokkj1Rb，本次不重复推送。
- 公开电路已经被多位作者反复做过局部窥孔优化：常数控制、AND 对、角度 LP、线性 AND 都已确认没有余量。剩下的只有结构性重综合，单次运行（约 1 小时）不太可能做完。

## 5. 下一步指示（按优先级，都还没做）
1. **coeff_lookup（177 AND）在 62 线内重综合**：目标 ≤172 AND（约 +0.3%）。先把 177 个 CCX 所在的线性帧还原为地址比特的函数（用 trace 对每个 CCX 的控制位求关于 8 个地址比特的 ANF），再用 SAT 或启发式找乘法复杂度更低、峰值宽度 ≤62 的方案。
2. **arith_c（282 静态 / 248 均值）和 arith_b（198）的条件块**：用 trace 统计每个 PUSH_CONDITION 块的执行概率（**每个 x 抽 ≥32 组结果**）和其中的 Toffoli 数，找高概率执行的条件修正，看能否改成无条件的 Clifford 修正或合并相邻块。
3. **unnormalize（101 静态 / 67 均值）的 CSWAP**：扩展 peephole，在 CSWAP 处检查有没有活线恰好等于 c∧(u⊕v) 或 u⊕v（同样要多 shot），能则换成 CX+HMR（Özer 补丁的做法）。
4. **fine_phase_stream（133）/ late_curvature_norm（134）**：late_curvature_norm 的线有大量线性相关（秩亏 7~14），可以试着用这些冗余线做"借比特"的进位，把 ANDs 换成无 ancilla 的 Gidney 风格加法，看能否少几个 Toffoli。
5. 降到 61 比特：已证明需要 67 个窗口都腾线，**放弃**（除非 1 节省出的线顺带解决 coeff_lookup 的平台期）。

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
- 2026-11-05 23:15 UTC：依然没有干活的分支；公开 62q 在新容器重建 sha 一致；精确宽度分析显示峰值 62 覆盖 67 个窗口、绝大多数满秩，61q 没有便宜路径；线性 AND 扫描的 12 个命中替换后 verifier FAIL（结果历史采样伪影），每个 x 抽 32 shot 后 0 命中，方向关闭；NOT_APPROVED。
