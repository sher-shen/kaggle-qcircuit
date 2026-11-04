# kaggle-qcircuit 时间线

## 2026-10-29
- 立项：Kaggle Google Quantum AI 量子电路编译赛（$150k，2027-01-20 截止）；建目录 + memory，整理赛题事实（部分来自第三方 repo，待核对）
- 还没报名、没下数据；下一步见 plan.md
- 用户粘贴 Overview 页 → competition_facts.md 改为官方版：给奖牌；1,544 队；总分 = 三题改进倍数的几何平均；奖金：总榜前 6 + 11/20 里程碑 $10k + Longest Leader $10k + **单题最好各 $10k**；用户还没点 Join
- 独立 agent 审核 + 抽查：dfthcsos 不是蓝海（公开 notebook 已 ≈9.6×），抄公开 notebook 即 ≈22.37，前三 ≈26 → 结论写入 landscape_1029.md；建议降为第二优先，Smart Buildings 升为主力（待用户确认）
- 用户定：量子题为主力（求职导向，目标奖牌），Smart Buildings 为备选；写新对话提示词 docs/NEXT_PROMPT.md
- 独立 agent 审核记忆：plan.md 重写（过时方案并入"已排除"）、NEXT_PROMPT 补约束、trunk 注来源
- 第二个对话：建 .venv（py3.12，kaggle CLI + numpy/scipy）；sparse clone Qualtran/kickmix 到 ext/，编出 Python 模块 kickmix 和 CLI bin/kickmix（Apple clang 21，C++20）；比赛参考电路/验证器不在 Qualtran 里，要从 Kaggle 数据拿
- 读 arXiv:2610.23832 §III：三题 cost 官方公式写进 competition_facts.md，替换 [三方] 段；等用户放 ~/.kaggle/kaggle.json
- token 存 ~/.kaggle/access_token（用户把 KGAT_ token 原文贴在了对话里，已建议比赛中途可在 Kaggle 重新生成替换）；数据共 1.04GB，下了 <50MB 的 28MB 到 data/；没下 dqi.kmb（886MB，用 dqi_reference_circuit.py 本地生成，字节数完全一致）和 FeMoCo fcidump（128MB，dfthcsos 验证必需，待用户批）
- data/kickmix/kickmix.so 是 Linux x86 版，Mac 用自编的
- invsqrt 参考：本地验证 PASS，cost 2,076,774.23 = 官方参考值（倍数 1.000），10 核 4 分钟
- 公开最高：ahmedberatozer v12 本地 GM 22.810（20.29 / 59.27 / 9.87），拆解写进 top_public_1029.md；正在本地复跑它的 invsqrt + dqi（runs/top_v12/）
- 用户看完复现结果后觉得太难、倾向不做；fcidump 不下载；主攻方向未拍板（建议 dfthcsos 主攻 + invsqrt 副线，见 plan.md）。dqi 参考验证仍在后台（runs/chain1.sh）
- dqi 参考本地验证 PASS：cost 2.443947e13，与官方参考一致（1.000×），142 秒；invsqrt+dqi 参考都 ≈1.0，dfthcsos 因没下 fcidump 未验
- 用户问：公开 notebook 算不算不公平（答：Kaggle 常态，规则允许公开分享；后果是地板高）、为什么要化学背景（答：dfthcsos 是量子化学的 DF/THC 张量分解，化学背景是捷径不是门槛）；用户自称"看不懂这个项目"，给了小学生版解释
- 用户想找跟论文相关的：Kaggle 现无生物/蛋白类进行中比赛；方法上最近的是 Squares in Squares（硬体堆积 + MC）
- 用户想找冷门赛（类似华为 AF）：扫了 AtCoder/DrivenData/华为/ROADEF，结论合并进个人记忆 项目/简历比赛机会.md；HTTF2027（AHC074）奖金只给日本居民
- 状态：本题暂停、可能放弃，等用户决定；环境和复现都保留
- 10/29–30：3 个独立 agent 全球搜"人少+现金+住法国能领"的赛：无一全核实；能领奖的只剩蛋白设计赛（长江杯/Poreva/PDC2026）→ 个人记忆 项目/蛋白设计赛.md；本题仍暂停待定
## 2026-10-31

- 10/31：用户重新有兴趣，要求"小学生也能听懂、不要公式"地讲清项目；讲了量子计算机原理、三题、invsqrt 任务与工具箱（核实 kickmix op_type.h）；读了 busyaprime 笔记本，纠正了我 Newton 的猜测（见 invsqrt_notes_1031.md）；用户觉得多题混讲太乱，决定新对话**只聊题1**；仍未决定是否参赛
- 10/31 晚：新对话只聊题1。ch.4 是纯文字叙述无表代码；改为自编小工具把 invsqrt.kmb 转文本，数出静态门数（CCX 1154/CSWAP 194/CCZ 49/Z_POW 48 等，详见 invsqrt_notes_1031.md），看出查表形状 CX–CCX–CX + HMR/CZ 擦除；与官方 1629.6 stamps 未对账。下一步：在序列里定位 172 个 AND 的主表
- 10/31 夜：用户转去补量子基础：经典/量子比特、Shor 数论半边（N=21 例）已懂；量子傅立叶变换半边未讲，用户将开新对话继续。题1 主表定位仍未做（见 invsqrt_notes_1031.md「学习进度」）

## 2026-11-01

- 11/01：用户一对一学 Shor 量子半边，读完「学习进度」后全程只聊找周期；讲通账簿全流程（号码本/草稿/配对/读草稿留梳子/QFT 亮点/连分数/验算），详见 invsqrt_notes_1031.md「学习进度」；顺带查官方 verifier：x 寄存器 22 位、max_x=3,133,452，更正「榜首 63 qubit 是总数、22 只是输入」；解释题1 输入输出与 S=Q×C。未参赛、未提交、无下载
