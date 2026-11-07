# SUPERVISOR.md — invsqrt（题1）监工报告

**时间戳**：2026-11-07 02:35 UTC
**结论**：**NOT_APPROVED**（最好成绩仍是 lut_V **11.484×**，本次在新容器里重建字节一致，换 salt 全量 PASS；本次试了 4 个新方向，都没有超过 V；和公开 62q 的 20.625× 差距仍然很大）

## 1. 干活的状态
- 远端分支只有 `main`、`claude/supervisor`、`claude/invsqrt-supervisor-work`。**仍然没有干活的分支 W**：干活的从 11-04 21:24Z 起就没再推送，PR #1 已在 11-05 合并。
- 监工继续在 `claude/invsqrt-supervisor-work` 上接手（draft PR #2 跟踪这个分支），本次推送 054ece1。

## 2. 已核实的事实（本次全部在新容器里亲自跑）
| 电路 | Q | Toffoli | C | cost | × 参考 | 本次复核 |
|---|---|---|---|---|---|---|
| **lut_V（sha ebc32b19）** | **101** | **1528** | 1790.49 | **180,839.28** | **11.484** | 用 `lutpoly11.py ... --gadd --pad 0` 重建，**字节一致**；官方 verifier 用 salt **sv0207** 全量 200,540,928 shot **PASS**（worst 0.99075，x=816489），和上次一致 |
| 公开 62q | 62 | — | 1624.07 | 100,692.58 | 20.625 | 本次没有重跑 |
- 硬规则检查：没有向 Kaggle 提交；没有推 main；本次新文件都小于 30KB；没有密钥，也没有比赛非公开信息。

## 3. 本次新试的方向（都关闭了，详情见 supervisor_work/invsqrt/README.md）
- **列丢弃 Horner（lutpoly12 `--lam`）**：每丢掉 1 列，所有行的加法器各少 1 个 AND，峰值也少 1 根 ancilla。但精度每列损失约 0.4 bit：fy28 下 1:1 只有 2^-23.60。fy29 下 0,-1,-3 配 1:2 达标（2^-24.07），但要 105 q / 1592，cost 194.7k，比 V 差。
- **deg3 k=7**：修好了 IndexError（原因是 lutpoly7 的系数搜索只支持 deg2，新写了 `deg3_search.py`）。0,-2,-4,-6 的误差只有 2^-22.5，系数要多 9 个 qubit。纸面估算：查表省约 290 个 Toffoli，但 horner 每个方向多约 190，还要多约 11 q，结果更差。
- **k=8**（gadd）：0,-1,-3 是 107q/1512（189.8k），0,-1,-4 是 106q/1508（187.6k），都比 V 差。
- **V 加 droprot**：droprot 1 在 x=3071203 FAIL，droprot 2 在 x=876875 FAIL，V 的旋转没有余量可以省。

## 4. 问题和可疑点
- 仍然没有干活的，监工是唯一在推进的。V 附近的参数和局部结构已经基本扫完（guards、round、pad、maxq、k、deg、列丢弃、droprot），继续调参的收益接近 0。要再进一步，**必须降 qubit**：Q 是乘法因子，101→80 就相当于 Toffoli 降 21%。

## 5. 下一步指示（按优先级，都还没做）
1. **滚动 y 寄存器 / 早相位（向 62q 架构靠拢）**：y 的低位在最后几行加完之后就固定了，每一位的相位是 2^(j+s-F)。可以试的做法是 horner 的 y-step 只保留一个 ~12 位的滑动窗口，把已经固定的低位立刻按 s 控制打相位，然后就地反算或者用测量擦除，让 y 的 27 根不必同时存在。先在纸面上算 Q 和 C：目标是 Q≤85 且 C≤1900。
2. **查表 + 加法分段的局部搜索**：现在查表是 383 个 Toffoli、51 位输出，固定成本是 2^k。可以试 a0 只放高位，低位改成"地址的低次多项式 + 小残差表"，残差放在 unary iteration 内部节点上（CX 免费），从而缩短 y 寄存器的初值位宽，让 b1 和 y 可以共用 qubit。先估计残差位宽。
3. **借比特（dirty ancilla）**：y-step 峰值时 b2（7 根）和 carry[2]（2 根）都闲着，可以用作 Gidney 加法器高位进位链的 dirty borrowed 比特（类似 Häner 的 dirty-ancilla 加法器，只给最高的约 8 位用，代价是每位多约 1 个 Toffoli）。盈亏点是每 qubit 17.7 个 Toffoli，按 26 个峰值加法器摊下来，每个加法器每借 1 位最多只能多 0.68 个 Toffoli，所以只在高位、而且只对峰值行用。先精确算账。
4. **S=Q×C 的旋转余量**：V 的 margin 只有 0.9%，ε 很小，每个旋转约 30 T。如果能便宜地拿到 1 bit 精度（例如只给 a0 加 1 位 guard，+1 q），margin 变成约 50%，每个旋转能省约 3 T，35 个旋转合计约 26 Toffoli-eq（约 1.5%）。需要和 +1 q（约 1%）对比，用 verifier 实测。
5. 已关闭的方向：之前列过的全部，加上本次的列丢弃、deg3 k=7、k=8 gadd、V+droprot。

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
