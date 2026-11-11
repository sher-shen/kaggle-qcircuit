# SUPERVISOR.md — invsqrt（题1）监工报告

**时间戳**：2026-11-11 04:05 UTC（本次运行 02:06 开始）
**结论**：**NOT_APPROVED**（当前最好的仍是公开 62q 电路加 merge2：62 q / 1325.48 Toffoli / 100,568.52 = **20.650×**，本次没有数值提升）

## 1. 干活的状态
- 远端分支只有 `main`、`claude/supervisor`、`claude/invsqrt-supervisor-work`。**仍然没有干活的分支 W**；干活的会话 11-04 之后没有推送过，视为已停。监工继续在 `claude/invsqrt-supervisor-work` 上接手（draft PR #2）。本次推送 3520b46、f84efa9。**本次和另一次监工运行重叠**：它在 03:20 往工作分支推了 a94a853（dc3：5 线 dirty-CCCX 4→3 在 D 上 NONE，salt sv1103mm PASS），我推送时 rebase 了一次，README 冲突已合并，两边结果都保留。

## 2. 已核实的事实（本次在新容器里亲自重跑：python3.13 + data/kickmix/kickmix.so，4 核）
| 电路 | Q | Toffoli（每 shot 均值） | C | cost | × 参考 | 本次复核 |
|---|---|---|---|---|---|---|
| **p62 + merge2（sha fc153f1f）** | 62 | 1325.48 | 1622.07 | **100,568.52** | **20.650** | 重新 clone manwithacat/kickmix-macos，用 ops.json 加 `edits/merge2.json` 重建，sha 一致；**官方 verifier 全量 200,540,928 shot，新 salt sv1102mm：PASS**，worst 0.99932（x=161），41 个旋转，见 `verify_p62_merge2_sv1102mm.json` |
- 倍数 = 2,076,774.23 / 100,568.52 = 20.650，用的是 verifier 输出的总 cost（Q × C），不是子项。
- 硬规则检查：没有向 Kaggle 提交；没有推 main；本次新增文件都 < 10 KB；没有密钥，也没有比赛非公开信息。

## 3. 本次做法（上次的指示 1 和 3）
- **指示 1 完成**：m = 20 时剪枝后还剩约 160 万（块 33380 是 6000 万）个 H，block_cells2.py 的 Python 逐格检验太慢，于是新写 `cells2b.c` + `block_cells2b.py`，把逐格仿射检验（每格对 (1, y, f) 做增量 GF(2) 消元）放进 C。自检（块 21952 的 D，m 19）：埋 L+ab+cd → HIT，埋 L+a(b+cd) → HIT，三个乘积 → NONE；块 21952 本身用旧脚本重跑 → NONE，和上次一致。
- **结果：4 个 20 线内积变体（21942..22027、22775..22865、22784..22866、33380..33466）3 → 2 全部 NONE(exact)**（`block_cells2b_n20_result.txt`，每个约 13 分钟；m = 20 埋 L+ab+cd 自检 → HIT）。7 个三 Toffoli 秩 1 的块现在全部关闭。
- **指示 3 用论证关闭**：借一根和块输入无关的脏线 e，把 e 置 0 就是一根干净 ancilla，而 cells 检验本来就允许任意宽度，所以 D × {0,1} 不会带来新解。借和输入相关的线就是更大的块，20 线变体正好是这种情况，已经 NONE。
- block_reach 这次用的是 stride 1（全部 x），seed 7。

## 4. 问题和可疑点
- 已经连续四十多次运行没有数值提升。≤20 线的块层面：只剩 8 个 dirty-CCCX 嵌套块（25601..、28840..）还没关，其余全部精确关闭。每处命中最多只省 1 个 Toffoli（约 +0.016×）。
- 可靠性说明：D 是采样到的可达集合，是真实 D 的子集，所以 NONE 在真实 D 上也成立；必要条件推导里假设门是 AND/Toffoli（CCZ 只改相位，对比特翻转残差没用）。
- **再次强烈建议用户停掉这个 routine，或者改成每天一次，或者把额度转到别的题（dqi / dfthcsos）。** invsqrt 的局部优化已经基本穷尽。

