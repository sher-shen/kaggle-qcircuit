# SUPERVISOR.md — invsqrt（题1）监工报告

**时间戳**：2026-11-06 21:25 UTC（每小时一次的监工，routine 仍在触发）
**结论**：**NOT_APPROVED**（自研最好的仍是 lut_U2 10.132×，这次换新 salt 全量复核 PASS；公开 62q 是 20.625×。这次没有 cost 提升，指示 2「改系数合同」用离线分析基本关掉了）

## 1. 干活的状态
- 远端分支只有 `main`（037709c）、`claude/supervisor`、`claude/invsqrt-supervisor-work`，**仍然没有干活的分支 W**。干活的从 11-04 21:24Z 起就没再推送，用户 11-05 已合并 PR #1 并在 main 上收尾。
- 监工继续在 `claude/invsqrt-supervisor-work` 上接手，这次推送了 8361420：`lut_counter_chain.py`、`lut_counter_extend.py`、`lut_counter_fit.py`、`../invsqrt/verify_lut_U2_sv0806.json`，README 里加了一节。

## 2. 已核实的事实
| 电路 | Q | C | cost | × 参考 | 本次复核 |
|---|---|---|---|---|---|
| lut_U2（main，sha 27d75c8f） | 109 | 1880.49 | 204,973.19 | 10.132 | **这次换新 salt sv0806 重跑官方 verifier，全量 200,540,928 shot PASS**（Toffoli 1618、35 个旋转、worst 0.99075，x=816489），和之前一致 |
| 公开 62q（67482db6） | 62 | 1624.07 | 100,692.58 | 20.625 | 这次没重跑。ops.json 重新 clone，用来提取查表真值表（177 个 static Toffoli，和之前一致） |
- 硬规则检查：没有向 Kaggle 提交；没有推 main；只提交了 .py、README 和一个几 KB 的 json；没有第三方电路、密钥或比赛非公开信息。

## 3. 本次实验（指示 2：改系数合同）
- 把 coeff_lookup 的 35 个输出（地址 q14 是 LSB，128 个一半是两种情况）按"高位只在低位翻转处翻转、次数减半"来找，发现两条**严格的二进制计数器链**：A = q41,q57,q40,q51,q50，B = q60,q44,q43,q59,q24,q42。之前说的 7 个阶梯输出就是它们的高位。
- 解码成模 2^5、2^6 的有符号整数后，它们是平滑递减、会回绕的序列。B 在前一半上就是 round(三次多项式(a))，残差最大 0.65。所以这 11 根线是平滑多项式系数的低 n 位，下游按模 2^n 用它们。
- 再在其余 24 个输出里贪心找下一位，允许和最多 2 个地址或计数器位做 XOR（只用 CNOT 的重编码），**没有比随机比特明显更平滑的候选**。所以剩下 24 个输出（承担精度）不是 A/B 的低位，用便宜的仿射重编码也变不平滑。
- 结论：能平滑化的只有 11 根线。如果改成用算术生成（常数乘加法器，大约 15~40 Toffoli），比它们在 177 个 AND 的表里分摊到的份额还贵；剩下 24 位没有单比特余量（06:45 已查）。**离线重编码没有找到收益，指示 2 关闭。**
- 另外确认：python-sat 的 wheel（cp313 manylinux）可以从 pip 下载，**下次可以直接用来跑 SAT 精确 MC**（这次没装，也没跑）。

## 4. 问题和可疑点
- 仍然没有干活的。用户已经收尾，这个 routine 每小时还在消耗额度。从 11-05 07:50 起连续 12 次没有 cost 提升。
- 公开 62q 这一路剩下的只有全局 SAT 或精确综合，以及自研电路的结构性重设计，这两件事一小时的无人值守运行都很难做完。

## 5. 下一步指示（按优先级，都还没做）
1. **用 python-sat 对 coeff_lookup 做分块精确 MC**：先做小块练手，比如只算计数器 A（5 个输出、8 个输入），求最少 AND 数，验证编码正确、看求解时间；然后对那 24 个随机位按 xag_mffc 的锥重叠分成 4~6 组，带宽度约束（≤4 根 scratch，允许输出原地累加）。目标是总数 < 172（63q 版的数）。哪组单独求解就超过它现在用到的 AND 数，就提前停。
2. **把查表拆成两个 7 位子表加选择**：地址最高位 q21 把表分成两个 128 段，而且两段规律不同。可以先离线算：两个 7 输入子表的模仿射秩、ANF 项数，以及用 q21 做 CSWAP 或受控选择的代价（每个输出 1 个 AND）。和 177 比，看有没有可能更便宜。
3. **自研 U2 一路往 62q 的结构靠**：U2 有 109q、1618 个 Toffoli；62q 有 62q、1327 个 Toffoli，差距主要在 Q。从 62q 的 stage 划分出发（查表 → 相位 taps → 三段算术 → 归一化），把 U2 的精度预算（行舍入、粗 guard）套进去，目标是 ≤70q、Toffoli ≤1700 的自研版（约 17×）。
4. 已关闭的方向：之前列过的全部，加上这次的计数器链重编码 / 系数合同平滑化。

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
