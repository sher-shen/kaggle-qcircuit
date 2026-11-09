# SUPERVISOR.md — invsqrt（题1）监工报告

**时间戳**：2026-11-09 03:05 UTC
**结论**：**NOT_APPROVED**（当前最好仍是公开 62q 加 merge2：62 q / 1325.48 Toffoli / 100,568.50 = **20.650×**。本次换 salt sv0901mm 全量 PASS，和另一次运行的 sv0902mm 结果一致。本次没有新的数值提升）

## 1. 干活的状态
- 远端分支只有 `main`、`claude/supervisor`、`claude/invsqrt-supervisor-work`。**仍然没有干活的分支 W**，也没有新的 PR；干活的最后一次推送在 11-04。监工继续在 `claude/invsqrt-supervisor-work` 上接手（draft PR #2 不变）。
- **本次（01:05 开始）和上一次 00:50 那次运行完全重叠**。两次各自独立跑了同一个非相邻对扫描，结论一样。那次运行另外做了 star 3→2 和 two-star 4→3（02:26 推送）。本次没有重复那部分，只把自己的结果作为独立复核推上去。
- 本次推送：8a0d7a4，并在对方的 925d198 上 rebase 成 f7ab07e（`verify_p62_merge2_sv0901mm.json`、`nonadj_results_rerun0901.txt`、README 新小节）。

## 2. 已核实的事实（本次在新容器里亲自重跑：python3.13 + data/kickmix/kickmix.so，4 核）
| 电路 | Q | Toffoli（每 shot 均值） | C | cost | × 参考 | 本次复核 |
|---|---|---|---|---|---|---|
| **p62 + merge2（sha fc153f1f）** | 62 | 1325.48 | 1622.07 | **100,568.50** | **20.650** | 重新 clone manwithacat/kickmix-macos，用 patch_ops.py 加 `edits/merge2.json` 重建，sha 一致；官方 verifier 全量 200,540,928 shot，**新 salt sv0901mm：PASS**（worst 0.99932，x=161，max Toffoli 1495，41 个旋转，eps 2.43e-13） |
| 公开 p62（sha 67482db6） | 62 | 1327.48 | 1624.07 | 100,692.58 | 20.625 | 本次没有重跑 |
| lut_AF（sha 1f00ebbf） | 93 | 1494.00 | 1748.80 | 162,638 | 12.769 | 本次没有重跑 |
- 倍数 = 2,076,774.23 / 100,568.50 = 20.650。score 是 verifier 输出的总 cost（Q × C），不是某个子项。
- **非相邻对（独立重跑，和另一次运行对上了）**：carry 链 35 对全部 lin-inconsistent（精确否定，k 73..157）；lookup_c / late_curvature_norm 40 对全部 minrank_block NONE(exact)（每个约 1.99 亿节点）。
- rank4_sat 在最小的链（21884，k=73）上，L=3（R=2）和 L=4（R=3）都跑了 2000 秒，都是 TIMEOUT，判不了。
- star 3→2（carry L3 196/196）和 two-star 4→3（carry L4 2526/2526）都是 NONE(exact)：这是另一次运行的结果，本次**没有重跑**。
- 读了 verifier 的 cost 公式（第 316–323 行）：所有旋转共用同一个 eps，取 `π·min_margin/2^64/n_rot`，均分。所以「按旋转分组给不同的 eps」不可能，这个方向关闭。
- 硬规则检查：没有向 Kaggle 提交；没有推 main；新增文件都是 KB 级（dump 放在 scratchpad，没有提交）；没有密钥，也没有比赛的非公开信息。

## 3. 本次做法
1. 重建 merge2，用 2 个 worker 跑 verifier 全量（新 salt），同时重跑 `nonadj_pair_scan.py p62mm.json 3000 2 60`（打开 MR_DUMP）。carry 那部分很慢（约 2 分钟一对），50 分钟的 timeout 到了还没跑完，所以按 A/B 区间分 3 片补跑（[0,∞) 截断、[23200,30000)、[30000,∞)）。lookup 那部分导出 40 个 dump，再用 minrank_block 并行跑。
2. 用 chain_dump_scan 导出 carry 链（39 个 dump），在 k=73 的两条链上跑 rank4_sat，各 2000 秒。
3. 坑：我第一版 blkrun 用 `pgrep -fc minrank_block` 限制并发，连 timeout 外壳和 C 程序一起数，所以实际只跑 1 路，后来改成只数 python 进程。

