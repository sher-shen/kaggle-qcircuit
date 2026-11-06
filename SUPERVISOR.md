# SUPERVISOR.md — invsqrt（题1）监工报告

**时间戳**：2026-11-06 07:25 UTC（每小时一次的监工；routine 仍在触发）
**结论**：**NOT_APPROVED**（自研最好的仍是 lut_U2 10.132×，本次换新 salt 全量复核 PASS；公开 62q 电路 20.625× 本次重建 sha 一致。本次没有新的 cost 提升，但把上次的第 1、2 优先方向用分析关掉了）

## 1. 干活的状态
- 远端分支：`main`（037709c）、`claude/supervisor`、`claude/invsqrt-supervisor-work`。**仍然没有干活的分支 W**，干活的从 11-04 21:24Z 起就没再推送。用户 11-05 已经把 PR #1 合并并在 main 上收尾。
- 监工继续在 `claude/invsqrt-supervisor-work` 上接手，本次推送了 a1993c1：`xag_affine.py`、`xag_mffc.py`、`andfree_scan.py`、`../invsqrt/verify_lut_U2_sv0706.json`，并在 README 里加了一节。

## 2. 已核实的事实
| 电路 | Q | C | cost | × 参考 | 本次复核 |
|---|---|---|---|---|---|
| lut_U2（main，sha 27d75c8f） | 109 | 1880.49 | 204,973.19 | 10.132 | **本次用新 salt sv0706 重跑官方 verifier，全量 200,540,928 shot PASS**（Toffoli 1618、35 个旋转、worst 0.99075 x=816489），和之前一致 |
| 公开 62q（67482db6） | 62 | 1624.07 | 100,692.58 | 20.625 | 从 ops.json 重建，**sha 字节一致**；verifier 本次没重跑（06:45 那次已经全量 PASS） |
- 硬规则检查：没有向 Kaggle 提交；没有推 main；只提交了 .py、README 和一个几 KB 的 verifier json；没有第三方电路文件，没有密钥，也没有比赛非公开信息。

## 3. 本次实验（结论都是关闭方向）
- **指示 1、2（MC 重综合 coeff_lookup）用分析关掉**：`xag_affine.py` 和 `xag_mffc.py` 显示，177 个 AND 的 **MFFC 全部是 1**（扇出 1~137，每个 AND 都作为线性项被几十个后续 AND 用到）。cut rewriting 的收益是 |MFFC| 减去新加的 AND，所以单遍要有收益，被改写节点的函数必须落在已有节点的仿射张成里，而 `lut_xag_rank.py` 已经证明这种情况为 0。所以 mockturtle 的 cut_rewriting 加 minmc 预期收益是 0，自写的局部割重综合也一样。另外每个输出的锥都覆盖 141~177 个 AND，28 个非阶梯输出单独就要用到全部 177 个，所以把 7 个阶梯状输出（转折 3~35 个，阈值 7/35/74/128/...）拆出来用比较器做，结构上省不下任何东西。
- **指示 3（跨 stage 线分配）**：`andfree_scan.py` 在 67 个 62 宽窗口的开头和中点找满足 w = a·b ⊕ 仿射 的活线，这种线可以免费测掉、之后花 1 个 Toffoli 重算，从而腾出一根线。结果：**coeff_lookup（10,578 个 op 的窗口）和 front_decoder_compute 都是 0 个**；只有 arith_b、arith_c、fine_phase_stream 的短进位窗口里有。所以 61q 每个窗口的代价都远不止 1 个 Toffoli。另外 63q 的 2^-17 tap（63q ops 27162-27168）用的 q48 是一根**长期滚动寄存器**（之前就存着 q21·q54 ⊕ …，19% 时间非零），不是临时线；62q 在 25860-25880 一直是 62 宽，搬不过来。方向关闭。

## 4. 问题和可疑点
- 仍然没有干活的。用户 11-05 已经收尾，这个 routine 每小时还在消耗额度。自 11-05 07:50 起，连续 11 次运行都没有 cost 提升。
- 公开 62q 这一路剩下的方向都要做全局重综合，比如带宽度约束的精确 MC 搜索（SAT），或者重新设计系数表示。一小时的无人值守运行很难做完。

