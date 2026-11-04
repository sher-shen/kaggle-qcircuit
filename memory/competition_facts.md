# kaggle-qcircuit 赛题事实（10/29 用户粘贴 Overview 页核对过）

## 基本 [官方]
- 名称：Google Quantum AI - Verifiable Quantum Circuit Compilation（Featured，主办 Google Quantum AI）
- URL：https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation
- **给 Kaggle 积分和奖牌**
- 10/29 时：1,544 队 / 1,651 参赛者 / 11,458 次提交；用户 10/29 已 Join（API 能下比赛数据，已验证）
- 不需要量子物理背景；没有训练数据，靠 AI agent + 经典优化 + 验证闭环
- 官方博客：https://opensource.googleblog.com/2026/10/announcing-verifiable-quantum-circuit-compilation-competition-on-kaggle.html

## 时间（均 23:59 UTC）[官方]
- 10/22 开赛
- **11/20 中期里程碑**：当时公榜第一得奖，前提是公开 notebook
- **2027-01-04 Longest Leader 截止**：相关 notebook 和数据集须在此前公开
- 2027-01-13 报名 / 组队截止；**2027-01-20 最终提交截止**

## 奖金 $150k [官方]
- 总榜：1st $50k / 2nd $25k / 3rd $10k / 4–6th 各 $5k
- 中期里程碑 $10k（11/20 公榜第一，须公开 notebook 并保持到赛末）
- Longest Leader $10k（开赛到 1/4 期间在公榜第一停留最久的队，须公开 notebook）
- **单题奖 3 × $10k**：invsqrt / dqi / dfthcsos 各自单题最好的队各得 $10k ← 不用总榜第一，专攻一题就有机会
- 所有附加奖同样要满足授权、可复现、文档要求（见 Rules）

## 计分 [官方]
- 总分 = 三题各自相对 baseline 改进倍数的**几何平均**（某题不改也算 1× → 专攻一题也能涨总分）
- 各题 cost 里 Q = 每 shot 的 qubit 数，T = 每 shot 的 Toffoli 数（准确公式见 cost_formulas.md）
- dqi：含译码失败率的置信上界项 → 允许不完美译码，失败率进成本
- dfthcsos：Q、T 按整个 block encoding 算，不只算提交的 ANGLE 电路；任一 ANGLE 电路宽 >128 qubit 直接拒收
- 验证：fuzz 测试（输入空间小就穷举，大就按算法权重随机抽样），检查输入复原、ancilla 清零、相位正确；随机数用提交内容的加盐哈希做种子（Fiat–Shamir）→ **没有隐藏测试集，改任何东西都会重新抽样**
- 失败率 ε ⇒ 量子输出误差 ≤ 2√ε
- 提交 zip：`invsqrt.kmb|.kmx`、`dqi.kmb|.kmx`、`dfthcsos/`（`angle_k_0..n-1` 连续编号，.kmb 或 .kmx；加 `submission.npz` 含 U, W, H2_I, H1_I, Hsym_lower, tree_edges）；评分约 45 分钟
- metric：verifier 源码在比赛数据 data/verifiers/（已读，与论文一致）

## 先例
- ecdsa.fail（2026，椭圆曲线密码电路的同类可验证比赛）：100 多名参赛者，多数没有量子背景，用 AI agent 把 Toffoli 数砍了约一半；参考 arXiv:2603.28846（Babbush et al.，kickmix 的出处）

## 三个任务 [官方]
1. **invsqrt（核聚变）**：给定平方距离 x，加 ∝1/√x 的相位，相对误差 2⁻²⁴；参考电路是"初值 + Newton 迭代"，可自由换方案；218 个电子 → 每步 23,653 对
2. **dqi（组合优化）**：可逆 Reed–Solomon 校验子译码器，从 syndrome 恢复 ±1 相位符号、抵消并清空工作区；允许偶尔译码失败（arXiv:2510.10967）
3. **dfthcsos（化学，FeMoCo）**：协同优化张量分解 + Givens 旋转树 + 加载角度的 QROM；分解要保证能量精度；态制备和 Givens 门按解析公式计价

## 工具
- kickmix（Qualtran 里，C++20 + Python）：可逆经典门 + 相位门 + 测量去计算，每条 CPU 指令处理 64–512 个测试输入，单核可跑 1 亿门以上
  - 源码：https://github.com/quantumlib/Qualtran/tree/main/kickmix
- 论文：arXiv:2610.23832（官方 companion）；arXiv:2610.22367（独立工作，kickmix + AI agent）

## 三题 cost 公式
- 已拆到 cost_formulas.md

## 已知开源方案
- https://github.com/somfieao/kickmix-compiler （Claude Code + DeepSeek 写生成器 + Dream-RSI 进化搜索；约 $13–15/次尝试，一轮约 $1.5k，太贵不照抄）
