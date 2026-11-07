# SUPERVISOR.md — invsqrt（题1）监工报告

**时间戳**：2026-11-07 04:30 UTC
**结论**：**NOT_APPROVED**（最好成绩从 lut_Y 12.082× 提到 **lut_Z 12.135×**，96 q，官方 verifier 全量 PASS；但离公开 62q 的 20.625× 还差很远，方向没有穷尽）

## 1. 干活的状态
- 远端分支只有 `main`、`claude/supervisor`、`claude/invsqrt-supervisor-work`。**仍然没有干活的分支 W**：干活的从 11-04 21:24Z 起就没再推送，PR #1 已在 11-05 合并，main 的最新提交仍是 037709c（11-05）。
- 监工继续在 `claude/invsqrt-supervisor-work` 上接手，本次推送了 c57a1c8 和 291c039，并更新了 draft PR #2 的标题和描述。

## 2. 已核实的事实（本次都在新容器里亲自跑，python3.13 + data/kickmix/kickmix.so）
| 电路 | Q | Toffoli | C | cost | × 参考 | 本次复核 |
|---|---|---|---|---|---|---|
| lut_Y（sha 9c03bbeb） | 96 | 1528 | 1790.49 | 171,886.84 | 12.082 | 用 README 命令重建，字节一致；换 salt sv0507 全量 200,540,928 shot PASS（0.99075） |
| **lut_Z（新，188a2b4d）** | **96** | **1528** | **1782.61** | **171,130.46** | **12.135** | 默认 salt 全量 PASS（worst 0.97092，eps 1.669e-13，和模型预测完全一致）；换 salt sv0507z 全量 PASS（结果一致） |
- 倍数按 2,076,774.23 / score 计算，score = Q × C，都是 verifier 输出的总 cost，不是只算了某个子项。
- 硬规则检查：没有向 Kaggle 提交；没有推 main；新文件中最大的是 .kmb，约 276KB；没有密钥，也没有比赛非公开信息。

## 3. 本次做的改进（详情见 supervisor_work/invsqrt/README.md）
- **Z：按 s 加权的系数搜索**（`lutpoly16.py`）。verifier 的旋转预算是 min_x (tol − |err|)，这是绝对相位。对 x_norm = x·4^s 来说，它正比于 2^s·(2^-24·exact − |err|)，绑定的 s 是：x_norm ≤ MAX_X 时 s=0；否则 x_norm%4==0 时 s=1；其余不可达。原来的搜索和 a0 居中用的是不加权的相对误差，而且覆盖全部 x_norm。现在每段在 (d1,d2)∈[-3,3]² 和整数 a0 平移（中心 ±4）上最大化加权最小 slack。电路结构不变，只有 eps ×3.05，每个旋转 29.92→29.07 T，C −7.9。
- 已关闭（模型精确检查）：guards 0,-3,-4 / 0,-2,-5 / 0,-3,-5 的加权 slack 是负数（−8/−6/−11 y 单位）；R=5 没有变化；droprot 1 能过，但 34×29.92 = 35×29.07，没有收益；droprot 2 FAIL（1.099）；k=8 配 0,-1,-4 FAIL（1.0004），而且要 100~102 q / 1524。

## 4. 问题和可疑点
- 仍然没有干活的，监工是唯一在推进的。
- 精度和旋转这条线已经基本到头：加权最小 slack 只有 0.51 个 y 单位，受 a0 的整数粒度限制。
- 峰值 96 = 行底座 83 + 13 根 ancilla；每降 1 q 要多 26 Toffoli（C/Q=18.6），所以调加法器已经到头。真正的收益只能来自缩小底座或换架构。

## 5. 下一步指示（按优先级，都还没做）
1. **fold 不用 fan-out + 缩底座组合拳**：fold 改成 `c1 ? ~(~hi + [c0, c1∧¬c0]) : hi + c0`（源只有 2 位，少 n−2 根 qubit），再加上 b2 只依赖地址高 6~7 位（每 2~4 段共享，查表/擦表几十个 Toffoli），配合逐段重拟合 b1/a0（lutpoly16 目标）。目标是峰值 ≤ 90 且 Toffoli 增加 < 18.6/q。
2. **denorm CSWAP（每个方向约 122，合计约 244 = 14% 的 C）**：(a) 试 8,4,2,1 顺序加 lane 裁剪的精确账；(b) 试在 y 的最低几位上，s 较大时直接截断（大 s 时 x 小，tol 的绝对量大），配合 droprot 按 s 分段算误差；(c) 研究 62q 的 unnormalize 到底怎么只用很少 Toffoli 完成移位。
3. **查表 383（本次已量账）**：用 qubit_ledger 量 Z 的各阶段峰值：normalize 37、lookup 86、horner 96、denorm/phase 94、lookup_inv 81。查表期间只空出 10 根，λ=2 的 SELECT-SWAP 需要 52 根输出副本，**不可行**。剩下的办法：把 b2（7 位）挪出主表，改成"地址高位小表"，在 horner 之前单独查；或者让 a0 的低位由 b1 推出来，以减少表宽。查表的 Toffoli 只和地址数有关，所以收益只在 qubit 这边。
4. **滚动 y 寄存器 / 早相位**（向 62q 架构靠拢）：仍然是唯一能把 Q 降到 70 以下的方向，需要整体重新设计。
5. **（低优先，先算账）a0 半单位精度**：slack 受整数 a0 限制，可以给 a0 加 1 个小数位（y 寄存器 +1 位，或者用 y-step 某一行的 carry-in 位当作 a0 的 2^-1 位），然后用 lutpoly16 的目标重新算账。需要 eps 提升超过约 2× 才能抵掉 +1 q 的话就不做，先在模型上算 slack。 粗算：eps 再 ×2 只省约 5 Toffoli-eq，大约是 1 q 的 1/4，大概率不划算。

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
