# SUPERVISOR.md — invsqrt（题1）监工报告

**时间戳**：2026-11-06 05:35 UTC（每小时一次的监工；routine 仍在触发）
**结论**：**NOT_APPROVED**（自研最好的 lut_U2 是 10.132×。公开 62q 电路 20.625×，本次又全量复核，结果是 **全量 200,540,928 shot PASS**（Toffoli 1327.483、worst 0.99932 x=161、score 100,692.58，一致）。指示 1、3 本次都做了：指示 1 已经证明手上的工具和简单思路都不能把 coeff_lookup 压到 177 以下，指示 3 已关闭。没有新的提升）

## 1. 干活的状态
- 远端分支和上次一样，只有 `main`（037709c）、`claude/supervisor` 和 `claude/invsqrt-supervisor-work`。**没有干活的分支 W**，干活的从 11-04 21:24Z 起就没再推送。
- 监工继续在 `claude/invsqrt-supervisor-work` 上接手，本次推送了 73e28fd：coeff_lookup 的分析工具 `lut_*.py`、`lut_flip.c`，另外在 README 里加了一节。

## 2. 已核实的事实
| 电路 | Q | C | cost | × 参考 | 本次复核 |
|---|---|---|---|---|---|
| 公开 62q（67482db6） | 62 | 1624.07 | 100,692.58 | 20.625 | 新容器里从 ops.json 重建，**sha 字节一致**。官方 verifier 全量重跑：**全量 200,540,928 shot PASS**（Toffoli 1327.483、worst 0.99932 x=161、score 100,692.58，一致） |
| lut_U2（main） | 109 | 1880.49 | 204,973.19 | 10.132 | 本次没重跑（之前已多次换 salt 全量 PASS） |
- 硬规则检查：没有向 Kaggle 提交；没有推 main；只提交了 .py、.c 和 README（共 152K）；没有第三方电路、大文件、密钥，也没有比赛非公开信息。

## 3. 本次实验
- **coeff_lookup（指示 1）**：算出了精确真值表。这个 stage 有 35 根输出线，每根都是 8 位地址的函数（256 个地址全部覆盖），ANF 次数是 7~8，每根 103~145 项，非仿射的 247 个单项全部出现，模仿射后秩是 35，基本就是随机函数（只有 q60、q41、q44、q43、q57、q40、q59 是阶梯状的高位）。
  - 双线性 4+4 分解：**35 种切分方式的行秩之和都是 225**，要 22+225=247 个 AND，比 177 差得多。
  - 177 个 AND 里有 170 个是两个 7~8 次函数相乘，所以这是一般的乘法复杂度（XAG）电路，不是单项式方案。
  - 精确 span 检查：没有任何一个 CCX 的乘积落在当时活着的线的仿射张成里，**0 命中**。
  - 计数下界大约 70~85 个 AND，不可构造，只说明理论上还有空间；要真正压下来得靠专门的 MC/SAT 重综合。
  - 我自己写的 GF(2) flip-graph 从平凡分解出发，连人工埋的秩 60 张量都找不回来，**这个工具无效**。
- **early_phase_taps（指示 3）**：用 `stage_match.py 15214 16657` 对比，两版在 stage 开头的 58 根活线一一对应、完全一致；但到 stage 结束（16166 vs 17429）时，62q 有 53 根活线、63q 有 54 根，q0..q3 和 q23 对不上。也就是说，多出的 4 个 Toffoli 是在出口用压缩编码省一根线的代价，和 op 15528 的结论一致。**关闭。**

## 4. 问题和可疑点
- 仍然没有干活的。用户 11-05 已经收尾，这个 routine 每小时还在消耗额度（之前已推送过两次提醒，本次不再推送）。
- 公开 62q 剩下的方向全是大规模结构性重综合，一小时一次的接手做不完。现有工具已证明拿不到便宜的收益。

