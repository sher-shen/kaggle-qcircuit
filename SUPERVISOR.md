# SUPERVISOR.md — invsqrt（题1）监工报告

**时间戳**：2026-11-07 00:45 UTC
**结论**：**NOT_APPROVED**（自研最好的仍是 lut_U2 10.132×，本次再次全量复核 PASS；公开 62q 是 20.625×。已连续 15 次没有 cost 提升）

## 1. 干活的状态
- 远端分支只有 `main`（037709c）、`claude/supervisor`、`claude/invsqrt-supervisor-work`。**仍然没有干活的分支 W**：干活的从 11-04 21:24Z 起就没再推送，PR #1 已在 11-05 合并。
- 监工继续在 `claude/invsqrt-supervisor-work` 上接手，本次推送 db4a900（lutpoly10 非均匀分段，以及 U2 的复核 json）。

## 2. 已核实的事实
| 电路 | Q | Toffoli | C | cost | × 参考 | 本次复核 |
|---|---|---|---|---|---|---|
| lut_U2（sha 27d75c8f） | 109 | 1618 | 1880.49 | 204,973.19 | 10.132 | **新容器里用 lutpoly7.py 重建，字节一致**；换 salt sv0700 跑官方 verifier，全量 200,540,928 shot **PASS**（35 个旋转，worst 0.99075，x=816489） |
| 公开 62q（67482db6） | 62 | — | 1624.07 | 100,692.58 | 20.625 | 本次未重跑（之前已多次全量 PASS） |
- U2 各 stage 的 Toffoli 数：normalize 84、lookup 383、horner 397、denorm 118、denorm_inv 118、horner_inv 397、lookup_inv 41、normalize_inv 80。
- 硬规则检查：没有向 Kaggle 提交；没有推 main；只提交了 .py、README 和小 json；没有密钥，也没有比赛非公开信息。

## 3. 本次实验：非均匀分段（新方向，已关闭）
- 思路：分段误差约按 h^3·M^-3 缩放，所以 M∈[2,4) 的段宽可以翻倍。Horner 的数字位统一取 x_norm 低 14 位；对 M<2 的部分，x[13] 同时当地址位。查表改成 8 位 unary iteration（192 个值），M<2 的 64 个值再嵌套一层 1 位 iteration。
- 结果：lookup 从 383 降到 **255**，和预期一致。但 horner 每个方向从 397 涨到 468：每步多一行；在 14 位数字单位下，M<2 段的系数翻倍或翻四倍，所以 b1 从 17 位变 18 位、b2 从 7 位变 9 位。整体是 115 q、1632 Toffoli，误差 2^-23.78（不达标）。Q×(T+262) = 217.8k，比 U2 的 205.0k 差。**关闭。**

## 4. 问题和可疑点
- 仍然没有干活的，用户已经收尾，这个 routine 每小时还在消耗额度。局部调参和参数化变体都已穷尽，剩下的都是一小时内做不完的结构性重写。**强烈建议用户停掉这个监工 routine**，或者开一个长时间的专门会话来做下面第 1、2 条。

## 5. 下一步指示（按优先级，都还没做）
1. **phase 和 horner 交错，去掉 y1 的整段 denormalize（来回 236 个 CSWAP，约占 14.6%）**：利用 exp(iθ(a+b)) = exp(iθa)·exp(iθb)，对整数严格成立。y 的最后一两行 Horner 不再加进 y，而是直接对行的值打相位，这样可以省掉"加进去再减出来"的那部分 2×行成本。难点是相位角带 2^s 因子。先算账：s 有 11 种取值，用 (bit AND [s=v]) 的方式要 11 倍旋转，必然不划算；要找按 s 的二进制位分解、只需 4 层受控移位的写法。
2. **horner 的 Gidney/Cuccaro 混合加法器**：峰值 109 里约有 21 根是加法器 ancilla。对峰值处的少数几行改用 1 ancilla 的 Cuccaro（每行多约 n 个 Toffoli），其余行保持不变，目标 Q≤100 且 Toffoli 增加 ≤140（盈亏平衡约为每 qubit 17 个 Toffoli）。kickmix 的 maxq 是全局按 14 Toffoli/qubit 换，不能按行选，需要自己写加法器。
3. **加法器换成不等长、不补 pad 的版本**，在 maxq 约束下逐行做整数规划（上次的第 3 条，还没做）。
4. 查表的启发式 XAG 随机重写（177 → ≤175），收益上限约 0.1%，优先级最低。
5. 已关闭的方向：之前列过的全部，加上本次的非均匀分段。

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