## 5. 下一步指示（按优先级，都还没做）
1. **dirty-CCCX 家族剩下的 6 个块（块 25601.., 28840..）**：n=5 那两个已被重叠运行的 dc3 关闭（不带 ancilla）。下一步是 n=7 tof 6 秩 3（块 25605..25618 / 28844..28857，|D|=91）的 6→5：dc3 直接枚举 5 个门不可行，改成剥离：先用秩条件枚举前 2~3 个门，剩下的用 K=1/K=2 残差判据；再做 n=9、n=11。
2. **跨条件上下文的块 / 更大的块（NMAX 24~26）**：block_extract2 现在不跨 PUSH_CONDITION 边界；放开这一条，看有没有新的 rank < t 块。
2b. 另一次运行的 dc3 已关闭 5 线 dirty-CCCX 4→3，但它的模型是「n 线上 A·g3·g2·g1，不带 ancilla」；带 1 根干净 ancilla 的版本还没做，可以作为 1 的一部分。
3. **相位侧**：把 CCZ（只改相位）放进块模型，检查测量擦除后的相位修正块（phase_merge_repair、unnormalize）能不能少一个 CCZ，用 phase polynomial 的 T 秩/CCZ 秩下界。
4. **换赛道评估**：每处命中只省约 0.016×。建议停止 invsqrt 微优化，把额度转到 dqi。
5. 已经关闭、不要再试：前面列过的全部方向，再加上本次的 4 个 20 线内积块 3→2，以及借用无关脏线。

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
- 2026-11-09 03:10 UTC：依然没有干活的分支；又和另一次运行重叠（推送时 rebase 了一次）；merge2 新容器重建 sha 一致，**换 salt sv0902mm 全量 PASS（100,568.59 = 20.650×）**；新做 star 3→2 和两颗星 4→3（删掉中心顶点后跑精确的秩 2 块搜索，埋解自检通过）：carry L3 196/196、carry L4 2526/2526 全部 NONE(exact)，lookup 33038 链 9/35 个顶点 NONE(exact)，其余没跑完；推送 c658887、925d198、2e53db5；NOT_APPROVED。
- 2026-11-09 04:35 UTC：依然没有干活的分支；本次没有重叠运行；merge2 新容器重建 sha 一致，**换 salt sv0904mm 全量 PASS（100,568.53 = 20.650×）**；lookup 33038 链 star 剩下的 27 个顶点跑完（36/36 NONE(exact)），33195 链 8/36；新写 star_basis.py（中心取基线的 XOR 组合，埋解自检 3/3），carry L3 上控制值组合 77/77、权重 2 组合 2961/2961 全部 NONE(exact)；推送 70012e8、12e740a、c8ae946；NOT_APPROVED。
- 2026-11-09 05:05 UTC：依然没有干活的分支；又和另一次运行重叠（发现后改跑别的链）；merge2 新容器重建 sha 一致，**salt sv0904mm 全量 PASS，score 100,568.5291，和对方用同一个 salt 的结果逐位相同（20.650×）**；minrank_block.c 提速约 1.4 倍（节点数逐位相同，埋解自检 2/2 HIT）；lookup 34604 链 star 21/36 NONE(exact)，其余还在跑；推送 b10278a；NOT_APPROVED。
- 2026-11-09 05:45 UTC：依然没有干活的分支；又和 04:06 那次运行重叠（rebase 了一次，重叠的 5 个顶点节点数逐位相同）；merge2 新容器重建 sha 一致，**换 salt sv0905mm 全量 PASS（100,568.54 = 20.650×）**；34192 埋解自检 HIT；**lookup 34604 链 star 36/36、34192 链 35/35、33888 链 36/36 NONE(exact)**；推送 e40abc0、4cc1008；建议停掉 routine 或把间隔调长；NOT_APPROVED。
- 2026-11-09 07:00 UTC：依然没有干活的分支；和 05:10 那次运行重叠，按它的指示改跑 33195，没有重复；merge2 新容器重建 sha 一致，**换 salt sv0906mm 全量 PASS（100,568.53 = 20.650×）**；**lookup 33195 链 star 36/36 NONE(exact)**（5 条 lookup 链已关闭）；33329 链 4/36；推送 5401e77、edad8b2；建议停掉 routine；NOT_APPROVED。
- 2026-11-09 08:10 UTC：依然没有干活的分支；本次没有重叠运行；merge2 新容器重建 sha 一致，**换 salt sv0907mm 全量 PASS（100,568.53 = 20.650×）**；**lookup 33329 链 star 36/36 NONE(exact)**（6 条 lookup 链已关闭，剩 33481、33623、33763）；推送 583ea40、f31e102；建议停掉 routine；NOT_APPROVED。
- 2026-11-09 22:55 UTC：依然没有干活的分支（距上次运行 08:10 隔了约 14 小时）；merge2 新容器重建 sha 一致，**换 salt sv0922mm 全量 PASS（100,568.54 = 20.650×）**；33481 埋解自检 HIT；lookup 33481 链 star 15/36、33763 链 4/36，全部 NONE(exact)；推送 c488af2、acee778；建议停掉 routine；NOT_APPROVED。
- 2026-11-09 23:55 UTC：依然没有干活的分支；本次没有重叠运行；merge2 新容器重建 sha 一致，**换 salt sv0923mm 全量 PASS（100,568.55 = 20.650×）**；**lookup 33481 链 star 36/36 NONE(exact)**（7 条 lookup 链已关闭，剩 33623、33763）；33763 链 9/36；推送 69d4397、d86eea0、9955ab3、a45ffb1；建议停掉 routine；NOT_APPROVED。
- 2026-11-10 02:40 UTC：依然没有干活的分支；01:07 起和另一次运行重叠，按链分工没有重复；中途容器重启过一次，结果没有丢；merge2 新容器重建 sha 一致，**换 salt sv1000mm 全量 PASS（100,568.57 = 20.650×）**；**lookup 33763、33623 链 star 36/36 NONE(exact)，9 条 lookup 链的单中心 star 全部关闭**；33038、33623、33763 上的 ctrl2 33/33 NONE(exact)（和对方重叠的 6 个节点数逐位相同）；推送 30fe56f、f68bf7a、1141962、82a0a87；建议停掉 routine；NOT_APPROVED。
- 2026-11-10 03:00 UTC：依然没有干活的分支；和 00:06、02:0x 两次运行重叠，按链分工；merge2 新容器重建 sha 一致，**换 salt sv1001mm 全量 PASS（100,568.55 = 20.650×）**；star_basis 埋解自检 HIT；**lookup ctrl2 在 34192、34604、33888 上 33/33 NONE(exact)**（关闭），33195 8/11、33329 6/11、33481 3/11 也全是 NONE(exact)，33038 上和另一次运行重叠的 8 个组合节点数逐位相同；推送 bfdc6be、24084c3、6d672dd；建议停掉 routine；NOT_APPROVED。
- 2026-11-10 03:20 UTC：依然没有干活的分支；和 01:07 那次运行（以及另一次推送 sv1003mm 的运行）重叠，33195、33329 反序跑来避免重复；merge2 新容器重建 sha 一致，**换 salt sv1002mm 全量 PASS（100,568.55 = 20.650×）**；本次 ctrl2 22/22 NONE(exact)，**9 条 lookup 链的 ctrl2 全部关闭**；深度剖面显示块搜索的成本全在前 14 层几乎没有方程的前缀上；推送 bedbbc5、828818c；建议停掉 routine；NOT_APPROVED。
- 2026-11-10 03:50 UTC：依然没有干活的分支；和 02:06 那次运行重叠；merge2 新容器重建 sha 一致，**换 salt sv1003mm 全量 PASS（100,568.56 = 20.650×）**；star_basis 埋解自检 HIT；ctrl2 剩下的 16 个组合 NONE(exact)，和对方逐位相同（**9 条 lookup 链的 ctrl2 全部关闭**）；推送 9956d7a、0e932fd、6564fa9；建议停掉 routine；NOT_APPROVED。
- 2026-11-10 04:40 UTC：依然没有干活的分支；本次没有重叠运行；merge2 新容器重建 sha 一致，**换 salt sv1004mm 全量 PASS（100,568.54 = 20.650×）**；完成指示 3：新写 minrank_block_big.py（无 s≤64 限制，和 C 版节点数逐位相同，埋解自检 HIT），**14 对相位 tap 全部 NONE(exact)**，merge2 的同目标 CCX 对全部精确关闭；顶点重排序实验（三种顺序都约 2e8 节点）说明按顶点分支有 4^11 平台；推送 2aa4247；建议停掉 routine；NOT_APPROVED。
- 2026-11-10 05:30 UTC：依然没有干活的分支；本次没有重叠运行；merge2 新容器重建 sha 一致，**换 salt sv1005mm 全量 PASS（100,568.53 = 20.650×）**；完成指示 3：新写 boundary_qform_core.py，16 个 stage 边界的跨边界窗口 K=3 只有 dirty-CCCX 伪影，K=4 为 0，关闭；T 门相对相位 Toffoli 因为门集里没有 H 而关闭；间隔 >60 的同目标对 215 对采样扫描 0 命中（自检能找回 merge2），关闭；建议停掉 routine；NOT_APPROVED。
- 2026-11-10 07:00 UTC：依然没有干活的分支；本次没有重叠运行；merge2 新容器重建 sha 一致，**换 salt sv1006mm 全量 PASS（100,568.59 = 20.650×）**；指示 3 关闭（目标 q25 后面被当作数据用）；新写 cccx_enum：dirty-CCCX 块在 5 线下用 3 个 Toffoli 做不到（精确 NONE，自检 5/5），6 线（多借一根 dirty 线）也是精确 NONE；推送 7140454、50c068e、b914d40 到 invsqrt-supervisor-work；建议停掉 routine；NOT_APPROVED。
- 2026-11-10 07:50 UTC：依然没有干活的分支；本次没有重叠运行；merge2 新容器重建 sha 一致，**换 salt sv1007mm 全量 PASS（100,568.56 = 20.650×）**；完成指示 1：新写 block_extract/block_enum/block_reach/block_dc，≤6 线 397 个块全定义域精确 NONE（自检 HIT），用全量可达入口集做无关项，≤6 线和 7 线（K≤1）一共 860 个块 0 命中；推送 97fa843、cbbc609 到 invsqrt-supervisor-work；建议停掉 routine；NOT_APPROVED。
- 2026-11-10 22:00 UTC：依然没有干活的分支；本次没有重叠运行；merge2 新容器重建 sha 一致，**换 salt sv1021mm 全量 PASS（100,568.55 = 20.650×）**；指示 1 关闭（93 个 R 都作用在 0 线上，没有出口无关项）；新写 block_dc_res（余项松弛，埋解自检 6/6），7 线 135/135、8 线 111/111 的 K2（3→2）在可达 D 上 NONE；block_k1_big：8~12 线 1093 个块 K1 NONE；推送 c1bec0a；建议停掉 routine；NOT_APPROVED。
- 2026-11-10 22:55 UTC：依然没有干活的分支；本次没有重叠运行；merge2 新容器重建 sha 一致，**换 salt sv1022mm 全量 PASS（100,568.52 = 20.650×）**；新写 block_rank（余项秩 ≤ K，任意 n）、block_rank_prod、block_peel（精确剥离，埋解和 5 个真实块自检通过）：≤16 线 1582 个块只剩 8 个秩亏 dirty-CCCX 块没关；块 260 的 5→4 在全定义域和可达 D 上都 NONE(exact)；推送 4dd7b76、eac023c、97ecdd8 到 invsqrt-supervisor-work；建议停掉 routine；NOT_APPROVED。
- 2026-11-10 23:58 UTC：依然没有干活的分支；本次没有重叠运行；merge2 新容器重建 sha 一致，**换 salt sv1023mm 全量 PASS（100,568.52 = 20.650×）**；新写 block_extract2（非贪心、NMAX 20，4257 个块）、block_k1_anf、k1_split.c/block_dset_k1：121 个秩 1 块的 K=1 在全定义域和可达 D 上都 NONE；秩 t−1 块在 D 上只剩新块 15417..15451（5→4，peel 超时没关）；推送 14b35d9 到 invsqrt-supervisor-work；建议停掉 routine；NOT_APPROVED。
- 2026-11-11 00:30 UTC：依然没有干活的分支；本次没有重叠运行；merge2 新容器重建 sha 一致，**换 salt sv1100mm 全量 PASS（100,568.59 = 20.650×）**；新写 block_peel2 + ab_enum.c（目标 w 用线性方程求解，加上跑出仿射包的情况；删一个 Toffoli 的自检 HIT），**块 15417..15451 5→4 NONE(exact)**，179 个 OPEN 块里 164 个 NONE(exact)，15 个 slack，0 个 HIT；推送 a0f495e
- 2026-11-11 02:00 UTC：依然没有干活的分支；本次没有重叠运行；merge2 新容器重建 sha 一致，**换 salt sv1101mm 全量 PASS（100,568.50 = 20.650×）**；新写 block_cells2 + cells2.c（两 AND 的必要条件：f 在余维 2 子空间的每个陪集上仿射；埋解自检 HIT/NONE 正确），**3 个内积块（19 线）3→2 NONE(exact)**；推送 fe11577；建议停掉 routine；NOT_APPROVED。
- 2026-11-11 04:05 UTC：依然没有干活的分支；本次没有重叠运行；merge2 新容器重建 sha 一致，**换 salt sv1102mm 全量 PASS（100,568.52 = 20.650×）**；新写 cells2b.c + block_cells2b.py（逐格检验放进 C，埋解自检正确，m 20 埋 L+ab+cd → HIT），**4 个 20 线内积变体 3→2 全部 NONE(exact)**，7 个秩 1 三 Toffoli 块全部关闭；和 03:xx 那次运行重叠（它做了 dc3，rebase 合并）；借无关脏线的方向用论证关闭；没有数值提升；建议停掉 routine 或转题；NOT_APPROVED。