## 5. 下一步指示（按优先级，都还没做）
1. **用真正的 MC 工具重综合 coeff_lookup**：把 35 个真值表（`lut_outputs.py` 的输出 F.npy）导出成 PLA，交给 mockturtle 的 XAG 优化（`xag_minmc_resynthesis` / cut rewriting）或 SAT 精确 MC，目标是 ≤171 AND，同时不超过当前的 39 根 scratch 线。可以先只对阶梯状的 7 个高位做精确 MC，看它们现在占用了多少 AND。
2. **跨 stage 线分配**：arith_a 最大占用 61，phase_merge_repair 是 60。看能不能在 fine_phase_stream 期间腾出一根线，从而整段搬 63q 版（省 4）。可以先用 `stage_match.py 25425 26758` 和 `25923 27216` 看出入口是否一致；如果出口也一致，再查 63q 那段的峰值宽度。
3. **flip-graph 改成从好的初值出发**：先从公开电路里抽出某种分解作为初值（比如把 lookup 按高 4 位分组后的 AND 结构），或者改用带启发式的 GF(2) 交替最小化，并先在埋秩张量上验证有效，再用到 T''。
4. 已关闭的方向：61 比特、删旋转、同角旋转对、线性 AND、AND 对、CSWAP 目标、op 15528、op 25874、互补块共享 AND 链、直接搬 63q stage、unnormalize 解码器（5 AND 已是下界）、旋转放进条件块、early_phase_taps 搬 63q（出口编码不同）、coeff_lookup 的双线性 4+4 分解和原地 span 替换。

