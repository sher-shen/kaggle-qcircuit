# invsqrt（题1 核聚变）学习笔记 · 10/31

## 任务本质
- 输入：**22 位**二进制 x（粒子间距平方；11/01 核实：data/verifiers/invsqrt/verify_submission_invsqrt.py 头部注释，n_p=10 每个动量分量 10 位，x=|ν−ν'|²，max_x=3(2^10−2)²=3,133,452，width=2·n_p+2=22；2^22≈419 万个号码位，实际用到 1..3,133,452 约 313 万个）；输出**不是一个数**，而是给每个 x 的"硬币"拧一个相位角，大小 ∝ 1/√x（误差上限 2⁻²⁴）；用到的草稿比特必须清回 0
- 我们交的只有一个文件 invsqrt.kmb（门清单）；没有训练数据，手里只有官方参考电路、verifier、别人公开的电路
- 打分 = 参考 cost / 我们的 cost；10/31 用户在这一题上开始想弄懂，仍**未决定**是否投入比赛

## kickmix 工具箱（源码 ext/Qualtran/kickmix/src/kickmix/circuit/op_type.h 核实）
- 开关类：X、CX、CCX（Toffoli）、SWAP、CSWAP；相位类：Z、CZ、CCZ、Z_POW（任意角旋转）；清理类：HMR（Hadamard+测量+重置）、R（置 0）；另有经典比特存取、NEG、以及大多数门的 *_IF 条件版本
- **没有加减乘除开方**，全是用上面拼出来的
- 比赛里只有 Toffoli 类（CCX/CCZ/CSWAP）和旋转（≈28.9T 每个）真正算钱，其余基本不计；物理原因：前者需要魔术态蒸馏，后者（Clifford）在纠错码上便宜

## 榜上实际做法（读 busyaprime 笔记本第 4 章，**推翻**我 10/31 早先"Newton + 小表"的猜测）
- 榜首 invsqrt 不是"先猜再修正"，而是"算盘"：让 x 经过**加法 + 查表**，把结果变相位，再 uncompute
- 成本大头是查表：主表 8 位地址 → 35 位输出，原 186 个 AND，busyaprime 搜索后压到 172（stamp 1643.6→1629.6）；窗口 S1 30→25 个 AND
- 接力史（seats=qubit 数）：官方 260 seats/7987.6 stamps → Gluzdov 84 → Phuc Thai 82 → busyaprime 78 → mrmeows 63 seats、stamps 1723.2→1643.6 → busyaprime 再改 1629.6
- 方法 = 局部重写搜索 + 穷举验证（8 位输入只有 256 种）
- **借比特**（省 seats）：anazemcev 发现归一化后 x[21] 恒为 1 且算术不读它 → 翻成 0 当干净进位线（93 qubit 版）；alexchilton 发现 scalar inverse 的 12 根输出线在某阶段恒为 0 → 其他 kernel 借用（16→7、16→4）。leoprovorov 的化学电路则选择"不借"
- 汇率参考（alexchilton，dqi 题）：多 1 个 qubit ≈ 1100 个 Toffoli，借比特要比这个汇率划算才做
- 笔记本在 ext/nb/（busyaprime / alexchilton / leoprovorov 等 8 个），busyaprime 的 ipynb 有 chapter 4

## 榜首 invsqrt.kmb 实测（10/31 晚，自编小工具把 .kmb 转成文本 kmx 后统计）
- 工具：用 ext/Qualtran/kickmix 源码里 circuit/id/util 的 .cc 编一个 20 行 main（from_kmb_file → write_kmx_to）；自带 python 模块是 py3.12 版，本机只有 3.13+，用不了；产物在会话 scratchpad，不在项目里
- 声明 22 根输入线起头（后续再分配草稿线，峰值 63 qubit），文件 45599 行。**静态门数**：CX 28717、CZ 10914、X 1513、Z 1512、**CCX 1154**、HMR 951、**CSWAP 194**、R 97、NEG 96、SWAP 64、**CCZ 49**、**Z_POW 48**、条件进出各 128
- 烧钱类静态合计 1445（CCX 80%、CSWAP 13%、CCZ 3.4%、Z_POW 3.3%）；**只是个数，不是 stamps**：官方记 1629.6 stamps/shot，两者没对上（旋转权重、条件块执行次数都没核），别把占比当成本占比
- 查表的"形状"：`CX×k  CCX  CX×k`（k 约 15–30），一个 CCX 前后各夹一排对称的 CX（拷贝/搭线再还原）；接着 `HMR + CZ` 成对出现（测量式擦除 + 修相位，擦除这步不烧 Toffoli）。这是从门序列看出的形状，**还没逐个对应到"8 位进 35 位出、172 个 AND"那张具体表**
- 旋转 Z_POW 只有 48 个，且集中在文件最末尾；说明相位是在尾部一次性打上去的，之前 41 次旋转的猜测仍不可用

## 还没做（下一步）
1. 把"8 位进、35 位出"那张表在门序列里定位出来（找连续 172 个 CCX 的那一段；busyaprime ch.4 只有文字，没有表的代码）
2. （已完成静态门数，见上；stamps 对账未做）
3. 再决定是否上手做局部重写搜索

## 已排除 / 被推翻
- "榜首 invsqrt 是小表 + Newton 修正"（10/31 我凭通用知识猜的）→ 被笔记本推翻，实际是加法 + 查表
- "41 次旋转 = 每位一次相位旋转"（未核实的猜测，不要引用）

## 学习进度
- 见 [invsqrt_learning_shor.md](invsqrt_learning_shor.md)（Shor 量子半边讲解记录、用户卡过的点、题1 输入输出与 S=Q×C）
- 注意：Shor 与题1 无直接关系；题1 下一步仍是定位 172 个 AND 的主表，未做
