# SUPERVISOR.md — invsqrt（题1）监工报告

**时间戳**：2026-11-07 03:45 UTC
**结论**：**NOT_APPROVED**（本次把最好成绩从 lut_V 11.484× 提到 **lut_Y 12.082×**，96 q，官方 verifier 全量 PASS；但和公开 62q 的 20.625× 差距仍然很大，方向没有穷尽）

## 1. 干活的状态
- 远端分支只有 `main`、`claude/supervisor`、`claude/invsqrt-supervisor-work`。**仍然没有干活的分支 W**：干活的从 11-04 21:24Z 起就没再推送，PR #1 已在 11-05 合并。main 的最新提交是 037709c（11-05，memory 收尾记录）。
- 监工继续在 `claude/invsqrt-supervisor-work` 上接手，本次推送了 62b2e5c、8456e5f、d86873a，并更新了 draft PR #2 的标题和描述。

## 2. 已核实的事实（本次全部在新容器里亲自跑，python3.13 + data/kickmix/kickmix.so）
| 电路 | Q | Toffoli | C | cost | × 参考 | 本次复核 |
|---|---|---|---|---|---|---|
| lut_V（sha ebc32b19） | 101 | 1528 | 1790.49 | 180,839.28 | 11.484 | 重建字节一致；salt sv0307 全量 200,540,928 shot PASS（0.99075） |
| lut_W（新，f145f85e） | 100 | 1528 | 1790.49 | 179,048.79 | 11.599 | 默认 salt 全量 PASS |
| lut_X（新，eaaa147a） | 102 | 1458 | 1720.49 | 175,489.77 | 11.834 | 默认 salt 全量 PASS |
| **lut_Y（新，9c03bbeb）** | **96** | **1528** | 1790.49 | **171,886.84** | **12.082** | 默认 salt 和 salt sv0407 两次全量 PASS（0.99075，结果一致） |
| 公开 62q | 62 | — | 1624.07 | 100,692.58 | 20.625 | 本次没有重跑 |
- 倍数按 2,076,774.23 / score 计算，score = Q × C，都是 verifier 输出的总 cost，不是只算了某个子项。
- 硬规则检查：没有向 Kaggle 提交；没有推 main；新文件中最大的是 .kmb，约 280KB；没有密钥，也没有比赛非公开信息。

## 3. 本次做的改进（详情见 supervisor_work/invsqrt/README.md）
- **W：top-CCX 加法器**（`lutpoly13.py --topccx`）。Gidney 加法器进入最高位的进位改用 1 个 CCX 直接 XOR 到目标位，不再用 init_and 存进 ancilla。Toffoli 数不变，每个加法器少用 1 根 ancilla，峰值 101→100。对 n≤6 做了穷举的经典检查。
- **X：两级 Horner 窗口**（`lutpoly14.py --groups 1:7:13`，扫描脚本 `group_scan.py`）。y-step 的前 7 行源只有 6~12 位，却要付 21 位窗口的进位链。把这 7 行放进 13 位的小窗口，配 2 根独立的带符号进位，最后一次折叠进主窗口。值域在所有 x_norm 上精确检查过：[-6510, 15940]，在允许范围内。每个方向省 35 Toffoli，代价是 +2 q。
- **Y：Gidney/Cuccaro 混合加法器**（`gadd_mix.py`，`lutpoly15.py --maxanc 13`）。需要超过 13 根 ancilla 的加法器，把源的最高几位改成原地 MAJ/UMA 进位：每位多 1 个 CCX，不需要 ancilla。实际只影响 y-step 的 6 个大行，Toffoli +70，峰值 102→96。对 n≤7、全部 maxanc/cin/sub 组合做了穷举检查，0 失败。
- 已关闭的方向：maxanc 12/11 仍是 96 q（峰值在 fold 的 fan-out），Toffoli 1554/1580，更差；group 6:12/8:14/9:15 都更差；r-step 分组每方向只省 11，而且它的进位会一直占着到 y-step 峰值，不划算。96 以下每降 1 q 都要在 13 行×2 个方向上各多 1 个 CCX（共 26 个，C/Q 只有 18.7），不划算。

## 4. 问题和可疑点
- 仍然没有干活的，监工是唯一在推进的。
- Y 的精度余量只有 0.9%（worst 0.99075，x=816489），旋转 eps 只有 5.5e-14，每个旋转约 30 T，35 个旋转合计约 262 Toffoli-eq，占 C 的 15%。
- 现在的峰值 96 = 底座 83（x 22 + s 4 + y 27 + r 17 + b2 7 + 3 对进位 6）+ 13 根 ancilla。要再大幅降低必须缩小底座，调加法器已经基本到头。

## 5. 下一步指示（按优先级，都还没做）
1. **fold 不用 fan-out**：c1=1 时用补码技巧 `hi' = ~(~hi + (c0 + 2·¬c0))`，源只需 [c0, t]，其中 t = c1∧¬c0（1 个 AND，1 根 ancilla）。每个 fold 少 n-2 根 qubit。单独用没有收益，但它能解除 maxanc≤12 时的 fold 峰值。可以和第 2 条一起做：峰值降到 94 = denorm 的水平。
2. **缩 denorm/phase 的底座（94）和行的底座（83）**：b2（7 根）和 carry[2]（2 根）在整个 y-step 和 denorm/phase 期间都闲着。可以试"r-step 之后用一次只针对 b2 位的测量式 del_lookup 擦掉 b2（约 41 Toffoli），horner_inv 之前再查一次表"。但重查要约 383，需要先算账。更好的办法是让 b2 只依赖地址的高 6~7 位（每 2~4 段共享），这样查表/擦表只要几十个 Toffoli；同时让 b1、a0 逐段重新拟合，精度用 deg3_search/lutpoly7 的搜索精确检验。
3. **精度余量换旋转成本**：每多 1 bit 余量，35 个旋转合计省约 4.9 Toffoli-eq。可以试 a0 逐段重新居中的目标改成"最大化 min(tol − |err|)"（绝对量，按 x 加权），或只给最差的段（M≈3.2，x≈816489 所在的段）提高系数精度，看 worst 能否降到 0.9 以下。用 verifier 实测。
4. **y-step 的 B 组行再分级**：B 组 6 行现在每行 20+6 CCX。可以试在 B 组内部用 Booth radix-4 处理最高的 2 行，或者把 B 组的进位链拆成两段加比较器，再用 lutpoly15 的 maxanc 精确算账。
5. **滚动 y 寄存器 / 早相位**（向 62q 架构靠拢）：仍然是唯一能把 Q 降到 70 以下的方向，需要整体重新设计，详见上一版第 1 条。

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