## 5. 下一步指示（按优先级，都还没做）
1. **coeff_lookup 的全局 MC 重综合，要带宽度约束**：这个 stage 里 8 根地址线、15 根 payload、35 根输出，同时最多 62 根，所以末尾只剩约 4 根 scratch。目标是 35 个 8 输入函数在 ≤4 根 scratch、并允许输出线原地累加的条件下，用不到 172 个 AND 实现。做法是把输出分组（比如按 xag_mffc 的锥重叠分成 5~7 组），每组用 SAT（如 CaDiCaL/kissat；如果权限不允许编译外部代码，就用 python-sat 的 wheel 或自写 DPLL）求精确的最少 AND 数，再拼起来对比 177。
2. **改变系数合同**：查表的 35 个输出看上去是随机函数。可以把 30 根进入算术的系数换成 signed-digit 或"差分 + 前一段系数"的表示，同时改下游算术，让表更平滑，次数更低、ANF 项更少。先离线算：对每种重编码，看 35 个输出模仿射的秩和 ANF 项数下降了多少，有明显下降再改电路。
3. **自研 lut_U2 一路换成公开 62q 的结构思路**：U2（109q、1618 Toffoli）比 62q（62q、1327 Toffoli）宽 47 根线，cost 的主要差距在 Q。可以从 62q 的 stage 划分（coeff_lookup → 相位 taps → 三段算术 → 归一化）出发，把 U2 的精度预算（行舍入、粗 guard）套进去，看能不能做出 ≤62q、Toffoli 更少的自研版本。
4. 已关闭的方向：之前列过的全部，加上本次的局部 MC 重综合（MFFC=1）、阶梯输出拆分、AND 可重算线腾宽（coeff_lookup 为 0）、63q 2^-17 tap 移植。

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
- 2026-11-06 04:45 UTC：依然没有干活的分支；公开 62q 重建 sha 一致，**官方 verifier 全量 PASS（20.625×）**；求出 unnormalize 解码器的真值表，秩下界证明 5 AND 已经最优；62q 和 63q 在 unnormalize 开头的移位计数编码不是仿射关系，整段搬过来不可行；旋转放进条件块在纸面上基本不可行；推送了 8a447da 到 invsqrt-supervisor-work；NOT_APPROVED。
- 2026-11-06 05:35 UTC：依然没有干活的分支；公开 62q 重建 sha 一致，**官方 verifier 全量 PASS（20.625×）**；coeff_lookup 求出真值表（35 个输出，近似随机，ANF 次数 7~8），双线性 4+4 分解要 225（比 177 差），177 个 AND 是一般的 XAG 电路，原地 span 检查 0 命中，自写的 flip-graph 无效；early_phase_taps 出口编码对不上，关闭；推送 73e28fd 到 invsqrt-supervisor-work；NOT_APPROVED。
- 2026-11-06 06:45 UTC：依然没有干活的分支；公开 62q 重建 sha 一致，**官方 verifier 全量 PASS（20.625×）**；把 coeff_lookup 导出成 XAG（177 AND，按 XAG 层面看 0 冗余），但在云端编译 mockturtle 被权限分类器拦下，指示 1 没跑成；查表单比特 slack 扫描结果是没有任何余量（早期 tap 线 ≥6.6e4×tol，其余 30 根翻转后末态不干净），方向关闭；推送 f667f7c 到 invsqrt-supervisor-work；NOT_APPROVED。
- 2026-11-06 07:25 UTC：依然没有干活的分支；U2 换 salt sv0706 全量复核 PASS（10.132×，一致）；公开 62q 重建 sha 一致；coeff_lookup 的 177 个 AND 的 MFFC 全为 1，所以 cut rewriting/局部 MC 重综合预期收益 0（关闭指示 1、2）；输出锥 141~177，阶梯输出拆分无效；AND 可重算线扫描在 coeff_lookup 为 0，63q 2^-17 tap 依赖滚动寄存器，搬不过来（关闭指示 3）；推送 a1993c1 到 invsqrt-supervisor-work；NOT_APPROVED。
