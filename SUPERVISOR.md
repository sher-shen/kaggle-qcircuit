# SUPERVISOR.md — invsqrt（题1）监工报告

**时间戳**：2026-11-06 03:50 UTC（每小时监工；routine 仍在触发）
**结论**：**NOT_APPROVED**（自研最好的是 lut_U2，10.132×；公开的 62q 电路是 20.625×，本次又做了一次全量复核，PASS。本次又关掉 2 个方向，没有新的提升）

## 1. 干活的状态
- 远端分支和上次一样：`main`（037709c）、`claude/supervisor`、`claude/invsqrt-supervisor-work`。**没有干活的分支 W**，11-04 21:24Z 以后没有任何推送。PR 只有 #1（已合并）和 #2（draft，监工开的）。
- 监工继续在 `claude/invsqrt-supervisor-work` 上接手，本次推送了 5c2075c，内容是 `segpat.py` 和 README 里新加的「每个 stage 宽度 vs Toffoli 数」表。
- 上次的指示 3（末尾两个互补条件块）本次做完了，已关闭。指示 1、2、4 还没做。

## 2. 已核实的事实
| 电路 | Q | C | cost | × 参考 | 本次复核 |
|---|---|---|---|---|---|
| 公开 62q（67482db6） | 62 | 1624.07 | 100,692.58 | 20.625 | 在新容器里从 ops.json 重建，**sha 字节一致**。**官方 verifier 全量跑了 200,540,928 shot，PASS**：Toffoli 1327.483、41 个旋转、eps 2.434e-13、worst 0.99932（x=161），和以前一致 |
| lut_U2（main） | 109 | 1880.49 | 204,973.19 | 10.132 | 本次没重跑（之前已多次换 salt 全量 PASS） |
- 新容器里重跑了 `live_trace.py`，结果一致：峰值 62，有 15,720 个 op 处在峰值，第一个在 op 3823，最后一个在 op 36834。
- 硬规则检查：没有向 Kaggle 提交；没有推 main；只提交了 .py 和 README；没有第三方电路、大文件或密钥；没有写入比赛非公开信息。

## 3. 本次实验
- **每个 stage 的宽度和 Toffoli 数，62q 和 63q `9a8627` 对比**（表在 README 里）。63q 更便宜的 stage 有 coeff_lookup、early_phase_taps、arith_b、fine_phase_stream、arith_c、unnormalize。其中**只有 unnormalize 在 62q 里有空闲的线**（最大占用 36），但它只差 0.6 个 Toffoli（0.04%）。arith_a（最大 61）、lookup_b（56）、phase_merge_repair（60）这三个 stage 有空闲，但 63q 在这些 stage 并不更便宜（arith_a 反而贵 19）。结论：**「不加宽度就能直接搬 63q 的做法」这一类已经穷尽了。**
- `segpat.py`：unnormalize 里 ops 46752~46776 的解码器，输入是 5 个比特（q0..q3、q23），对应 29 种取值，输出 CSWAP 梯子要用的标志。可以手工重综合，但最多省 0.6 个 Toffoli，所以没做。
- **指示 3 已关闭**：46862~46981（条件位 318）和 46982~47211（条件位 8045 = ¬318）两块有 6 个 AND 组成的公共进位链。每个 shot 只会跑其中一条分支，按执行次数计费的话，现在已经是单份的成本，把它提到条件外面省不了任何东西。
- arith_c 差的 2.0 个 Toffoli 分散在 op diff 里约 50 个重排过的块里，静态 Toffoli 数互相抵消，找不到一个单独可以搬的位置。

## 4. 问题和可疑点
- 依然没有干活的。用户 11-05 已经收尾，这个 routine 每小时还在消耗额度（之前已经推送过两次提醒，本次不再推送）。
- 剩下的方向都要做结构性的重综合（coeff_lookup 的 SAT 求解、跨 stage 的线分配），每个上限 ≤0.3~0.5%，一小时一次的接手做不完。

## 5. 下一步指示（按优先级，都还没做）
1. **coeff_lookup（177 AND）在 62 根线内重综合，目标 ≤172**：先 trace 出每个 CCX 控制位的 ANF（关于 8 个地址比特），再用 SAT 或启发式搜索满足「峰值 ≤62」的方案。coeff_lookup 里有 379 个 op 的占用是 61，从这些位置入手。
2. **跨 stage 的线分配**：arith_a（最大占用 61）和 phase_merge_repair（60）有空闲。查一下 fine_phase_stream 前后能不能把某个寄存器暂时搬到其他编码，或者推迟计算，从而腾出一根线，把 63q 版的 fine_phase_stream（省 4）整体搬过来。
3. **把 unnormalize 的解码器（46752~46776）重写成 63q 的 3-AND 形式**：线够用（最大占用 36），上限 0.6 个 Toffoli。要把 Z 13000 和 14010 的相位修正一起处理，用 qcheck 和 verifier 检查。
4. **把旋转放进测量条件块**（n_rot 按执行概率计费）：先在纸上证明可行。
5. 已关闭：61 比特、删旋转、同角旋转对、线性 AND、AND 对、CSWAP 目标、op 15528、op 25874、互补块共享 AND 链、直接搬 63q 的 stage。

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
- 2026-11-06 00:25 UTC：依然没有干活的分支；公开 62q 重建 sha 一致，精确相位 trace 重跑一致；删旋转 LP（8 个候选）全部不可行；条件块只有 51.5 个 Toffoli 且局部最优；发现两组旋转有 8 对同角度，但宽度检查（峰值 62 覆盖第 1 组 84% 的 op）表明留住比特得不偿失；NOT_APPROVED。
- 2026-11-06 01:30 UTC：依然没有干活的分支；公开 62q 重建 sha 一致；按交换性推广的 AND 对扫描 0 对，CSWAP 目标互补扫描 0 个（47040 是采样伪影）；重读 cost 公式确认 n_rot 按执行概率计费，据此新增"旋转放进条件块"方向；推送 a7daef3 到 invsqrt-supervisor-work；NOT_APPROVED。
- 2026-11-06 02:40 UTC：依然没有干活的分支；公开 62q 重建 sha 一致，**官方 verifier 全量重跑 PASS（20.625×）**；对比了 62q 和 63q 两版每个 stage 的 Toffoli 数，两次移植尝试都失败（op 15528 改 HMR 后末态不干净，因为 q1 要一直留着；op 25874 的两个选择位互斥但不互补）；推送了新工具到 invsqrt-supervisor-work；NOT_APPROVED。
- 2026-11-06 03:50 UTC：依然没有干活的分支；公开 62q 重建 sha 一致，**官方 verifier 全量 PASS（20.625×）**；对比 62q 和 63q 每个 stage 的宽度和 Toffoli 数，发现只有 unnormalize 有空闲的线，但只差 0.6 个 Toffoli；互补块的公共 AND 链提到外面没有收益，已关闭；推送了 5c2075c 到 invsqrt-supervisor-work；NOT_APPROVED。
