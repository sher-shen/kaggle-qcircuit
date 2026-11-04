# 三题官方 cost 公式（10/29）

## 公式与参数 [官方：arXiv:2610.23832 §III；与 data/verifiers 源码一致，参考电路本地跑出的 cost = 官方参考值]
- 各题得分 = 参考 cost / 提交 cost（越低越好），总分 = 三题几何平均；参考程序 ≈1.0
- 验证：每 shot 查 ①输入/输出寄存器比特 ②scratch 全回 |0⟩ ③相位在容差内；k 次失败/N 次 → Clopper–Pearson 上界 ε+（δ=2⁻¹²⁸，k=0 时 ε+≈88.7/N）；种子 = SHA-256(电路 .kmb 规范序列化) + 比赛私有 salt
- **invsqrt**：S = Q × C，C = Toffoli + T/4（每 shot 平均）。Clifford Z_POW 免费；T 角 1T；每个更细的 Z_POW 按 0.56·log₂(1/ϵ)+5.3 个 T 计价，ϵ = π·(min_x[tol(x)−|err(x)|])/n_rot（剩余误差余量均分给 n_rot 个旋转 → 精度留余量能省旋转钱）
  - 必须只有一个命名寄存器 "x"（22 qubit），x∈[1, 3,133,452] 全穷举 × 每 x 64 shot（2.0 亿 shot），**k=0**；相位 64-bit 定点（2⁻⁶⁴ turn），目标 ⌊2⁶⁵β/√x⌋，容差 tol(x)=2⁻²⁴β/√x turn
  - 参考：Q=260，Toffoli 7,735，1 T，37 个非 Clifford Z_POW → C=7,988，S=2.08×10⁶；最坏相对误差 2⁻²⁵·⁰⁷（初值 QROM+三次多项式 → 1 步 Newton）
- **dqi**：S = R(ε+)·Q²·T，R(ε)=ln2 / (−ln(1/2+2√ε))（p₀=1/2）；ε+≥1/16 无分。Q=全部 qubit（含 840 qubit 输入 syndrome），T=单次 Toffoli（含清理）。**1% qubit = 2% Toffoli**
  - N=102,400 shot，0 失败时 ε+≈8.7e-4 → R≈1.19（精确解码的地板）；ε+=1e-3→1.21，1e-2→1.94
  - 参数 (m,n,b,r)=(4095,70,12,2016)，GF(2¹²)，纠 ℓ=35 个符号错；错误重量按三对角矩阵主特征向量分布（E[wt]≈31.05，wt=35 占 2.8%）
  - 参考：Q=1,893，T=5,725,461（EEA 222 步 + Chien 搜索 4095 位置 × Itoh–Tsujii 求逆 351 Toffoli + 反算；63-Toffoli Karatsuba 乘法）
- **dfthcsos**（FeMoCo，N=76 轨道，η=113）：S = λ_eff × T_tot × Q_tot，λ_eff = √(E_gap(2Λ−E_gap))，E_gap = E_upper − E_SOS，**E_upper 固定 = −22140.27335 Ha**（不重算基态）
  - Λ = ‖h(1)′‖* + ¼Σ_{ρ,c}(|W(ρc)| + Σ_b|w_b(ρc)|)²（式 56）；E_SOS 见式 57；对称平移 (S,β₁) 固定为 baseline 的，提交的被忽略
  - 拒收：ε₁（一体 Frobenius）>20 mHa、ε₂（二体 Frobenius）>20 mHa、任一 Angles_k 电路 >128 qubit、Λ≤49.0、E_gap≤3.914898；不对下限做 clamp
  - T_tot = Angles_k 电路正向+反向遍历的模拟 Toffoli + Outer/Inner 态制备启发式 Toffoli（Ref.[11] 表 3）+ N−1 个 Givens 旋转启发式成本；Q_tot = 常驻 qubit（态制备寄存器 + 角度字寄存器）+ Outer/Inner/Angles 中最大临时工作区（**不封顶 128**）
  - 可优化：秩 (R,B,C)、向量 u、权重 w/W、角度精度、角度加载电路、Givens 树
- 第三方旧信息（未核实）：限 5 次/天，评分约 45 分钟；somfieao repo 只做 invsqrt，本地 3.69×、公榜 1.546

- 官方参考 cost（Kaggle metric 常数）：invsqrt 2,076,774.23 / dqi 2.4439474e13 / dfthcsos 3,355,599,588.3
