# SUPERVISOR.md — invsqrt（题1）监工报告

**时间戳**：2026-11-05 05:35 UTC（每小时一次的监工运行）
**结论**：**NOT_APPROVED**（本次 9.457× → **9.755×**，全量验证通过；离公开最高约 20.29×（63 qubit）还差 2.08 倍，差距主要在 qubit：112 vs 63）

## 1. 干活的状态
- `git fetch` 后远端仍只有 `main`、`claude/supervisor`、`claude/invsqrt-supervisor-work`；PR 只有监工开的 draft #1。**依然没有干活的分支 W**（会话启动约 9 小时，零推送）→ 监工继续接手，在 `claude/invsqrt-supervisor-work` 上干活。
- 上次指示：1（相位融合）本次算账后判定**不划算**（见第 4 节）；2、3 没做；4 没做；5 没做。本次做的是新发现的两个"免费"Toffoli 削减。

## 2. 已核实事实（亲自跑官方 verifier，200,540,928 shots，4 核，每次约 5~6 分钟）
| 候选 | Q | Toffoli | C | cost | × 参考 | 结果 | 复核方式 |
|---|---|---|---|---|---|---|---|
| lut_N（上次最好） | 112 | 1708 | 1960.76 | 219,605.63 | 9.457 | PASS（0.931） | 按 README 命令重建，字节一致（ee3f21fc）；**换 salt `sv0505` 全量重跑**，score 一致 |
| lut_P = N + smallfirst | 112 | 1688 | 1940.76 | 217,365.63 | 9.554 | PASS（0.931） | 全量；`verify_lut_P.json` |
| **lut_Q = P + foldadd（当前最好）** | **112** | **1648** | 1900.76 | **212,885.63** | **9.755** | PASS（0.931） | 全量（默认 salt）+ 另跑 2 shot/x 全 x 筛查也 PASS；`verify_lut_Q.json`；sha f5c49fc0 |
- 倍数 = 2,076,774.23 / verifier 的 `score`（含 35 个旋转的总 cost），不是子项。P、Q 与 N 数值完全相同（worst err/tol 都是 0.9305），只省 Toffoli。
- 硬规则：没有向 Kaggle 提交；没推 main；最大新文件 312 KB；没有密钥；提交里只有本地 verifier 数字。

## 3. 本次做的事（监工接手，分支 claude/invsqrt-supervisor-work，commit "candidates P ... Q"）
1. 用 kickmix flame chart 拆了 N 的 Toffoli：normalize 78 / lookup 354 / Horner 395 / denorm 122 / 相位（35 旋转≈252 C）/ denorm_inv 122 / Horner_inv 395 / unlookup 38 / normalize_inv 74。**峰值 112 q 在 y 步行加法器里**：x 22 + s 4 + y 28 + r 18 + b2 8 + pad 6 + 进位 4 + 加法器辅助约 22。
2. `--smallfirst`：反归一化按 1,2,4,8 的顺序移位，每级 CSWAP 只覆盖可能非零的位（利用 s≤10、s3=1 ⇒ s2=0），132→122 每方向，−20 Toffoli。
3. `--foldadd`：Horner 的进位折叠 `hi += c0; hi -= 2c1`（两个受控自增，约 31 Toffoli）改成一个加法器 `hi += [c0, c1, c1, …]`（c0−2c1 的补码，c1 用 CX 扇出到临时比特），两步两方向共 −40 Toffoli。
4. pad 重扫（带新开关）：pad 4/5/6/7/8 → 110q/1692、111q/1668、112q/1648、113q/1632、114q/1620，pad 6 仍最好。
5. lutpoly6.py 新开关默认关闭，旧输出字节一致（N 重建仍是 ee3f21fc）。

## 4. 问题和可疑点 / 算账结论
- 干活的会话 9 小时零推送，基本确定已停，**用户最好去看一下那个会话**。
- **上次指示 1（s 高位改成"AND 临时比特 + 旋转"）算账不划算**：省 s2/s3 两级 CSWAP 约 2×60，但 y 每位都要 3 档角度，非 Clifford 旋转从 35 涨到约 85，+50×≈7.2 C ≈ +360 C；而且反归一化不在 qubit 峰值上，省不了 Q。不要再做。
- 在现有架构里 Q 基本卡在 112：maxq（每少 1 q 每个加法器 +1 Toffoli，y 步 26 个加法器）、去 r 步窗口、b2 粗表重算都算过，都比现在差。**要到 15×以上必须换架构**（第 5 节 1、2）。
- 相位-梯度寄存器（把各行直接加进相位梯度，省 y 步逆运算）也算过：需要约 38 位梯度寄存器 + 37 辅助，qubit 爆掉，不做。

