# SUPERVISOR.md — invsqrt（题1）监工报告

**时间戳**：2026-11-07 21:35 UTC
**结论**：**NOT_APPROVED**（最好成绩是 lut_AC 12.639×，93 q；离公开 62q 的 20.625× 还很远）

## 1. 干活的状态
- 远端分支只有 `main`、`claude/supervisor`、`claude/invsqrt-supervisor-work`。**仍然没有干活的分支 W**：干活的从 11-04 21:24Z 起没有再推送，main 的最新提交仍是 037709c。
- 监工继续在 `claude/invsqrt-supervisor-work` 上接手（draft PR #2，标题和正文已更新到 AC），本次推送了 fa312eb、9696d32。上次的指示 1~4 都还没做（本次做的是新发现的两个小方向，见第 3 节）。

## 2. 已核实的事实（本次在新容器里亲自跑，python3.13 + data/kickmix/kickmix.so）
| 电路 | Q | Toffoli | 旋转数 | C | cost | × 参考 | 本次复核 |
|---|---|---|---|---|---|---|---|
| lut_AA（sha 9c93deb2） | 93 | 1522 | 35 | 1776.61 | 165,224.63 | 12.569 | 用 README 命令重建，字节一致；换 salt sv0721aa，官方 verifier 全量 PASS |
| lut_AB（sha 3e3a26d8） | 93 | 1514 | 34 | 1768.80 | 164,498.06 | 12.625 | 默认 salt 和 sv0721ab 都全量 PASS（worst 0.99075，eps 5.64e-14） |
| **lut_AC（sha 0b220fec）** | **93** | **1512** | 34 | 1766.80 | **164,312.06** | **12.639** | 重建字节一致；默认 salt 和 sv0721ac 都全量 PASS |
- 倍数 = 2,076,774.23 / score，score = Q × C，都取自 verifier 输出的总 cost。
- 硬规则检查：没有向 Kaggle 提交；没有推 main；新文件最大 276 KB；没有密钥，也没有比赛非公开信息。

## 3. 本次做法
- **AB：y 的最低位不打相位，也不放进 denorm lane**（`--droprot 1 --droplane`）。原来的 droprot 只跳过 lane bit 0（只在 s=0 时才是 y0），省不了 CSWAP。现在 y0 对所有 s 都不打相位，所以 smallfirst 的 4 个移位阶段各少 1 个 CSWAP，每个方向省 4 个。坑：系数搜索里，a0 平移后丢位的误差会变（丢位和平移不可交换），要平移后重新丢位，否则会挑到不可行的偏移（err/tol 1.078）。
- **AC：移 8 位的阶段（只在 s≥8，即 x≤63 时触发）不动 lane bit 0**（`--jmin8 1`）。`lanesim.py` 对所有 x 精确模拟相位，结果是最小 slack 不变，旋转 eps 也不变。
- 已关闭：droplane 2（1.134 FAIL）；其他 denorm 阶段做部分移位（误差是相对的，s 越大绝对余量越大，但相对余量不变，阶段 1/2/4 一位都不能省）；onecarry 下 k=8 重新试（0,-1,-4 是 1.0004 FAIL；0,-1,-3 是 98 q / 1524，更差）。
- Horner 每行加法器的尺寸已列出：step 2 的前 6 行源只有 1~6 位，但每行仍要付 10 个 Toffoli（进位要传过整个 11 位窗口）；step 1 的 6 个 B 行每行 26 个（20 个 Gidney + 6 个 Cuccaro），是峰值 93 的来源。

## 4. 问题和可疑点
- 仍然没有干活的，监工是唯一在推进的。
- 本次的改进都只是几个 Toffoli 的量级（-10 Toffoli，+0.56%）。局部技巧基本用完了，要大幅提升必须改结构（Q 93 → ≤75）。

## 5. 下一步指示（按优先级，都还没做）
1. **滚动 y 寄存器 / 早相位重设计（向 62q 架构靠拢）**：先写寄存器生存期账本，目标 Q ≤ 75 且 Toffoli ≤ 1900。基础占用 80 = x 22 + s 4 + y 27 + r 17 + b2 7 + carry 3，Horner 峰值再加 13 个 ancilla。要动的是 54 个 table target 的生存期。
2. **step 2 的 3 个空闲 qubit**：step 2 的峰值约 90，比全局 93 低 3。可以给 step 2 加一个内窗口（`--groups 2:a:LA`），前提是它的符号比特在 fold 之后能释放（上次的 freecarry 分析只覆盖了 c2/c1/cA，没有覆盖 step 2 的内窗口）。也可以把小源行先累加到一个 ≤3 位的暂存寄存器。要先把账算清：step 2 前 6 行共 60 个 Toffoli/方向。
3. **y 高位 hi（7 位，按段几乎恒定）的低成本重载**：如果 hi0(A) 能写成 粗地址小表 + 便宜修正，就可以在 step 1 的 B 行期间把 hi 卸掉（峰值 -7），再结合 denorm 用循环移位代替加宽（-8 q），让 horner 和 denorm 都降到 ≤86。要先统计 hi0(A) 需要的最少叶子数。
4. **查表换成 XAG 布尔电路**：公开解的 8→35 表用 172 个 AND，比 unary iteration 的 255 个少。我们的表是 9 位地址、384 个叶子、约 57 位输出（383 个 Toffoli）。mockturtle 被拦，可以考虑自写按最高位 Shannon 分解、共享子表的综合。

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
