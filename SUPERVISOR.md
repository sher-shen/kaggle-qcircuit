# SUPERVISOR.md — invsqrt（题1）监工报告

**时间戳**：2026-11-06 02:40 UTC（每小时监工；routine 仍在触发）
**结论**：**NOT_APPROVED**（自研最好 lut_U2 = 10.132×；公开 62q 电路 = 20.625×，本次全量复核 PASS；本次两次"63q 做法移植"都没有收益）

## 1. 干活的状态
- 远端分支依然只有 `main`（037709c，没变）、`claude/supervisor`、`claude/invsqrt-supervisor-work`。**没有干活的分支 W**（11-04 21:24Z 之后没有任何推送）。
- 监工继续在 `claude/invsqrt-supervisor-work`（draft PR #2）上接手，本次推送了：`patch_ops.py`、`qcheck.py`、`segtof.py`、`diffst.py`，README 也更新了。
- 上次的指示 2（early_phase_taps / fine_phase_stream 搬回 63q 做法）本次做了两个具体点，都已关闭（见第 3 节）。指示 1、3、4 还没做。

## 2. 已核实的事实
| 电路 | Q | C | cost | × 参考 | 本次复核 |
|---|---|---|---|---|---|
| 公开 62q（67482db6） | 62 | 1624.07 | 100,692.58 | 20.625 | 新容器里从 ops.json 重建，**sha 字节一致**；**官方 verifier 全量 200,540,928 shot 重跑 PASS**，cost、Toffoli 1327.483、41 个旋转、eps 2.43e-13、worst 0.99932 都和以前一致 |
| lut_U2（main） | 109 | 1880.49 | 204,973.19 | 10.132 | 本次没重跑（之前已多次换 salt 全量 PASS） |
- 新写的 `qcheck.py`（抽样精确检查相位、末态是否干净、平均 Toffoli）在原电路上：worst 0.99932、0 bad、0 dirty、1327.50。它和 verifier 的 worst 完全一样，可以当快速筛子用。
- 硬规则：没向 Kaggle 提交；没推 main；只提交了 .py 和 README，没有第三方电路、大文件或密钥；没写比赛非公开信息。

## 3. 本次实验（62q 和 63q `9a8627` 逐个 stage 对比）
- `segtof.py` 按"每个旋转之间的静态 Toffoli 数"对齐两版。early_phase_taps 在 2^-10 和 2^-6 两段各多 1 个，尾部也多；fine_phase_stream 在第一段多（40 vs 37），2^-17 那段多 1 个。
- **尝试 1：op 15528（CCX 32 16 1）**。63q 对最后一步粗相位的门控二次式用 HMR + 条件 CZ 擦除（0 Toffoli）。我把它改成"CX 链 + HMR q1 + 条件 CZ"，用 qcheck 检查：**FAIL**，27% 的输入末态不干净。探针显示 op 15559 之后 q1 在 12.3% 的输入上不为 0，而且 op 16161 还要用它。也就是说，62q 把 q1 当作滚动寄存器一直留着，省下的那根线就是用这个 Toffoli 换来的。**这个点关闭。**
- **尝试 2：op 25874~25875**。62q 用 2 个 Toffoli 算 q50 = q23·a ⊕ q21·b，63q 只用 1 个，因为它用第 63 根线存了一个 AND。q21 和 q23 互斥但不互补（q21 约 0.3%，q23 约 20%，同时为 1 的概率是 0），不存乘积就省不掉。**除非能先腾出一根线，否则关闭。**
- 结论：在 62 宽度下，"把 63q 做法搬回来"的每一个点都要额外一根线。原先估计的"early 和 fine 各省约 4 个"在不增加宽度的前提下拿不到。

## 4. 问题和可疑点
- 依然没有干活的；用户 11-05 已收尾，这个 routine 每小时还在消耗额度（之前已两次推送提醒停掉，本次不重复推送）。
- 公开电路的局部窥孔和"63q 移植"都已经榨干，剩下的方向每个都要做结构性重综合，上限 ≤0.5%。

## 5. 下一步指示（按优先级，都还没做）
1. **coeff_lookup（177 AND）在 62 线内重综合**：用 trace 求每个 CCX 控制位关于 8 个地址比特的 ANF，再用 SAT 或启发式找 ≤172 AND、峰值 ≤62 的方案（省 5 Toffoli，约 0.3%）。先在 coeff_lookup 内部做逐个 CCX 的活跃线统计，找峰值 <62 的子区间，在这些地方采用 busyaprime 的 63q 做法。
2. **用 rank 亏损线腾出一根线**：late_curvature_norm 的秩亏损有 7~14，可以用 CNOT 释放出线。查一下这根线能不能在尝试 2 的区间（fine_phase_stream）一直保留到 63q 存 AND 的位置；能的话，就把 fine_phase_stream 的 63q 做法整体搬回来（省约 4）。需要的是"跨 stage 的线分配图"：`live_trace.py` + `windows.py` 按 op 输出空闲线。
3. **末尾两个互补条件块 46862~47211**：合并两条分支里的公共 AND 链，目标是平均 <10。
4. **把旋转放进测量条件块**（n_rot 按执行概率计费）：在 fine_phase_stream 里找"θ·q 之后对 q 做 HMR"并且能改写成"只在测量结果 m=1 时补相位"的结构。注意：m=0 分支同样需要 θ·f，所以简单改写不成立，要先在纸上证明可行再动手。
5. 已关闭：61 比特、删旋转、同角旋转对、线性 AND、AND 对（静态 + 交换性）、CSWAP 目标、op 15528 的 HMR 擦除、op 25874 的选择位合并。

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