## 5. 下一步指示（按优先级，都还没做）
1. **a0 和 P 分开打相位，砍掉 y 寄存器高位**（新）：相位对 y 是线性的，y = a0 − P。查表后先把 a0（28 位）按 s 移位打相位、移回，然后用测量式擦除把 a0 从查表输出里去掉（del_lookup 只擦 a0 那段，约 38 Toffoli）；Horner 只把 −P 累加进一个约 22 位、初值为偏置 2^21 的新寄存器（偏置从 a0 表里减掉，保持非负），对 P 移位打相位，再逆运算。好处：y 步峰值少 a0 高位（约 −6~8 q），而且不再需要 hi/进位折叠。代价：多一套移位（约 +2×100 CSWAP）和约 +15 个旋转。**先只算账**（峰值 Q、Toffoli、旋转数），S 能降再写。
2. **查表粗细分段（don't-care 树）**：相对误差要求下 M∈[2,4) 的段可以比 M∈[1,2) 宽一倍。外层对 x[14..21] 做 unary iteration（192 叶），只在 M∈[1,2) 的 64 个叶子上再按 x[13] 分（每叶 1 个 AND）≈ 256 叶，比 384 少约 100 Toffoli。难点：Horner 行数要统一成 14 行（细段在 δ14 的半区间上拟合即可），会让 r +1 位、b2 +2 位、每步 +1 行；先用整数模型算误差和总账，再决定。
3. **自写 y 步加法器提前擦进位前缀**（上上次指示 2，仍没做）：y 步 26 个 22 位加法器的约 22 个辅助比特是峰值大头；按 8 位分块、块间 1 比特接力，先在 4~8 位上穷举验证。目标峰值 −10 q。
4. **降截断噪声换比特**（上次指示 4）：误差瓶颈在 y 步行截断；"最低 1 位虚拟化"或低权重行合并，让 guards 0,−2,−5 过线（Q −1、Toffoli −4）。
5. 系数搜索扩到 a0/b1/b2 联合，并以 verifier 真实 err/tol（含 droprot 截断）为目标。
6. 每个新候选都用官方 verifier 全量跑（`PYTHONPATH=data/kickmix python3.13 data/verifiers/invsqrt/verify_submission_invsqrt.py X.kmb`，约 5~6 分钟；快速筛查用 `--shots-per-x 2 --batch-size 4`）；脚本要能字节一致重建。

## 历史
- 2026-11-05 01:35 UTC：没有干活的分支；复核 sv_B（1.181× PASS，一致）；监工接手，做了 LUT+二次方案 lut_C 4.417× 和 lut_D 4.763×（全量 PASS），lut_E 4.792×（全量 PASS），开了 draft PR #1；NOT_APPROVED。
- 2026-11-05 02:45 UTC：依然没有干活的分支；独立全量复核 lut_E（4.792×，一致）；监工继续接手，做了 signed-digit + 窗口 Horner（H 8.452×）、clamp（I 8.598×）、二分归一化（J 8.962×）、零顶移位（K **9.060×**），全部全量 PASS，推到 claude/invsqrt-supervisor-work，并更新 PR #1；NOT_APPROVED。
- 2026-11-05 03:35 UTC：依然没有干活的分支；换 salt 独立全量复核 K（一致）；监工继续接手，做了 droptop（L **9.158×**，113 q，全量 PASS）；maxq 限比特和 lutpoly5（M∈[1,2)）都没有变好；判断现在的架构已接近局部最优，下一步要改结构（自写加法器、高位提前打相位、c2 分组）；NOT_APPROVED。
- 2026-11-05 04:35 UTC：依然没有干活的分支；换 salt 独立全量复核 L（一致）；监工继续接手，做了 droprot（9.19×）和每段系数整数搜索（lut_N **9.457×**，112 q，全量 PASS）；发现 lutpoly5 的 rangeq bug（不是精度问题，放弃该方向）；fy=28 证明不可行；NOT_APPROVED。
- 2026-11-05 05:35 UTC：依然没有干活的分支；换 salt 独立全量复核 N（一致）；监工继续接手，做了 smallfirst（P 9.554×）和单加法器进位折叠（Q **9.755×**，112 q，全量 PASS）；算账否定了"s 高位用 AND+旋转"方向；NOT_APPROVED。