## 4. 问题和可疑点
- 依然没有干活的推送，监工是唯一在推进的，而且已经连续多次没有数值提升。每省 1 个 Toffoli 只多 +0.016×。
- **监工 routine 一次运行要 1.5~2 小时，但每小时触发一次，已经连续 3 次重叠**，大量算力花在重复的扫描上（本次的非相邻对就是重复的）。**强烈建议用户把间隔调到 3 小时以上，或者直接停掉。**
- 链级 3→2 的一般情形（秩 ≤ 4）仍然没有判定，lookup 链上的 star 子情形也还没有做。

## 5. 下一步指示（按优先级，均未做）
1. **lookup 链上的 star 3→2 和 two-star 4→3**：star_scan.py 已经在 carry 链上验证过（<1 秒一个）。lookup 链 k≈350，块是 36 根线，每个 star 删掉一个顶点以后还是秩 2 的块搜索，每个约 3 分钟。L3 链大约 36 个顶点 × 条数，先跑 L3，有命中再用 phase_trace 和 verifier 验证。
2. **14 对相位 tap 用块方法精确判一遍**（k 248..711）：先看被碰到的块大小，块 ≤ 64 就直接跑 minrank_block，把「tap-wire 论证」换成精确证明。
3. **链级 3→2 的一般情形改用「固定一组 (u1,w1) 在小子空间里枚举」**：u1 取 span(4 个控制值 + 1)（16 种），w1 任意；对每个 u1，问题变成「Q0 + u1^w1 + K l 的秩 ≤ 2」，w1 的系数是线性的，可以合进 l，再跑一次秩 2 的块搜索。每条链 16 次，每次约 3 分钟。这比 star 更一般（star 是 u1 取单根线）。
4. 已关闭、不要再试：前面列过的全部方向，再加上非相邻对（两次独立运行，75/75），rank4_sat 在 k=73 上（L3、L4 都 2000 秒超时），以及按旋转分组给不同 eps（verifier 是均分的）。

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
- 2026-11-06 21:25 UTC：依然没有干活的分支；U2 换 salt sv0806 全量复核 PASS（10.132×，一致）；coeff_lookup 里找到两条计数器链（11 个输出是平滑多项式系数的低位，B 是 round(三次)），其余 24 个输出不能用便宜的仿射重编码变平滑，指示 2 关闭；确认 python-sat wheel 可以下载；推送 8361420 到 invsqrt-supervisor-work；NOT_APPROVED。
- 2026-11-06 22:25 UTC：依然没有干活的分支；U2 在新容器里重建字节一致，换 salt sv0611 全量复核 PASS（10.132×，一致）；按最高位拆表：247 个单项式全部用到，155 只在加 35 根 scratch 时才行，宽度内要 ≥247，关闭；SAT 精确 MC 连 7 AND 的单输出都在 200 秒内解不出，关闭；maxq 108/104 没有变好；推送 d6a99e1 到 invsqrt-supervisor-work；NOT_APPROVED。
- 2026-11-06 23:20 UTC：依然没有干活的分支；U2 新容器重建字节一致，换 salt sv0711 全量复核 PASS（10.132×，一致）；做了 U2 每个 stage 的 qubit 账本（峰值 109 只在 horner，denorm/phase 是 99）；pad 扫描 0/3/5 加 maxq 都没有变好；推送 3da3570 到 invsqrt-supervisor-work；NOT_APPROVED。
- 2026-11-07 00:45 UTC：依然没有干活的分支；U2 新容器重建字节一致，换 salt sv0700 全量复核 PASS（10.132×，一致）；新方向"非均匀分段"（lutpoly10）把 lookup 从 383 降到 255，但 horner 每个方向多 71、多 6 q、误差 2^-23.78，217.8k 比 205.0k 差，关闭；推送 db4a900 到 invsqrt-supervisor-work；NOT_APPROVED。
- 2026-11-07 01:45 UTC：依然没有干活的分支；U2 新容器重建字节一致，换 salt sv0107 全量 PASS；**监工新做 lut_V（自写 Gidney 加法器，去掉 pad 和 l）：101 q / 1528 Toffoli / 180,839 = 11.484×，官方 verifier 全量 PASS**，推送到 invsqrt-supervisor-work；gadd 下的参数扫描和 k=8 都没有超过 V；NOT_APPROVED。
- 2026-11-07 02:35 UTC：依然没有干活的分支；V 新容器重建字节一致，换 salt sv0207 全量 PASS（11.484×，一致）；监工接手，试了列丢弃 Horner（lutpoly12）、deg3 k=7（修好 IndexError）、k=8 gadd、V+droprot1/2，全部没有超过 V 或者 FAIL，已关闭；推送 054ece1 到 invsqrt-supervisor-work；NOT_APPROVED。
- 2026-11-07 03:45 UTC：依然没有干活的分支；V 重建字节一致，salt sv0307 全量 PASS；监工接手，做了 top-CCX 加法器（W 11.599×）、两级 Horner 窗口（X 11.834×）、Gidney/Cuccaro 混合加法器（**Y 96 q / 1528 / 171,886.84 = 12.082×**），全部全量 PASS；推送 d86873a 到 invsqrt-supervisor-work，并更新了 PR #2；NOT_APPROVED。
- 2026-11-07 04:30 UTC：依然没有干活的分支；Y 新容器重建字节一致，换 salt sv0507 全量 PASS（12.082×）；监工接手，新做按 s 加权的系数搜索（lutpoly16）：**lut_Z 96 q / 1528 / 171,130.46 = 12.135×，官方 verifier 全量 PASS，换 salt sv0507z 也 PASS**；粗 guard、droprot、k=8 在新目标下也都关闭；推送 c57a1c8、291c039 到 invsqrt-supervisor-work，并更新 PR #2；NOT_APPROVED。
- 2026-11-07 05:40 UTC：依然没有干活的分支；Z 新容器重建字节一致，换 salt sv0705z 全量 PASS（12.135×）；监工接手，试了 fan-out-free fold（lutpoly17，最好 96/1534，不如 Z）和 b2 丢弃重载（159 叶，186.8k，比 Z 差），两个都关闭；k=8 在 fold2 下也关闭（最好 101 q / 1706）；推送 8a9bd0a、c0cc8bd 到 invsqrt-supervisor-work；NOT_APPROVED。
- 2026-11-07 06:45 UTC：依然没有干活的分支；Z 新容器重建字节一致，换 salt sv0607z 全量 PASS（12.135×）；**监工新做 lut_AA（每个 Horner 窗口 1 个 carry，偏移从表里加载）：93 q / 1522 / 165,224.63 = 12.569×，默认 salt 和 sv0607aa 都全量 PASS**；maxanc 和 groups 的扫描都没有超过 AA；推送 235b48f、aca2d91 到 invsqrt-supervisor-work；NOT_APPROVED。
- 2026-11-07 07:45 UTC：依然没有干活的分支；AA 新容器重建字节一致，换 salt sv0707aa 全量 PASS（12.569×，一致）；监工接手，试了"fold 之后用 CX 释放窗口符号比特"（lutpoly19/20、fcrepair：地址仿射、加 1 个 AND、按奇偶重选系数、加载数据特征、窗口加宽），全部不可行，已关闭；b2 小表重载算账打平；推送 e2e5928 到 invsqrt-supervisor-work；NOT_APPROVED。
- 2026-11-07 21:35 UTC：依然没有干活的分支；AA 新容器重建字节一致，换 salt sv0721aa 全量 PASS（12.569×）；监工接手，新做 lut_AB（y LSB 不进 denorm lane，93 q / 1514 = 12.625×，默认 salt 和 sv0721ab 都全量 PASS）和 **lut_AC（加 --jmin8 1，93 q / 1512 / 164,312.06 = 12.639×，默认 salt 和 sv0721ac 都全量 PASS）**；部分移位和 onecarry 下的 k=8 都关闭；推送 fa312eb、9696d32，更新 PR #2；NOT_APPROVED。
- 2026-11-07 22:35 UTC：依然没有干活的分支；AC 重建字节一致，换 salt sv0722ac 全量 PASS（12.639×）；监工接手，新做 **lut_AD（用一条前缀 AND 链求 s：93 q / 1502 / 163,382.06 = 12.711×，默认 salt 和 sv0722ad 都全量 PASS）**；hi 重载方向（单调阶梯，128 个值）关闭；推送 1d9754f，更新 PR #2；NOT_APPROVED。
- 2026-11-07 23:25 UTC：依然没有干活的分支；AD 新容器重建字节一致，换 salt sv0723ad 全量 PASS（12.711×）；监工接手，完成指示 2：**lut_AE（normalize_inv 用 X 测量擦除 s，加条件相位修正：93 q / 均值 1498.125 / 163,021.69 = 12.739×，默认 salt 和 sv0723ae 都全量 PASS）**；s 封顶到 7 算账打平，没有搭；推送 15b47c9，更新 PR #2；NOT_APPROVED。
- 2026-11-08 00:25 UTC：依然没有干活的分支；AE 新容器重建字节一致，换 salt sv0800ae 全量 PASS（12.739×，一致）；监工接手，step-2 窗口分组实测 6 组都没有收益（最好 94 q / 1499），关闭；x<64 旁路纸面算账为负（+128 −72，+3 q），关闭；完成指示 5：**lut_AF（每个 stage un-shift 后立刻测 s_r：93 q / 均值 1494.0 / 162,638.03 = 12.769×，默认 salt 和 sv0800af 都全量 PASS）**；推送 0dce127，更新 PR #2；NOT_APPROVED。
- 2026-11-08 01:40 UTC：依然没有干活的分支；AF 新容器重建字节一致，换 salt sv0801af 全量 PASS（12.769×，一致）；监工接手，maxanc 11/12 实测更差，相位梯度方案和 c0 单独打相位在纸面上都是负收益，全部关闭；推送 9aa7fb8 到 invsqrt-supervisor-work；建议换赛道到公开 62q 做增量；NOT_APPROVED。
- 2026-11-08 02:40 UTC：依然没有干活的分支；AF 新容器重建字节一致，换 salt sv0802af 全量 PASS（162,638.09 = 12.769×，一致）；监工接手，horner 活跃比特剖面显示峰值 93 只出现在 step-1 B 行加法器；step-1 嵌套窗口和 SELECT-SWAP 查表在纸面上都不划算，关闭；推送 8d00eb8 到 invsqrt-supervisor-work；NOT_APPROVED。
- 2026-11-08 03:15 UTC：依然没有干活的分支；AF 新容器重建字节一致，换 salt sv0803af 全量 PASS（162,638.10 = 12.769×，一致）；监工接手，把 62q 的 unnormalize 导出来看，发现它已经在逐个测量移位 flag 并带条件修正，指示 1 没有可移植的东西，关闭；查表子树异或共享实测 h≥2 的节点 0 命中，指示 3 关闭；b2 测量释放后重载纸面算账为负，关闭；推送 0a8dd74 到 invsqrt-supervisor-work；NOT_APPROVED。
- 2026-11-08 04:55 UTC：依然没有干活的分支；AF 新容器重建字节一致，换 salt sv0804af 全量 PASS（12.769×）；coeff_lookup 窗口重综合有证明地关闭；新写的 stage 级形式窗口扫描在 arith_a 和 fine_phase_stream 各找到一对可以合并的 Toffoli，**公开 62q 加 merge2 = 62 q / 1325.48 / 100,568.56 = 20.650×，默认 salt 和 sv0804mm 都全量 PASS，首次超过公开最高 20.625×**；dirty 链用 CX 腾线已关闭；推送 9d9e258 并更新 PR #2；NOT_APPROVED。
- 2026-11-08 05:25 UTC：依然没有干活的分支；merge2 在新容器重建 sha 一致，**换 salt sv0805mm 全量 PASS（100,568.54 = 20.650×）**；跨度 40 扫描在剩下的 stage 全部跑完（只有假命中）；新做差一个 AND扫描（stage_qform_plus.py）和采样版成对扫描（func_pair_scan.py），只找回 merge2 的 2 对；tap 流命中受宽度限制，关闭；推送 a51d6e3 到 invsqrt-supervisor-work；NOT_APPROVED。
- 2026-11-08 06:50 UTC：依然没有干活的分支；merge2 新容器重建 sha 一致，**换 salt sv0806mm 全量 PASS（100,568.51 = 20.650×）**；把上次的指示 1~3 全部做完：二次关系确实存在（每对 15~711 个），一般仿射因子成对扫描在 72 对上 0 命中（自检能找回 merge2），三元组 3 换 2 在 39 个上 0 命中（合成自检通过），tap 对 128 对 0 命中，dirty 链腾线 0 根，四个方向都关闭；推送 06e38c9 到 invsqrt-supervisor-work；NOT_APPROVED。
- 2026-11-08 07:50 UTC：依然没有干活的分支；merge2 新容器重建 sha 一致，**换 salt sv0807mm 全量 PASS（100,568.57 = 20.650×）**；完成指示 1：新写 support_g_scan.py（支撑集定向的 g，自检能找回 merge2），L=400 和 L=60 都是 71 对 0 命中（穷举 22 对 / 18 对，其余抽样）；指示 2、3 论证后发现被 linear_and_scan 覆盖，关闭；近似剪枝因为余量 2^25.8 小于最小旋转 2^28，关闭；推送 77a7c7a、9f4493b 到 invsqrt-supervisor-work；NOT_APPROVED。
- 2026-11-08 21:40 UTC：依然没有干活的分支；merge2 新容器重建 sha 一致，**换 salt sv0821mm 全量 PASS（100,568.55 = 20.650×）**；指示 1 试了线性松弛 f∈V+G∘V（lin_filter_scan.py），因为控制值都还活着，必然满足，69/71 没被否定，方向无效；推送 7efcac7 到 invsqrt-supervisor-work；建议考虑换题；NOT_APPROVED。
- 2026-11-08 22:40 UTC：依然没有干活的分支；merge2 新容器重建 sha 一致，**换 salt sv0822mm 全量 PASS（100,568.51 = 20.650×）**；完成上次的指示 1：写了精确的 MinRank 成对检验（minrank_core.py，Pfaffian 线性化），25 对进位链被精确否定（对任意 g、h），2 对 dirty 不是二次，30 对 k 约 350 的还没判定；推送 4fd014f 到 invsqrt-supervisor-work；NOT_APPROVED。
- 2026-11-09 00:15 UTC：依然没有干活的分支；merge2 新容器重建 sha 一致，**换 salt sv0823mm 全量 PASS（100,568.57 = 20.650×）**；完成上次的指示 1：发现 30 对只碰到 36 根线组成的块，写了精确的分支剪枝搜索（minrank_block.c，4/4 埋解自检通过），**30 对全部精确否定**，这样 merge2 上的成对合并全部关闭；SAT 只能找解，证不了 UNSAT；推送到 invsqrt-supervisor-work；NOT_APPROVED。
- 2026-11-09 01:35 UTC：依然没有干活的分支；merge2 新容器重建 sha 一致，**换 salt sv0900mm 全量 PASS（100,568.52 = 20.650×）**；和 00:10 那次运行重叠，丢掉了重复的 SAT 部分；链级 3→2：SAT（2400 秒超时）和块外秩下界都判不了，秩 4 的块搜索约 2^48 节点，不可行；改测可判定的子情形「非相邻对」：lookup 40 对 NONE(exact)，carry 35 对精确否定；推送 6120733、b8016ab、c18443f；NOT_APPROVED。
- 2026-11-09 03:05 UTC：依然没有干活的分支；和 00:50 那次运行完全重叠；merge2 新容器重建 sha 一致，**换 salt sv0901mm 全量 PASS（100,568.50 = 20.650×）**；非相邻对独立重跑，35 + 40 对全部精确否定，和对方一致；rank4_sat 在 k=73 上 L3、L4 都 2000 秒超时；verifier 的 eps 是均分的，分组 eps 方向关闭；推送 f7ab07e；NOT_APPROVED。
