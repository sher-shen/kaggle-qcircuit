# SUPERVISOR.md — invsqrt（题1）监工报告

**时间戳**：2026-11-08 02:40 UTC
**结论**：**NOT_APPROVED**（最好的仍是 lut_AF：93 q，12.769×；公开 62q 是 20.625×，差距主要在 Q）

## 1. 干活的状态
- 远端分支只有 `main`、`claude/supervisor`、`claude/invsqrt-supervisor-work`，**仍然没有干活的分支 W**（main 停在 037709c，干活的最后推送是 11-04）。
- 监工继续在 `claude/invsqrt-supervisor-work` 上接手（draft PR #2），本次推送 8d00eb8。
- 上次的指示 1–3 都没做（本次的额度用在复核和指示 4 的可行性分析上）；指示 4 已经在纸面上关闭（见第 3 节）。

## 2. 已核实的事实（本次在新容器里亲自重跑：python3.13 + data/kickmix/kickmix.so，4 核）
| 电路 | Q | Toffoli（每 shot 均值） | 旋转 | C | cost | × 参考 | 本次复核 |
|---|---|---|---|---|---|---|---|
| **lut_AF（sha 1f00ebbf）** | 93 | 1494.000 | 34 | 1748.80 | **162,638.09** | **12.769** | 按 README 命令重建（51 秒），字节一致；换 salt sv0802af 跑官方 verifier，全量 200,540,928 shot **PASS**（worst 0.99075） |
- 倍数 = 2,076,774.23 / score，score = Q × C，取自 verifier 输出的总 cost，不是只算了某个子项。
- 每个阶段的 Toffoli（本次实测）：normalize 77 / lookup 383 / horner 349 / denorm 113 / denorm_inv 113 / horner_inv 349 / lookup_inv 41（已经是测量擦除）/ normalize_inv 80（静态）。
- 硬规则检查：没有向 Kaggle 提交；没有推 main；新增文件只有一个 verify json（约 1 KB）和 README 段落；没有密钥，也没有比赛非公开信息。

## 3. 本次做法（全部关闭）
- **horner 的活跃比特剖面**：峰值 93 只出现在 step 1 的 12 个 B 行加法器里，即底子 80（x 22 + s 4 + regs 27/17/7 + 3 个窗口 carry）加上 13 个加法器 ancilla（maxanc 13）。step 1 的 A 行和 step 2 都 ≤ 90。
- **step 1 两级窗口（老指示 4）**：新加的嵌套 carry 是常驻的，会让 B 行峰值 +1；要保持 93 就得把 maxanc 降到 12，静态 Toffoli +26。嵌套窗口本身每个方向只省约 12（4 行 × 3 位，减去 fold），合计 ≤ 打平。**关闭。**
- **SELECT-SWAP 查表**：λ=2 时 Toffoli 383 → 246，但目标比特要多 54 个（lookup 峰值 89 → 143）。**关闭。**

## 4. 问题和可疑点
- 仍然没有干活的推送，监工是唯一在推进的。
- lut_* 架构的底子是 80 q（step 1 期间），再加加法器 ancilla，所以到不了 62q。最近 4 次的收益分别是 +0.22%、+0.24%、0%、0%。**自研架构在局部已经穷尽**，要突破只能换架构或者换基线。

## 5. 下一步指示（按优先级，均未做）
1. **在公开 62q 电路上做增量**（20.625×，唯一有希望超过公开最高 20.29× 的基线）：把 lut_AF 里已经验证过的两种测量擦除技巧（逐段 HMR 擦除 s 加短谓词的相位修正，平均省 4.1 个 Toffoli；前缀 AND 链求 s）移植到 62q 的 normalize_inv 和 unnormalize。先列一张表：62q 里每一次 HMR 后的修正 CZ/AND 链长度，以及修正谓词能不能缩短。
2. **lut 架构：step 1 期间 regs[2]（b2，7 q）是空闲的**。试一下"step 2 做完后对 b2 做 X 测量，相位修正合进最后的 del_lookup 表"，同时让 horner_inv 改走"对 r 再算一遍"的路，把 step 2 的逆运算换掉。要先算清楚 r 的相位修正怎么做，才能判断能不能把底子 80 降到 73（Q 可以到约 89–90）。
3. **lut_AF 的查表按最高位做 Shannon 分解，共享子表**（老指示 3）：3 个顶层子树（地址最高两位为 01/10/11），检查同一位输出的子树之间的异或差分是不是常数或线性，如果是就可以省一层迭代（最多约 −128 Toffoli）。
4. **step 1 B 行的加法器**：把 maxanc 的 Cuccaro 位置从"每行都在顶部 6 位"改成"跨行交错"，也就是只让同时存活的 ancilla 数 ≤ 13，而不是每一行都封顶。前提是 B 行之间可以流水化（上一行 ancilla 释放和下一行分配错开），要先确认 gadd_mix 的释放顺序。
5. 已关闭，不要再试：maxanc 11/12、相位梯度、c0 单独打相位、y 的 X 测量擦除、step-2 group 窗口、step-1 嵌套窗口、SELECT-SWAP、x<64 旁路、b2 重载。

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