## 历史
35-- 2026-11-05 01:35 UTC：没有干活的分支；复核 sv_B（1.181× PASS，一致）；监工接手，做了 LUT+二次方案 lut_C 4.417× 和 lut_D 4.763×（全量 PASS），lut_E 4.792×（全量 PASS），开了 draft PR #1；NOT_APPROVED。
36-- 2026-11-05 02:45 UTC：依然没有干活的分支；独立全量复核 lut_E（4.792×，一致）；监工继续接手，做了 signed-digit + 窗口 Horner（H 8.452×）、clamp（I 8.598×）、二分归一化（J 8.962×）、零顶移位（K **9.060×**），全部全量 PASS，推到 claude/invsqrt-supervisor-work，并更新 PR #1；NOT_APPROVED。
37-- 2026-11-05 03:35 UTC：依然没有干活的分支；换 salt 独立全量复核 K（一致）；监工继续接手，做了 droptop（L **9.158×**，113 q，全量 PASS）；maxq 限比特和 lutpoly5（M∈[1,2)）都没有变好；判断现在的架构已接近局部最优，下一步要改结构（自写加法器、高位提前打相位、c2 分组）；NOT_APPROVED。
38-- 2026-11-05 04:35 UTC：依然没有干活的分支；换 salt 独立全量复核 L（一致）；监工继续接手，做了 droprot（9.19×）和每段系数整数搜索（lut_N **9.457×**，112 q，全量 PASS）；发现 lutpoly5 的 rangeq bug（不是精度问题，放弃该方向）；fy=28 证明不可行；NOT_APPROVED。
39-- 2026-11-05 05:35 UTC：依然没有干活的分支；换 salt 独立全量复核 N（一致）；监工继续接手，做了 smallfirst（P 9.554×）和单加法器进位折叠（Q **9.755×**，112 q，全量 PASS）；算账否定了"s 高位用 AND+旋转"方向；NOT_APPROVED。
40-- 2026-11-05 06:45 UTC：依然没有干活的分支；换 salt 独立全量复核 Q（一致）；监工继续接手，做了 Horner 行舍入（carry-in）+ 粗 guard 0,-3,-5（T **9.867×**，111 q，全量 PASS）；算账否定了"a0/P 分开打相位"和"查表粗细分段"；NOT_APPROVED。
41-- 2026-11-05 07:50 UTC：依然没有干活的分支；换 salt 独立全量复核 T（一致）；监工继续接手，把行舍入推广到 fy=28（U 10.115×，110 q）并扫 maxq（U2 **10.132×**，109 q），全量 PASS；可达 x_norm 搜索无收益；判断精度方向已到头；NOT_APPROVED。
42-- 2026-11-05 21:40 UTC：依然没有干活的分支；PR #1 已被用户合并；新容器里重建 U2 字节一致，换 salt sv2105 全量复核 PASS（10.132×，一致）；k=8/10、deg3、fy29、粗 guard 扫描都没有达标的改进（0,-3,-4 省 52 Toffoli 但差 0.53 bit）；云端拿不到公开 62q 电路；推送了提醒用户停掉还在触发的监工 routine；NOT_APPROVED。
43-- 2026-11-05 22:55 UTC：依然没有干活的分支；U2 重建字节一致；**公开 62q 电路首次在云端拿到并重建（sha 67482db6 一致），官方 verifier 全量 PASS = 20.625×**；角度 LP、窥孔扫描、AND 对扫描都没有收益；从 main 重开 claude/invsqrt-supervisor-work 并开 draft PR #2（只有工具和复核）；NOT_APPROVED。
44-- 2026-11-05 23:15 UTC：依然没有干活的分支；公开 62q 在新容器重建 sha 一致；精确宽度分析显示峰值 62 覆盖 67 个窗口、绝大多数满秩，61q 没有便宜路径；线性 AND 扫描的 12 个命中替换后 verifier FAIL（结果历史采样伪影），每个 x 抽 32 shot 后 0 命中，方向关闭；NOT_APPROVED。
45-- 2026-11-06 00:25 UTC：依然没有干活的分支；公开 62q 重建 sha 一致，精确相位 trace 重跑一致；删旋转 LP（8 个候选）全部不可行；条件块只有 51.5 个 Toffoli 且局部最优；发现两组旋转有 8 对同角度，但宽度检查（峰值 62 覆盖第 1 组 84% 的 op）表明留住比特得不偿失；NOT_APPROVED。
46-- 2026-11-06 01:30 UTC：依然没有干活的分支；公开 62q 重建 sha 一致；按交换性推广的 AND 对扫描 0 对，CSWAP 目标互补扫描 0 个（47040 是采样伪影）；重读 cost 公式确认 n_rot 按执行概率计费，据此新增"旋转放进条件块"方向；推送 a7daef3 到 invsqrt-supervisor-work；NOT_APPROVED。
47-- 2026-11-06 02:40 UTC：依然没有干活的分支；公开 62q 重建 sha 一致，**官方 verifier 全量重跑 PASS（20.625×）**；对比了 62q 和 63q 两版每个 stage 的 Toffoli 数，两次移植尝试都失败（op 15528 改 HMR 后末态不干净，因为 q1 要一直留着；op 25874 的两个选择位互斥但不互补）；推送了新工具到 invsqrt-supervisor-work；NOT_APPROVED。
48-- 2026-11-06 03:50 UTC：依然没有干活的分支；公开 62q 重建 sha 一致，**官方 verifier 全量 PASS（20.625×）**；对比 62q 和 63q 每个 stage 的宽度和 Toffoli 数，发现只有 unnormalize 有空闲的线，但只差 0.6 个 Toffoli；互补块的公共 AND 链提到外面没有收益，已关闭；推送了 5c2075c 到 invsqrt-supervisor-work；NOT_APPROVED。
49-- 2026-11-06 04:45 UTC：依然没有干活的分支；公开 62q 重建 sha 一致，**官方 verifier 全量 PASS（20.625×）**；求出 unnormalize 解码器的真值表，秩下界证明 5 AND 已经最优；62q 和 63q 在 unnormalize 开头的移位计数编码不是仿射关系，整段搬过来不可行；旋转放进条件块在纸面上基本不可行；推送了 8a447da 到 invsqrt-supervisor-work；NOT_APPROVED。
- 2026-11-06 05:35 UTC：依然没有干活的分支；公开 62q 重建 sha 一致，**官方 verifier 全量 PASS（20.625×）**；coeff_lookup 求出真值表（35 个输出，近似随机，ANF 次数 7~8），双线性 4+4 分解要 225（比 177 差），177 个 AND 是一般的 XAG 电路，原地 span 检查 0 命中，自写的 flip-graph 无效；early_phase_taps 出口编码对不上，关闭；推送 73e28fd 到 invsqrt-supervisor-work；NOT_APPROVED。
