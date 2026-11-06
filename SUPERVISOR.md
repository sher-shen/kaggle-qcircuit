# SUPERVISOR.md — invsqrt（题1）监工报告

**时间戳**：2026-11-06 06:45 UTC（每小时一次的监工；routine 仍在触发）
**结论**：**NOT_APPROVED**（自研最好的仍是 lut_U2 10.132×；公开 62q 电路 20.625× 本次又全量复核 PASS。本次没有新的提升，并且第一优先方向被权限挡住了）

## 1. 干活的状态
- 远端分支：`main`（037709c）、`claude/supervisor`、`claude/invsqrt-supervisor-work`。**仍然没有干活的分支 W**，干活的从 11-04 21:24Z 起就没再推送。
- 监工继续在 `claude/invsqrt-supervisor-work` 上接手，本次推送了 f667f7c：`lut_extract_xag.py`、`lut_xag_rank.py`、`lut_dcare.py`、`verify_public62_0606.json`，另外在 README 里加了一节。

## 2. 已核实的事实
| 电路 | Q | C | cost | × 参考 | 本次复核 |
|---|---|---|---|---|---|
| 公开 62q（67482db6） | 62 | 1624.07 | 100,692.58 | 20.625 | 新容器里从 ops.json 重建，**sha 字节一致**；官方 verifier 全量重跑 **200,540,928 shot PASS**（Toffoli 1327.483、worst 0.99932 x=161、score 100,692.58，一致） |
| lut_U2（main） | 109 | 1880.49 | 204,973.19 | 10.132 | 本次没重跑（之前已多次换 salt 全量 PASS） |
- 硬规则检查：没有向 Kaggle 提交；没有推 main；只提交了 .py、README 和 verifier 的 json 输出（几 KB）；没有第三方电路文件（cl.v 是从第三方电路导出的，没有提交）；没有密钥，也没有比赛非公开信息。

## 3. 本次实验
- **指示 1（用 MC 工具重综合 coeff_lookup）**：`lut_extract_xag.py` 把 ops 238..15214 导出成 8 输入、35 输出的 XAG Verilog，177 个 AND。这段里没有条件块，15 根 payload 线（q0..q13、q23）也完全没碰过，可以直接喂给 mockturtle。**但在云端编译 mockturtle（外部代码）被 Claude Code 的 auto-mode 权限分类器拒绝了，所以没跑成。** 要继续这个方向，需要用户放行，或者在本地跑。
- `lut_xag_rank.py`：177 个 AND 的乘积真值表彼此线性无关，也不在输入和更早乘积的张成里，XAG 层面 0 冗余。
- **查表 don't-care（新方向，已关闭）**：发现系数线被 HMR 测掉后，相位修正都是 one-hot 查表上的纯 Z 门，代价和表的内容无关，所以理论上表值的 don't-care 可以利用。`lut_dcare.py` 在 stage 结束处翻转每根输出线，并把它后面第一次 HMR 强制成结果 0（相当于相位修正完全一致），然后按地址记录最坏误差。结果：早期 tap 的 5 根线（40、41、50、51、57）在所有地址上误差都 ≥6.6e4×tol；其余 30 根翻转后末态都不干净（系数进入了原地算术，后面又被反算），**单比特余量为 0**。
- 后台跑了官方 verifier 全量（约 25 分钟），结果见上表。

## 4. 问题和可疑点
- 仍然没有干活的。用户 11-05 已经收尾，这个 routine 每小时还在消耗额度。
- 第一优先方向需要编译外部 C++ 库，在这个无人值守的会话里被权限挡住了；除此之外，剩下的方向都是大规模结构性重综合。

## 5. 下一步指示（按优先级，都还没做）
1. **（需要用户放行或本地执行）mockturtle MC 重综合**：`git clone --depth 1 https://github.com/lsils/mockturtle`，用 `cut_rewriting` + `future::xag_minmc_resynthesis` + `mc_cost`（cut_size 5~6）迭代，再加 `xag_constant_fanin_optimization` 和 `exact_linear_resynthesis_optimization`，输入是 `lut_extract_xag.py` 的输出。如果降到 ≤171 AND，再做 pebbling（scratch ≤39 根，测量反算只要两个输入还在就是免费的），并且把 stage 的相位当成额外输出（只有末级 AND 是免费的 CZ）。
2. **自写的局部 MC 重综合**（不依赖外部代码）：在 XAG 上枚举 ≤5 输入的割，对每个割的多输出真值表做小规模穷举（SAT 不能用的话就用 BFS 枚举 ≤3 个 AND 的 XAG），能用更少的 AND 实现就替换掉。先拿 7 个阶梯状高位输出（q40/41/43/44/57/59/60）试。
3. **跨 stage 线分配**（上次的指示 2，没做）：arith_a 峰值 61、phase_merge_repair 峰值 60，看能不能在 fine_phase_stream 期间腾出一根线，整段搬 63q 版（省 4）。先跑 `stage_match.py 25425 26758` 和 `25923 27216`。
4. **改变系数合同**：单比特没有余量，但可以考虑把系数换成别的表示（比如对 30 根进入算术的系数做 signed-digit 重编码，同时改算术），这样可能让表更"平滑"、AND 更少。工作量大，优先级最低。
5. 已关闭的方向：之前列过的全部，再加上查表单比特 don't-care 和 XAG 层面的线性冗余。

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
